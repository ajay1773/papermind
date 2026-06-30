from langsmith import traceable

from papermind.retrieval.classifier import classify_query
from papermind.vectorstore import query_chunks
from papermind.retrieval.generator import generate_response
from papermind.common.schemas import SourceInfo


@traceable(name="run_query")
async def run_query(user_query: str, source: str | None = None) -> dict:
    classification = classify_query(user_query)

    search_parts = [classification["rewritten_query"]] + classification["expanded_terms"]
    search_query = " ".join(search_parts)

    chunks = await query_chunks(
        query_text=search_query,
        n_results=5,
        needs_tables=classification["needs_tables"],
        source=source,
    )

    result = generate_response(
        query=user_query,
        chunks=[SourceInfo(**c) for c in chunks],
    )

    debug = {
        "query_type": classification["query_type"],
        "needs_tables": classification["needs_tables"],
        "dense_weight": classification["dense_weight"],
        "sparse_weight": classification["sparse_weight"],
        "rewritten_query": classification["rewritten_query"],
        "expanded_terms": classification["expanded_terms"],
        "search_query": search_query,
    }

    return {
        "answer": result,
        "sources": chunks,
        "debug": debug,
    }
