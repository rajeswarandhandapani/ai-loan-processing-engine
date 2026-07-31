"""Application configuration loaded from environment variables (.env).

All settings are type-checked by pydantic-settings. Access them through
`get_settings()`, which is cached so the .env file is read only once.
"""

import os
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    """Application settings. Field names match the .env keys (case-insensitive)."""

    # Azure Document Intelligence — document OCR / form + table extraction
    AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT: str | None = None
    AZURE_DOCUMENT_INTELLIGENCE_KEY: str | None = None

    # LLM provider: "azure" (Azure OpenAI) or "anthropic" (Claude)
    LLM_PROVIDER: str | None = None

    # Azure OpenAI — chat completions + embeddings for vector search
    AZURE_OPENAI_ENDPOINT: str | None = None
    AZURE_OPENAI_API_KEY: str | None = None
    AZURE_OPENAI_DEPLOYMENT_NAME: str | None = None
    AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME: str | None = None
    AZURE_OPENAI_API_VERSION: str = "2024-06-01"

    # Azure AI Search — vector search over lending policy docs (RAG)
    AZURE_SEARCH_ENDPOINT: str | None = None
    AZURE_SEARCH_KEY: str | None = None

    # RAG / vector store — see app/rag/README.md for the full provider matrix.
    # Vector store backend: "chroma" (local ChromaDB) or "azure" (Azure AI Search)
    VECTOR_STORE_PROVIDER: str = "chroma"
    # Embedding backend: "local" (ONNX, bundled with ChromaDB), "huggingface"
    # (sentence-transformers), or "azure" (Azure OpenAI)
    EMBEDDING_PROVIDER: str = "local"
    # Where ChromaDB persists its data. Relative paths resolve against backend/.
    CHROMA_PERSIST_DIR: str = ".chroma"
    # Local embedding model, used only when EMBEDDING_PROVIDER=huggingface
    HUGGINGFACE_EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    # PDF parser for policy ingestion: "auto" (Azure DI if configured, else pypdf),
    # "pypdf" (local), or "azure_di" (Azure Document Intelligence)
    POLICY_PDF_PARSER: str = "auto"

    # Azure AI Language — sentiment analysis + entity extraction
    AZURE_LANGUAGE_ENDPOINT: str | None = None
    AZURE_LANGUAGE_KEY: str | None = None

    # Anthropic Claude — alternative LLM provider
    ANTHROPIC_API_KEY: str | None = None
    ANTHROPIC_MODEL: str | None = None

    # LangSmith tracing — optional debugging/monitoring of LangChain runs
    LANGSMITH_TRACING: bool = True
    LANGSMITH_ENDPOINT: str | None = None
    LANGSMITH_API_KEY: str | None = None
    LANGSMITH_PROJECT: str | None = None

    # Application
    app_name: str = "AI Loan Processing Engine"
    debug: bool = False

    # Document Intelligence cache — avoids re-processing the same file
    DOCUMENT_CACHE_ENABLED: bool = True
    DOCUMENT_CACHE_DIR: str = ".cache/document_intelligence"

    model_config = SettingsConfigDict(
        env_file=os.path.join(BACKEND_DIR, ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the cached Settings instance (reads .env once)."""
    return Settings()


def is_configured(value: str | None) -> bool:
    """True if a setting holds a real value rather than a placeholder.

    `.env.example` ships values like `https://<your-resource>.search.windows.net`,
    and a half-filled `.env` is the normal state of this project. Treating those
    as configured produces confusing DNS errors deep inside an SDK, so anything
    still carrying the `<...>` placeholder markers counts as unset.
    """
    if not value or not value.strip():
        return False
    return "<" not in value and ">" not in value
