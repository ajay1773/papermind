import os
from typing import Literal, Optional
import httpx
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel

S2_BASE = "https://api.semanticscholar.org/graph/v1"
S2_API_KEY = os.getenv("SEMANTIC_SCHOLAR_API_KEY", "")

_FIELDS = "paperId,title,year,citationCount"


class CitationEdge(BaseModel):
    semantic_scholar_id: str
    title: str
    year: Optional[int]
    citation_count: int
    direction: Literal["cites", "cited_by"]


def _headers() -> dict:
    if S2_API_KEY:
        return {"x-api-key": S2_API_KEY}
    return {}


def _fetch_edges(paper_id: str, endpoint: str, direction: str, limit: int) -> list[CitationEdge]:
    url = f"{S2_BASE}/paper/{paper_id}/{endpoint}"
    params = {"fields": _FIELDS, "limit": limit}
    with httpx.Client(timeout=15) as client:
        resp = client.get(url, params=params, headers=_headers())
        resp.raise_for_status()
    edges = []
    for item in resp.json().get("data", []):
        nested_key = "citingPaper" if endpoint == "citations" else "citedPaper"
        p = item.get(nested_key, {})
        if not p.get("paperId"):
            continue
        edges.append(CitationEdge(
            semantic_scholar_id=p["paperId"],
            title=p.get("title") or "",
            year=p.get("year"),
            citation_count=p.get("citationCount", 0),
            direction=direction,
        ))
    return edges


def register(mcp: FastMCP) -> None:
    @mcp.tool(name="get_citation_network")
    def get_citation_network(
        semantic_scholar_id: str,
        max_per_direction: int = 10,
    ) -> list[CitationEdge]:
        """
        Return both the papers that cite this paper and the papers it cites.

        Args:
            semantic_scholar_id: Semantic Scholar paper ID of the seed paper
            max_per_direction: Number of edges to return in each direction (default 10).
        """
        limit = min(max_per_direction, 25)
        cited_by = _fetch_edges(semantic_scholar_id, "citations", "cited_by", limit)
        cites = _fetch_edges(semantic_scholar_id, "references", "cites", limit)
        return cited_by + cites
