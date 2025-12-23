"""
Application configuration management.

Loads environment variables and provides settings for Azure AI services.
"""

import os
from pathlib import Path
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Azure Document Intelligence
    AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT: str  | None = None
    AZURE_DOCUMENT_INTELLIGENCE_KEY: str | None = None

    # Azure OpenAI
    AZURE_OPENAI_ENDPOINT: str | None = None
    AZURE_OPENAI_API_KEY: str | None = None
    AZURE_OPENAI_DEPLOYMENT_NAME: str | None = None
    AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME: str | None = None
    AZURE_OPENAI_API_VERSION: str = "2024-06-01"

    # Optional: Azure AI Search
    AZURE_SEARCH_ENDPOINT: str | None = None
    AZURE_SEARCH_KEY: str | None = None

    # Optional: Azure AI Language
    AZURE_LANGUAGE_ENDPOINT: str | None = None
    AZURE_LANGUAGE_KEY: str | None = None

    # Langsmith
    LANGSMITH_TRACING: bool = True
    LANGSMITH_ENDPOINT: str | None = None
    LANGSMITH_API_KEY: str | None = None
    LANGSMITH_PROJECT: str | None = None


    # Application settings
    app_name: str = "AI Loan Processing Engine"
    debug: bool = False

    # Document Intelligence Cache
    DOCUMENT_CACHE_ENABLED: bool = True
    DOCUMENT_CACHE_DIR: str = ".cache/document_intelligence"

    model_config = SettingsConfigDict(
        env_file=os.path.join(BACKEND_DIR, ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )


# Global settings instance
@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
