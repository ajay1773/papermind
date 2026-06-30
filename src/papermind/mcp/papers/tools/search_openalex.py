import logging
import re
from datetime import date, timedelta
from typing import Optional, cast

import httpx
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel

from papermind.config import settings

logger = logging.getLogger(__name__)
OPENALEX_BASE = "https://api.openalex.org"
MAILTO = settings.openalex_mailto


class PaperResult(BaseModel):
    openalex_id: str
    title: str
    publication_date: Optional[str]
    publication_year: Optional[int]
    authors: Optional[list[str]]
    concepts: Optional[list[str]]
    doi: Optional[str]
    citation_count: int
    is_open_access: bool
    oa_status: Optional[str]
    work_type: Optional[str]
    source_name: Optional[str]
    abstract: Optional[str]
    pdf_url: Optional[str]
    landing_page_url: Optional[str]
    is_fetchable: bool


def _reconstruct_abstract(inverted_index: dict | None) -> str | None:
    if not inverted_index:
        return None
    words = sorted(
        [(pos, word) for word, positions in inverted_index.items() for pos in positions]
    )
    return " ".join(word for _, word in words)


def _best_pdf_url(work: dict) -> Optional[str]:
    for source in [
        (work.get("primary_location") or {}).get("pdf_url"),
        (work.get("open_access") or {}).get("oa_url"),
        (work.get("best_oa_location") or {}).get("pdf_url"),
    ]:
        if source:
            return source
    return None


def _is_direct_pdf(url: str | None) -> bool:
    if not url:
        return False
    if url.startswith("https://doi.org/"):
        return False
    direct_hosts = [
        "arxiv.org/pdf",
        "europepmc.org",
        "openreview.net/pdf",
        "aclanthology.org",
        "link.springer.com/content/pdf",
    ]
    return any(host in url for host in direct_hosts)


def _parse_work(work: dict) -> PaperResult:
    oa = work.get("open_access") or {}
    primary = work.get("primary_location") or {}
    authorships = cast(list[dict], work.get("authorships", []))
    concepts = cast(list[dict], work.get("concepts", []))
    return PaperResult(
        openalex_id=work["id"].replace("https://openalex.org/", ""),
        title=work.get("title") or "",
        authors=[authorship.get("author", {}).get("display_name") for authorship in authorships[:7]],
        concepts=[concept.get("display_name", "") for concept in concepts],
        doi=work.get("doi"),
        publication_date=work.get("publication_date"),
        publication_year=work.get("publication_year"),
        citation_count=work.get("cited_by_count", 0),
        is_open_access=oa.get("is_oa", False),
        oa_status=oa.get("oa_status"),
        work_type=work.get("type"),
        source_name=(primary.get("source") or {}).get("display_name"),
        abstract=_reconstruct_abstract(work.get("abstract_inverted_index")),
        pdf_url=_best_pdf_url(work),
        landing_page_url=primary.get("landing_page_url"),
        is_fetchable=_is_direct_pdf(_best_pdf_url(work)),
    )


def register(mcp: FastMCP) -> None:
    @mcp.tool(name="search_papers_openalex")
    def search_papers_openalex(
        query: str,
        days_back: int = 90,
        max_results: int = 10,
        concept_ids: Optional[list[str]] = None,
    ) -> list[PaperResult]:
        """
        Search for recent academic papers using OpenAlex (primary source).
        Returns structured metadata including open-access PDF URLs where available.

        Args:
            query: Keyword search. Wrap specific technical phrases in double quotes for exact
                   phrase matching (e.g. '"large language models" evaluation benchmark').
            days_back: Only return papers published in the last N days (default 90)
            max_results: Number of papers to return (max 25 per call)
            concept_ids: Optional list of OpenAlex concept IDs to restrict domain
                         (e.g. ['C41008148', 'C11413529'] for Computer Science + NLP).
                         Dramatically reduces off-topic results for broad queries.
        """
        from_date = (date.today() - timedelta(days=days_back)).isoformat()

        quoted_phrases = re.findall(r'"([^"]+)"', query)

        # Use unquoted task/domain words as the title filter — these are the specifics
        # (e.g. "evaluation benchmarks" from '"large language models" evaluation benchmarks').
        # Using the quoted subject as the title filter instead matches every paper that
        # uses that subject, regardless of whether the paper is actually about the task.
        unquoted_words = [
            w for w in re.sub(r'"[^"]*"', "", query).split()
            if len(w) > 3
        ]
        title_filter = ""
        if unquoted_words:
            title_filter = f",title.search:{' '.join(unquoted_words[:3])}"
        elif quoted_phrases:
            title_filter = f",title.search:{quoted_phrases[0]}"

        concept_filter = ""
        if concept_ids:
            concept_filter = "," + ",".join(f"concepts.id:{cid}" for cid in concept_ids[:2])

        params = {
            "search": query,
            "filter": f"from_publication_date:{from_date},type:article{concept_filter}{title_filter}",
            "sort": "relevance_score:desc",
            "per_page": min(max_results, 25),
            "select": "id,title,publication_year,cited_by_count,open_access,primary_location,abstract_inverted_index,open_access,best_oa_location,authorships,concepts,publication_date,doi",
            "mailto": MAILTO,
        }
        logger.info("search_papers_openalex called | query=%r days_back=%d max_results=%d", query, days_back, max_results)
        logger.info("OpenAlex request | url=%s/works params=%s", OPENALEX_BASE, params)
        try:
            with httpx.Client(timeout=15) as client:
                resp = client.get(f"{OPENALEX_BASE}/works", params=params)
                resp.raise_for_status()
            results = resp.json().get("results", [])
            logger.info("OpenAlex response | %d results returned", len(results))
            return [_parse_work(w) for w in results]
        except Exception as e:
            logger.error("OpenAlex request failed | %s", e)
            raise RuntimeError(f"OpenAlex search failed: {e}") from e
