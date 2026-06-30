from langsmith import traceable

from papermind.common.embeddings import get_openai_client
from papermind.common.schemas import SourceInfo

SIMPLE_PROMPT = """
Answer the query based on the provided context.

Context:
{context}

Query:
{query}
"""
COT_PROMPT = """
Answer the query based on the provided context.Think step by step and provide the answer in a structured way.

Context:
{context}

Query:
{query}
"""


def build_context(chunks: list[SourceInfo]) -> str:
    context = ""
    for chunk in chunks:
        context += f"{chunk.text}\n"
    context += "\n\n---\n\n"
    return context


@traceable(name="generate_response")
def generate_response(query: str, chunks: list[SourceInfo]) -> str:
    client = get_openai_client()
    context = build_context(chunks)
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": COT_PROMPT.format(context=context, query=query)},
        ],
    )
    return response.choices[0].message.content or ""
