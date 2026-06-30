from papermind.vectorstore.client import (
    ensure_collection,
    store_chunks,
    query_chunks,
    has_chunks_for_source,
    safe_has_chunks_for_source,
    safe_store_chunks,
    get_chunks_by_openalex_id,
    delete_paper,
    qdrant_configured,
    _get_qdrant,
    COLLECTION,
)


def get_qdrant_client():
    return _get_qdrant()


__all__ = [
    "ensure_collection",
    "store_chunks",
    "query_chunks",
    "has_chunks_for_source",
    "safe_has_chunks_for_source",
    "safe_store_chunks",
    "get_chunks_by_openalex_id",
    "delete_paper",
    "qdrant_configured",
    "get_qdrant_client",
    "COLLECTION",
]
