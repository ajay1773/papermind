from mcp.server.fastmcp import FastMCP
from papermind.retrieval.classifier import classify_query
from papermind.vectorstore import query_chunks
from papermind.common.schemas import SourceInfo


def register(mcp: FastMCP) -> None:
    @mcp.tool(name="search_papers")
    async def search_papers(query: str, source: str | None = None) -> list[SourceInfo]:
        """
        Search the paper store for relevant chunks using hybrid search (dense + sparse RRF).

        Args:
            query: Natural language search query
            source: Optional filename filter to restrict search to a single paper
        """
        classification = classify_query(query)
        search_parts = [classification["rewritten_query"]] + classification["expanded_terms"]
        search_query = " ".join(search_parts)
        chunks = await query_chunks(search_query, source=source)
        return [SourceInfo(**c) for c in chunks]
