import os
from pathlib import Path

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    openai_api_key: str = ""

    data_dir: str = "./data"
    upload_dir: str = "./data/uploads"

    app_host: str = "0.0.0.0"
    app_port: int = Field(
        default=8000,
        validation_alias=AliasChoices("APP_PORT", "PORT"),
    )
    app_debug: bool = False

    mcp_host: str = "0.0.0.0"
    mcp_papers_port: int = 8009
    mcp_papers_url: str = "http://127.0.0.1:8009/mcp"

    llama_cloud_api_key: str = ""
    qdrant_url: str = ""
    qdrant_api_key: str = ""
    qdrant_timeout_seconds: float = 30.0

    langsmith_api_key: str = ""
    langsmith_project: str = "papermind"
    langsmith_tracing: str = "false"

    openalex_mailto: str = "your@email.com"
    semantic_scholar_api_key: str = ""

    eval_llm_model: str = "gpt-4o-mini"
    eval_embedding_model: str = "text-embedding-3-small"
    eval_samples_path: str = "evals/eval_samples.jsonl"
    eval_collect_enabled: bool = False

    briefing_rate_limit: str = "5/hour"
    briefing_rate_limit_enabled: bool = True


settings = Settings()

if settings.langsmith_api_key:
    os.environ["LANGSMITH_API_KEY"] = settings.langsmith_api_key
    os.environ["LANGSMITH_PROJECT"] = settings.langsmith_project
    os.environ["LANGSMITH_TRACING"] = settings.langsmith_tracing


def ensure_data_dirs() -> None:
    """Create writable data directories (local dev + Docker volume)."""
    Path(settings.data_dir).mkdir(parents=True, exist_ok=True)
    Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)


ensure_data_dirs()
