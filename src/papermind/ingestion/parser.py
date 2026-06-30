import os
import tempfile

from llama_cloud import LlamaCloud

from papermind.config import settings

_client: LlamaCloud | None = None


def _get_client() -> LlamaCloud:
    global _client
    if _client is None:
        _client = LlamaCloud(api_key=settings.llama_cloud_api_key)
    return _client


def extract_with_llamaparse(contents: bytes) -> str:
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

    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)
