import logging
import uuid

from openai import AsyncOpenAI
from fastembed import SparseTextEmbedding
from qdrant_client import AsyncQdrantClient, models
from qdrant_client.models import (
    Distance, VectorParams,
    SparseVectorParams, Modifier,
    PointStruct, SparseVector,
    Filter, FieldCondition, MatchValue,
)

from papermind.config import settings

logger = logging.getLogger(__name__)

_qdrant: AsyncQdrantClient | None = None
_openai_client: AsyncOpenAI | None = None
_bm25_model: SparseTextEmbedding | None = None

COLLECTION = "papers"
DIMS = 1536  # text-embedding-3-small


def qdrant_configured() -> bool:
    return bool(settings.qdrant_url.strip())


def _get_qdrant() -> AsyncQdrantClient:
    global _qdrant
    if _qdrant is None:
        if not qdrant_configured():
            raise RuntimeError("QDRANT_URL is not configured")
        _qdrant = AsyncQdrantClient(
            url=settings.qdrant_url,
            api_key=settings.qdrant_api_key or None,
            timeout=settings.qdrant_timeout_seconds,
        )
    return _qdrant


def _get_openai() -> AsyncOpenAI:
    global _openai_client
    if _openai_client is None:
        _openai_client = AsyncOpenAI(api_key=settings.openai_api_key)
    return _openai_client


def _get_bm25() -> SparseTextEmbedding:
    global _bm25_model
    if _bm25_model is None:
        _bm25_model = SparseTextEmbedding(model_name="Qdrant/bm25")
    return _bm25_model


# Public accessor for MCP store tools that need direct Qdrant access
@property
def qdrant():
    return _get_qdrant()


async def ensure_collection() -> None:
    if not qdrant_configured():
        raise RuntimeError("QDRANT_URL is not configured")

    client = _get_qdrant()
    existing = [c.name for c in (await client.get_collections()).collections]
    if COLLECTION not in existing:
        await client.create_collection(
            collection_name=COLLECTION,
            vectors_config={
                "dense": VectorParams(
                    size=DIMS,
                    distance=Distance.COSINE,
                )
            },
            sparse_vectors_config={
                "sparse": SparseVectorParams(
                    modifier=Modifier.IDF,
                )
            }
        )

    await client.create_payload_index(
        collection_name=COLLECTION,
        field_name="is_chunk",
        field_schema=models.PayloadSchemaType.BOOL,
    )
    await client.create_payload_index(
        collection_name=COLLECTION,
        field_name="type",
        field_schema=models.PayloadSchemaType.KEYWORD,
    )
    await client.create_payload_index(
        collection_name=COLLECTION,
        field_name="source",
        field_schema=models.PayloadSchemaType.KEYWORD,
    )
    await client.create_payload_index(
        collection_name=COLLECTION,
        field_name="openalex_id",
        field_schema=models.PayloadSchemaType.KEYWORD,
    )


async def embed_dense(texts: list[str]) -> list[list[float]]:
    response = await _get_openai().embeddings.create(
        model="text-embedding-3-small",
        input=texts,
    )
    return [item.embedding for item in response.data]


def embed_sparse(texts: list[str]) -> list[SparseVector]:
    results = list(_get_bm25().embed(texts))
    return [
        SparseVector(
            indices=r.indices.tolist(),
            values=r.values.tolist(),
        )
        for r in results
    ]


async def store_chunks(chunks: list[dict]) -> None:
    if not chunks:
        return

    await ensure_collection()

    texts = [c["text"] for c in chunks]
    dense_vectors = await embed_dense(texts)
    sparse_vectors = embed_sparse(texts)

    points = []
    for chunk, dense_vec, sparse_vec in zip(chunks, dense_vectors, sparse_vectors):
        stable_id = str(uuid.uuid5(
            uuid.NAMESPACE_DNS,
            f"{chunk['source']}::{chunk['chunk_id']}"
        ))

        points.append(PointStruct(
            id=stable_id,
            vector={
                "dense": dense_vec,
                "sparse": sparse_vec,
            },
            payload={
                "is_chunk": True,
                "text": chunk["text"],
                "source": chunk["source"],
                "chunk_id": chunk["chunk_id"],
                "openalex_id": chunk.get("openalex_id", ""),
                "type": chunk["type"],
                "heading": chunk["heading"],
                "page": chunk["page"],
                "char_count": chunk["char_count"],
            }
        ))

    client = _get_qdrant()
    for i in range(0, len(points), 100):
        await client.upsert(
            collection_name=COLLECTION,
            points=points[i:i + 100],
        )


