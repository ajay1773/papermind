import os
from typing import Optional
import httpx
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel

S2_BASE = "https://api.semanticscholar.org/recommendations/v1"
S2_API_KEY = os.getenv("SEMANTIC_SCHOLAR_API_KEY", "")

_FIELDS = "paperId,title,year,abstract,citationCount,openAccessPdf"


class RelatedPaper(BaseModel):
    semantic_scholar_id: str
    title: str
    year: Optional[int]
    abstract: Optional[str]
    citation_count: int
    pdf_url: Optional[str]


def _headers() -> dict:
    if S2_API_KEY:
        return {"x-api-key": S2_API_KEY}
    return {}


def register(mcp: FastMCP) -> None:
    @mcp.tool(name="get_related_papers")
    def get_related_papers(
        semantic_scholar_id: str,
        max_results: int = 10,
    ) -> list[RelatedPaper]:
        """
        Get recommended papers related to a given paper using Semantic Scholar's
        recommendation engine.

        Args:
            semantic_scholar_id: Semantic Scholar paper ID of the seed paper
            max_results: Number of recommendations to return (max 20)
        """
        url = f"{S2_BASE}/papers/forpaper/{semantic_scholar_id}"
        params = {
            "fields": _FIELDS,
            "limit": min(max_results, 20),
        }
        with httpx.Client(timeout=15) as client:
            resp = client.get(url, params=params, headers=_headers())
            resp.raise_for_status()
        papers = resp.json().get("recommendedPapers", [])
        results = []
        for p in papers:
            oa = p.get("openAccessPdf") or {}
            results.append(RelatedPaper(
                semantic_scholar_id=p["paperId"],
                title=p.get("title") or "",
                year=p.get("year"),
                abstract=p.get("abstract"),
                citation_count=p.get("citationCount", 0),
                pdf_url=oa.get("url"),
            ))
        return results
