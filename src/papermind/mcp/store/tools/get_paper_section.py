from mcp.server.fastmcp import FastMCP
from papermind.vectorstore import get_qdrant_client, COLLECTION, ensure_collection
from qdrant_client.models import Filter, FieldCondition, MatchValue


def register(mcp: FastMCP) -> None:
    @mcp.tool(name="get_paper_section")
    async def get_paper_section(source: str, section_name: str) -> list[dict]:
        """
        Retrieve all chunks from a specific section of an indexed paper.

        Args:
            source: Filename of the paper
            section_name: Section heading to retrieve (e.g. "Abstract", "Methods", "Results")
        """
        await ensure_collection()

        results, _ = await get_qdrant_client().scroll(
            collection_name=COLLECTION,
            scroll_filter=Filter(
                must=[
                    FieldCondition(key="source", match=MatchValue(value=source)),
                    FieldCondition(key="is_chunk", match=MatchValue(value=True)),
                ]
            ),
            with_payload=True,
            with_vectors=False,
            limit=1000,
        )

        return [
            {
                "text": r.payload["text"],
                "heading": r.payload["heading"],
                "page": r.payload["page"],
                "type": r.payload["type"],
            }
            for r in results
            if r.payload and section_name.lower() in r.payload["heading"].lower()
        ]
