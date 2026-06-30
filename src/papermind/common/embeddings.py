from openai import OpenAI

from papermind.config import settings

_openai_client: OpenAI | None = None

EMBEDDING_MODEL = "text-embedding-3-small"


def get_openai_client() -> OpenAI:
    global _openai_client
    if _openai_client is None:
        _openai_client = OpenAI(api_key=settings.openai_api_key)
    return _openai_client


def generate_embeddings(texts: list[str]) -> list[list[float]]:
    client = get_openai_client()
    response = client.embeddings.create(model=EMBEDDING_MODEL, input=texts)
    return [item.embedding for item in response.data]


def generate_chat_response(query: str, context_chunks: list[str]) -> str:
    client = get_openai_client()
    context = "\n\n---\n\n".join(context_chunks)
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a helpful research assistant. Answer the user's question "
                    "based on the provided context. If the context doesn't contain "
                    "enough information, say so clearly.\n\n"
                    f"Context:\n{context}"
                ),
            },
            {"role": "user", "content": query},
        ],
    )
    return response.choices[0].message.content or ""
