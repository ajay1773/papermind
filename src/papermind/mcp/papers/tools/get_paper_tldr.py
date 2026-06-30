import os
from typing import Optional
import httpx
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel

S2_BASE = "https://api.semanticscholar.org/graph/v1"
S2_API_KEY = os.getenv("SEMANTIC_SCHOLAR_API_KEY", "")

_FIELDS = "title,year,abstract,tldr,citationCount,venue,openAccessPdf,externalIds"


class PaperDetails(BaseModel):
    semantic_scholar_id: str
    title: str
    year: Optional[int]
    abstract: Optional[str]
    tldr: Optional[str]
    tldr_model: Optional[str]
    citation_count: int
    venue: Optional[str]
    pdf_url: Optional[str]
    arxiv_id: Optional[str]


def _headers() -> dict:
    if S2_API_KEY:
        return {"x-api-key": S2_API_KEY}
    return {}


def register(mcp: FastMCP) -> None:
    @mcp.tool(name="get_paper_tldr")
    def get_paper_tldr(semantic_scholar_id: str) -> PaperDetails:
        """
        Fetch AI-generated TLDR and metadata for a paper from Semantic Scholar.

        Args:
            semantic_scholar_id: Semantic Scholar paper ID or DOI prefixed with "DOI:" or arXiv ID prefixed with "ARXIV:"
        """
        url = f"{S2_BASE}/paper/{semantic_scholar_id}"
        with httpx.Client(timeout=15) as client:
            resp = client.get(url, params={"fields": _FIELDS}, headers=_headers())
            resp.raise_for_status()
        data = resp.json()
        tldr_obj = data.get("tldr") or {}
        oa = data.get("openAccessPdf") or {}
        external_ids = data.get("externalIds") or {}
        return PaperDetails(
            semantic_scholar_id=data["paperId"],
            title=data.get("title") or "",
            year=data.get("year"),
            abstract=data.get("abstract"),
            tldr=tldr_obj.get("text"),
            tldr_model=tldr_obj.get("model"),
            citation_count=data.get("citationCount", 0),
            venue=data.get("venue"),
            pdf_url=oa.get("url"),
            arxiv_id=external_ids.get("ArXiv"),
        )
