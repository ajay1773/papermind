import logging
import asyncio
from typing import Literal, cast

from pydantic import BaseModel

from papermind.agent.prompts import EXTRACT_FINDINGS_PROMPT_FULLTEXT, EXTRACT_FINDINGS_PROMPT_TLDR
from papermind.common.llm import get_llm
from papermind.agent.state import PaperMindState
from papermind.memory import MemoryService
from papermind.vectorstore import get_chunks_by_openalex_id

logger = logging.getLogger(__name__)

# Keep extraction focused: first N chunks (abstract/intro) + last N chunks (conclusion/results)
_EXTRACTION_HEAD_CHUNKS = 6
_EXTRACTION_TAIL_CHUNKS = 4
_EXTRACTION_MAX_CHARS = 8_000
_TLDR_MIN_CHARS = 80


class PaperExtraction(BaseModel):
    openalex_id: str
    title: str
    main_claim: str
    methodology: str
    key_results: str
    novelty: str
    limitations: str
    relevant_to: str
    confidence: Literal["high", "low"]
    source_type: Literal["full_text", "tldr_only"]


def _extraction_cache_hit_message(paper_id: str) -> dict:
    return {
        "agent": "reader",
        "event": "extraction_cache_hit",
        "paper_id": paper_id,
        "reason": "reusing cached extraction",
    }


def _has_extractable_text(paper: dict) -> bool:
    tldr = paper.get("tldr") or {}
    tldr_text = tldr.get("tldr") if isinstance(tldr, dict) else ""
    return bool((tldr_text or "").strip() or (paper.get("abstract") or "").strip())


def _select_chunks(chunks: list) -> list:
    """Keep head + tail chunks to cover abstract/intro and conclusions without passing the full paper."""
    total = _EXTRACTION_HEAD_CHUNKS + _EXTRACTION_TAIL_CHUNKS
    if len(chunks) <= total:
        return chunks
    return chunks[:_EXTRACTION_HEAD_CHUNKS] + chunks[-_EXTRACTION_TAIL_CHUNKS:]


def _build_extraction_content(chunks: list) -> str:
    selected = _select_chunks(chunks)
    content = "\n\n".join(chunk["text"] for chunk in selected)
    if len(content) > _EXTRACTION_MAX_CHARS:
        content = content[:_EXTRACTION_MAX_CHARS] + "\n\n[content truncated]"
    return content


async def extract_from_full_text(paper: dict) -> PaperExtraction:
    session_chunks = paper.get("_session_chunks") or []
    if session_chunks:
        content = _build_extraction_content(session_chunks)
    else:
        chunks = await get_chunks_by_openalex_id(paper["openalex_id"])
        content = _build_extraction_content(chunks)
    if not content.strip() and _has_extractable_text(paper):
        logger.info(
            "extract: no chunks for %s, falling back to abstract/tldr",
            paper.get("openalex_id", "?"),
        )
        return await extract_from_tldr(paper)
    structured_llm = get_llm().with_structured_output(PaperExtraction)
    return cast(PaperExtraction, await structured_llm.ainvoke([
        {"role": "system", "content": EXTRACT_FINDINGS_PROMPT_FULLTEXT},
        {"role": "user", "content": f"OpenAlex ID: {paper['openalex_id']}\nPaper: {paper['title']}\n\nContent:\n{content}"}
    ]))


async def extract_from_tldr(paper: dict) -> PaperExtraction:
    tldr = paper.get("tldr", {}).get("tldr") or paper.get("abstract") or ""
    structured_llm = get_llm().with_structured_output(PaperExtraction)
    return cast(PaperExtraction, await structured_llm.ainvoke([
        {"role": "system", "content": EXTRACT_FINDINGS_PROMPT_TLDR},
        {"role": "user", "content": f"OpenAlex ID: {paper['openalex_id']}\nPaper: {paper['title']}\n\nTLDR:\n{tldr}"}
    ]))


async def extract_for_paper(
    paper: dict,
    memory: MemoryService,
) -> tuple[PaperExtraction | None, dict | None]:
    paper_id = paper.get("openalex_id", "")
    if paper_id:
        cached = memory.get_paper_extraction(paper_id)
        if cached:
            return PaperExtraction.model_validate(cached), _extraction_cache_hit_message(paper_id)

    fetch_status = paper.get("fetch_status")
    if fetch_status in ("full_text", "already_indexed"):
        result = await extract_from_full_text(paper)
    elif fetch_status == "tldr_only" or _has_extractable_text(paper):
        tldr_text = (paper.get("tldr") or {}).get("tldr") or paper.get("abstract") or ""
        if len(tldr_text.strip()) < _TLDR_MIN_CHARS:
            logger.info(
                "extract: skipping %s — extractable text too short (%d chars)",
                paper_id or paper.get("title", "?"),
                len(tldr_text.strip()),
            )
            return None, None
        result = await extract_from_tldr(paper)
    else:
        logger.info(
            "extract: skipping %s — fetch_status=%s and no abstract/tldr",
            paper_id or paper.get("title", "?"),
            fetch_status,
        )
        return None, None

    if paper_id:
        memory.save_paper_extraction(paper_id, result.model_dump())
    return result, None


async def extract_findings(state: PaperMindState) -> dict:
    errors = state.get("errors", [])
    fetched_papers = state.get("fetched_papers", [])

    if not fetched_papers:
        errors.append({"node": "extract_findings", "error": "No fetched papers to extract from", "recoverable": True})
        return {"extracted_findings": [], "errors": errors, "status": "drafting"}

    memory = MemoryService()
    agent_messages = list(state.get("agent_messages", []))

    try:
        tasks = [
            extract_for_paper(paper, memory)
            for paper in fetched_papers
            if isinstance(paper, dict)
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        findings = []
        for result in results:
            if isinstance(result, BaseException):
                logger.warning("extract_findings: one extraction failed: %s", result)
                errors.append({"node": "extract_findings", "error": str(result), "recoverable": True})
                continue

            extraction, cache_message = result
            if cache_message is not None:
                agent_messages.append(cache_message)
            if extraction is not None:
                findings.append(extraction.model_dump())

        return {
            "extracted_findings": findings,
            "agent_messages": agent_messages,
            "errors": errors,
            "status": "drafting",
        }

    except Exception as e:
        logger.exception("extract_findings: unexpected error")
        errors.append({"node": "extract_findings", "error": str(e), "recoverable": False})
        return {"extracted_findings": [], "errors": errors, "status": "drafting"}