async def has_chunks_for_source(source: str | None = None, openalex_id: str | None = None) -> bool:
    if not qdrant_configured():
        return False

    await ensure_collection()

    if not source and not openalex_id:
        return False

    key = "openalex_id" if openalex_id else "source"
    value = openalex_id if openalex_id else source
    assert value is not None

    result = await _get_qdrant().count(
        collection_name=COLLECTION,
        count_filter=Filter(must=[
            FieldCondition(key=key, match=MatchValue(value=value)),
        ]),
        exact=False,
    )
    return result.count > 0


async def safe_has_chunks_for_source(
    source: str | None = None,
    openalex_id: str | None = None,
) -> bool:
    try:
        return await has_chunks_for_source(source=source, openalex_id=openalex_id)
    except Exception as exc:
        logger.warning("Qdrant chunk lookup failed, continuing without index: %s", exc)
        return False


async def safe_store_chunks(chunks: list[dict]) -> bool:
    try:
        await store_chunks(chunks)
        return True
    except Exception as exc:
        logger.warning("Qdrant store failed, continuing with in-session chunks: %s", exc)
        return False


async def get_chunks_by_openalex_id(openalex_id: str, limit: int = 100) -> list[dict]:
    if not qdrant_configured():
        return []

    try:
        await ensure_collection()
    except Exception as exc:
        logger.warning("Qdrant unavailable for chunk retrieval: %s", exc)
        return []

    try:
        results, _ = await _get_qdrant().scroll(
            collection_name=COLLECTION,
            scroll_filter=Filter(must=[
                FieldCondition(key="openalex_id", match=MatchValue(value=openalex_id)),
            ]),
            limit=limit,
            with_payload=True,
        )
    except Exception as exc:
        logger.warning("Qdrant scroll failed for %s: %s", openalex_id, exc)
        return []

    return [
        {
            "text": r.payload.get("text"),
            "heading": r.payload.get("heading"),
            "source": r.payload.get("source"),
            "openalex_id": r.payload.get("openalex_id"),
            "page": r.payload.get("page"),
            "type": r.payload.get("type"),
            "chunk_id": r.payload.get("chunk_id"),
            "char_count": r.payload.get("char_count"),
        }
        for r in results
        if r.payload
    ]


async def query_chunks(
    query_text: str,
    n_results: int = 5,
    needs_tables: bool = False,
    source: str | None = None,
) -> list[dict]:
    if not qdrant_configured():
        return []

    await ensure_collection()

    conditions = [
        FieldCondition(key="is_chunk", match=MatchValue(value=True))
    ]

    excluded_types = ["figure_caption"]
    if not needs_tables:
        excluded_types.append("table")

    conditions.append(
        FieldCondition(
            key="type",
            match=models.MatchExcept(**{"except": excluded_types})
        )
    )

    if source:
        conditions.append(
            FieldCondition(key="source", match=MatchValue(value=source))
        )

    where = Filter(must=conditions)  # type: ignore[arg-type]

    dense_vec = (await embed_dense([query_text]))[0]
    sparse_vec = embed_sparse([query_text])[0]

    results = await _get_qdrant().query_points(
        collection_name=COLLECTION,
        prefetch=[
            models.Prefetch(
                query=dense_vec,
                using="dense",
                limit=20,
                filter=where,
            ),
            models.Prefetch(
                query=models.SparseVector(
                    indices=sparse_vec.indices,
                    values=sparse_vec.values,
                ),
                using="sparse",
                limit=20,
                filter=where,
            ),
        ],
        query=models.FusionQuery(fusion=models.Fusion.RRF),
        limit=n_results,
        with_payload=True,
    )

    return [
        {
            "text": r.payload["text"] if r.payload else None,
            "heading": r.payload["heading"] if r.payload else None,
            "source": r.payload["source"] if r.payload else None,
            "page": r.payload["page"] if r.payload else None,
            "type": r.payload["type"] if r.payload else None,
            "score": round(r.score, 4),
        }
        for r in results.points
    ]


async def delete_paper(filename: str) -> None:
    await _get_qdrant().delete(
        collection_name=COLLECTION,
        points_selector=Filter(
            must=[FieldCondition(
                key="source", match=MatchValue(value=filename)
            )]
        ),
    )
