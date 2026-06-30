from pydantic import SecretStr
from langchain_openai import OpenAIEmbeddings
from langchain_experimental.text_splitter import SemanticChunker

from papermind.config import settings

_splitter: SemanticChunker | None = None


def _get_splitter() -> SemanticChunker:
    global _splitter
    if _splitter is None:
        embedder = OpenAIEmbeddings(
            api_key=SecretStr(settings.openai_api_key),
            model="text-embedding-3-small",
        )
        _splitter = SemanticChunker(
            embeddings=embedder,
            breakpoint_threshold_type="percentile",
            breakpoint_threshold_amount=85,
        )
    return _splitter


def semantic_split(text: str) -> list[str]:
    if len(text) < 500:
        return [text]

    docs = _get_splitter().create_documents([text])
    return [doc.page_content for doc in docs if doc.page_content.strip()]
