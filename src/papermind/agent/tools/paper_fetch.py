import asyncio
import json
import logging
import random

import httpx

from papermind.mcp.client import get_mcp_tool
from papermind.ingestion.chunker import chunk_pdf
from papermind.memory import MemoryService
from papermind.vectorstore import safe_has_chunks_for_source, safe_store_chunks

logger = logging.getLogger(__name__)

_PDF_SEMAPHORE = asyncio.Semaphore(3)
_PDF_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Accept": "application/pdf,*/*",
}
_PDF_TIMEOUT = httpx.Timeout(connect=15.0, read=120.0, write=30.0, pool=5.0)
_RETRY_DELAYS = [2, 5, 10]


async def _stream_pdf(url: str) -> bytes:
    """Download a PDF with retries and exponential backoff on transient failures."""
    last_exc: Exception = RuntimeError("no attempts made")
    for attempt, delay in enumerate(_RETRY_DELAYS + [None]):
        try:
            async with httpx.AsyncClient(timeout=_PDF_TIMEOUT, headers=_PDF_HEADERS) as client:
                async with client.stream("GET", url, follow_redirects=True) as resp:
                    resp.raise_for_status()
                    return await resp.aread()
        except (httpx.RemoteProtocolError, httpx.ReadTimeout, httpx.ConnectTimeout) as e:
            last_exc = e
            if delay is None:
                break
            jitter = random.uniform(0, 2)
            logger.warning("_stream_pdf: attempt %d failed (%s), retrying in %.1fs", attempt + 1, e, delay + jitter)
            await asyncio.sleep(delay + jitter)
        except httpx.HTTPStatusError:
            raise
    raise last_exc


def _memory_hit_message(paper_id: str, reason: str = "already indexed in Qdrant") -> dict:
    return {
        "agent": "reader",
        "event": "memory_hit",
        "paper_id": paper_id,
        "reason": reason,
    }


def _record_indexed_paper(paper: dict) -> None:
    paper_id = paper.get("openalex_id") or paper.get("title", "")
    if not paper_id:
        return
    MemoryService().add_indexed_paper(
        paper_id=paper_id,
        title=paper.get("title", paper_id),
        source=paper.get("title", paper_id),
    )


async def _has_stored_chunks(paper: dict) -> bool:
    paper_openalex_id = paper.get("openalex_id", "")
    source_name = paper.get("title", "unknown.pdf")
    if paper_openalex_id:
        return await safe_has_chunks_for_source(openalex_id=paper_openalex_id)
    return await safe_has_chunks_for_source(source=source_name)


async def _mark_already_indexed(paper: dict, reason: str) -> tuple[dict, dict]:
    paper_id = paper.get("openalex_id") or paper.get("title", "")
    paper["fetch_status"] = "already_indexed"
    _record_indexed_paper(paper)
    logger.info("fetch: skipping '%s' (%s)", paper_id, reason)
    return paper, _memory_hit_message(paper_id, reason)


async def download_pdf(paper: dict) -> tuple[dict, dict | None]:
    pdf_url = paper.get("pdf_url")
    if not pdf_url:
        paper["fetch_status"] = "no_url"
        return paper, None

    if await _has_stored_chunks(paper):
        return await _mark_already_indexed(paper, "already indexed in Qdrant")

    source_name = paper.get("title", "unknown.pdf")
    paper_openalex_id = paper.get("openalex_id", "")

    async with _PDF_SEMAPHORE:
        try:
            content = await _stream_pdf(pdf_url)
            chunks = chunk_pdf(content, source_name, openalex_id=paper_openalex_id)
            stored = await safe_store_chunks(chunks)

            paper["fetch_status"] = "full_text"
            paper["chunk_count"] = len(chunks)
            if stored:
                _record_indexed_paper(paper)
            else:
                paper["_session_chunks"] = chunks
                paper["fetch_error"] = "Qdrant unavailable; using in-session PDF chunks"
                logger.warning(
                    "download_pdf: indexed in-session only for %s",
                    paper.get("openalex_id", "?"),
                )

        except httpx.HTTPError as e:
            logger.warning("download_pdf: HTTP error for %s: %s", paper.get("openalex_id", "?"), e)
            _mark_abstract_only(paper, str(e))
        except Exception as e:
            logger.exception("download_pdf: unexpected error for %s", paper.get("openalex_id", "?"))
            _mark_abstract_only(paper, str(e))

    return paper, None


def _mark_abstract_only(paper: dict, error: str) -> dict:
    """OpenAlex abstract is enough for extraction even when Semantic Scholar fails."""
    if paper.get("abstract"):
        paper["fetch_status"] = "tldr_only"
        paper["fetch_error"] = error
        return paper
    paper["fetch_status"] = "skipped"
    paper["fetch_error"] = error
    return paper


async def get_tldr(paper: dict) -> dict:
    try:
        tldr_tool = await get_mcp_tool("get_paper_tldr")
    except Exception:
        return _mark_abstract_only(paper, "get_paper_tldr tool not found")

    raw_doi = paper.get("doi")
    if not raw_doi:
        return _mark_abstract_only(paper, "No DOI available for Semantic Scholar lookup")

    doi = raw_doi.replace("https://doi.org/", "").replace("http://doi.org/", "")
    s2_id = f"DOI:{doi}" if not doi.startswith("DOI:") else doi

    try:
        result = await tldr_tool.ainvoke({"semantic_scholar_id": s2_id})
        parsed = json.loads(result) if isinstance(result, str) else result

        if isinstance(parsed, list):
            tldr_data = next((item for item in parsed if isinstance(item, dict)), {})
        elif isinstance(parsed, dict):
            tldr_data = parsed
        else:
            tldr_data = {}

        paper["tldr"] = json.loads(tldr_data.get("text", "{}"))
        if paper["tldr"]:
            paper["fetch_status"] = "tldr_only"
        else:
            _mark_abstract_only(paper, "Semantic Scholar returned empty TLDR")
    except (json.JSONDecodeError, TypeError) as e:
        logger.warning("get_tldr: bad response for %s: %s", paper.get("openalex_id", "?"), e)
        _mark_abstract_only(paper, f"Bad TLDR response: {e}")
    except Exception as e:
        error_str = str(e)
        if "404" in error_str:
            logger.info("get_tldr: paper %s not found in Semantic Scholar (404)", paper.get("openalex_id", "?"))
            error_msg = "Paper not found in Semantic Scholar"
        else:
            logger.warning("get_tldr: failed for %s: %s", paper.get("openalex_id", "?"), error_str)
            error_msg = error_str
        _mark_abstract_only(paper, error_msg)

    return paper


async def _fetch_paper(paper: dict, papers_to_skip: set[str]) -> tuple[dict, dict | None]:
    paper_id = paper.get("openalex_id", "")
    if paper_id and paper_id in papers_to_skip:
        if await _has_stored_chunks(paper):
            return await _mark_already_indexed(paper, "listed in papers_to_skip")

    if await _has_stored_chunks(paper):
        return await _mark_already_indexed(paper, "already indexed in Qdrant")

    if paper.get("is_fetchable", False):
        return await download_pdf(paper)
    return await get_tldr(paper), None


async def fetch_papers(
    papers: list[dict],
    papers_to_skip: list[str] | None = None,
) -> tuple[list[dict], list[dict]]:
    skip_set = set(papers_to_skip or [])
    results = await asyncio.gather(
        *[_fetch_paper(paper, skip_set) for paper in papers],
        return_exceptions=True,
    )

    fetched: list[dict] = []
    agent_messages: list[dict] = []
    for paper, result in zip(papers, results):
        if isinstance(result, BaseException):
            logger.warning("Failed to fetch paper %s: %s", paper.get("openalex_id", "?"), result)
            paper["fetch_status"] = "failed"
            paper["fetch_error"] = str(result)
            fetched.append(paper)
            continue

        fetched_paper, agent_message = result
        fetched.append(fetched_paper)
        if agent_message is not None:
            agent_messages.append(agent_message)
    return fetched, agent_messages
