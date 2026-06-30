import io
import logging
import os
import tempfile

from llama_cloud import LlamaCloud

from papermind.config import settings

logger = logging.getLogger(__name__)

_client: LlamaCloud | None = None


def _get_client() -> LlamaCloud:
    global _client
    if _client is None:
        _client = LlamaCloud(api_key=settings.llama_cloud_api_key)
    return _client


def _is_credits_exhausted(exc: Exception) -> bool:
    msg = str(exc).lower()
    return "402" in msg or "credits" in msg or "exceeded" in msg


def extract_with_pypdf(contents: bytes) -> str:
    """Plain-text fallback using pypdf — no API required."""
    from pypdf import PdfReader
    reader = PdfReader(io.BytesIO(contents))
    parts = []
    for i, page in enumerate(reader.pages, 1):
        text = page.extract_text() or ""
        if text.strip():
            parts.append(f"<!-- Page {i} -->")
            parts.append(text.strip())
    return "\n\n".join(parts)


def extract_with_llamaparse(contents: bytes) -> str:
    """Parse PDF via LlamaParse. Falls back to pypdf on credit exhaustion or missing key."""
    if not settings.llama_cloud_api_key:
        logger.info("LLAMA_CLOUD_API_KEY not set — using pypdf fallback")
        return extract_with_pypdf(contents)

    client = _get_client()
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            f.write(contents)
            tmp_path = f.name

        file = client.files.create(
            file=tmp_path,
            purpose="parse"
        )

        result = client.parsing.parse(
            file_id=file.id,
            tier="agentic",
            version="latest",
            expand=["markdown"],
            output_options={
                "markdown": {
                    "tables": {"output_tables_as_markdown": True}
                }
            },
            processing_options={
                "ocr_parameters": {"languages": ["en"]}
            }
        )

        parts = []
        for i, page in enumerate(result.markdown.pages if result.markdown else [], 1):
            parts.append(f"<!-- Page {i} -->")
            parts.append(page.markdown)
        return "\n\n".join(parts)

    except Exception as e:
        if _is_credits_exhausted(e):
            logger.warning("LlamaParse credits exhausted — falling back to pypdf: %s", e)
            return extract_with_pypdf(contents)
        raise

    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)
