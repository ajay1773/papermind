from mcp.server.fastmcp import FastMCP
from papermind.vectorstore import query_chunks


def register(mcp: FastMCP) -> None:
    @mcp.tool(name="list_indexed_papers")
    async def list_indexed_papers() -> list[dict]:
        """
        List all papers currently indexed in the paper store.
        """
        chunks: list[dict] = await query_chunks(query_text="", n_results=1000, needs_tables=False, source=None)
        for chunk in chunks:
            chunk["source"] = chunk["source"].split("::")[0]
            chunk["chunk_id"] = chunk["source"].split("::")[1]
        return chunks
