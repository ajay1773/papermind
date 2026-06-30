import json
from langsmith import traceable

from papermind.common.embeddings import get_openai_client


@traceable(name="classify_query")
def classify_query(query: str) -> dict:
    client = get_openai_client()

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0,
        messages=[
            {
                "role": "system",
                "content": """You are a search query optimizer for a research paper RAG system.

Analyze the user's question and return a JSON object. Return JSON only — no
preamble, no explanation, no markdown code fences.

{
  "query_type": "conceptual" | "factual" | "numerical",
  "needs_tables": true | false,
  "dense_weight": <float between 0.0 and 1.0>,
  "sparse_weight": <float between 0.0 and 1.0>,
  "rewritten_query": "<improved query for search>",
  "expanded_terms": ["<term 1>", "<term 2>", "<term 3>"]
}

Classification rules:

query_type:
  conceptual → how/why questions, concept explanations, methodology,
               differences between ideas, architecture descriptions
  factual    → specific named things, definitions, what-is questions,
               named systems, authors, sections
  numerical  → scores, metrics, percentages, benchmarks, results,
               accuracy values, tables of data

needs_tables:
  true  → answer likely lives in a data table
          (scores, metrics, comparisons, results, rankings, numbers)
  false → answer is in prose
          (explanations, methodology, concepts, differences)

dense_weight + sparse_weight must sum to 1.0:
  conceptual → dense_weight=0.7, sparse_weight=0.3
               (semantic understanding matters more than keywords)
  factual    → dense_weight=0.5, sparse_weight=0.5
               (both matter equally)
  numerical  → dense_weight=0.3, sparse_weight=0.7
               (exact term matching matters more for specific values)

rewritten_query rules:
  - Remove filler: "can you explain", "tell me about", "I want to know"
  - Replace vague pronouns with what they refer to (if obvious)
  - Make it specific and self-contained
  - Keep it short — 5-15 words is ideal for search
  - Examples:
    "Tell me how collaborative RAG works" → "collaborative RAG architecture mechanism"
    "What does table 2 show?" → "page level benchmark results table metrics"
    "Explain the thing from section 3" → "methodology Visual-RAG pipeline"

expanded_terms rules:
  - 2-3 terms the answer might use in academic papers
  - Synonyms, related concepts, alternative phrasings
  - Do NOT change the meaning of the query
  - Examples:
    "Collaborative RAG" → ["cross-institutional retrieval", "federated RAG",
                           "privacy-preserving retrieval"]
    "hallucination rate" → ["unsupported claims", "factual errors",
                            "fabricated content"]
    "CoP score" → ["context precision", "answer correctness metric"]
"""
            },
            {
                "role": "user",
                "content": query
            }
        ],
        response_format={"type": "json_object"},
    )

    try:
        result = json.loads(response.choices[0].message.content or "{}")

        return {
            "query_type": result.get("query_type", "conceptual") if result else "conceptual",
            "needs_tables": result.get("needs_tables", False),
            "dense_weight": float(result.get("dense_weight", 0.6)),
            "sparse_weight": float(result.get("sparse_weight", 0.4)) if result else 0.4,
            "rewritten_query": result.get("rewritten_query", query) if result else query,
            "expanded_terms": result.get("expanded_terms", []) if result else [],
        }

    except (json.JSONDecodeError, KeyError, ValueError):
        return {
            "query_type": "conceptual",
            "needs_tables": False,
            "dense_weight": 0.6,
            "sparse_weight": 0.4,
            "rewritten_query": query,
            "expanded_terms": [],
        }
