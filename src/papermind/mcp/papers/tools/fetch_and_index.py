from typing import Optional
import httpx
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel


class IndexResult(BaseModel):
    success: bool
    paper_id: str
    chunks_indexed: int
    source_filename: str
    message: str


def register(mcp: FastMCP) -> None:
    @mcp.tool(name="fetch_and_index_paper")
    def fetch_and_index_paper(
        pdf_url: str,
        paper_id: str,
        title: str,
        authors: Optional[list[str]] = None,
        publication_date: Optional[str] = None,
    ) -> IndexResult:
        """
        Download a paper PDF from a URL and run it through the ingestion pipeline.

        Args:
            pdf_url: Direct URL to the open-access PDF
            paper_id: Unique identifier (OpenAlex ID or Semantic Scholar ID)
            title: Paper title
            authors: List of author names
            publication_date: ISO date string (YYYY-MM-DD)
        """
        filename = f"{paper_id.replace('/', '_')}.pdf"
        with httpx.Client(timeout=60, follow_redirects=True) as client:
            resp = client.get(pdf_url)
            resp.raise_for_status()
            pdf_bytes = resp.content

        return IndexResult(
            success=False,
            paper_id=paper_id,
            chunks_indexed=0,
            source_filename=filename,
            message="Ingestion pipeline not yet connected — wire up ingest_pdf() in this tool.",
        )
