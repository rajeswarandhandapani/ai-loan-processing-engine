"""
============================================================================
Application Configuration Management
============================================================================
Centralized configuration using Pydantic Settings.

Key Concepts:
- Environment Variables: Configuration loaded from .env file
- Pydantic Settings: Type-safe configuration with validation
- Singleton Pattern: Single configuration instance via lru_cache

Security Best Practices:
- Never commit .env files to version control
- Use separate .env files for dev/staging/prod
- Rotate API keys regularly
- Use Azure Key Vault in production

Usage:
    from app.config import settings
    print(settings.AZURE_OPENAI_ENDPOINT)
"""

import os
from pathlib import Path
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

# ============================================================================
# Path Configuration
# ============================================================================
# Resolve the backend directory path for locating .env files
BACKEND_DIR = Path(__file__).resolve().parent.parent


# ============================================================================
# Settings Class with Pydantic
# ============================================================================
# Pydantic Settings provides:
# - Automatic type conversion (str "true" -> bool True)
# - Validation (raises error if required field missing)
# - Environment variable loading from .env files
# - Case-insensitive field matching
class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # ========================================================================
    # Azure Document Intelligence Configuration
    # ========================================================================
    # Used for: Document OCR, form extraction, table detection
    # Service: Azure AI Document Intelligence (formerly Form Recognizer)
    AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT: str | None = None
    AZURE_DOCUMENT_INTELLIGENCE_KEY: str | None = None

    # ========================================================================
    # LLM Provider Selection
    # ========================================================================
    # Supported values: "azure" (Azure OpenAI) or "anthropic" (Claude)
    LLM_PROVIDER: str | None = None

    # ========================================================================
    # Azure OpenAI Configuration
    # ========================================================================
    # Used for: Chat completions, embeddings for vector search
    # Note: Deployment names are specific to your Azure OpenAI resource
    AZURE_OPENAI_ENDPOINT: str | None = None
    AZURE_OPENAI_API_KEY: str | None = None
    AZURE_OPENAI_DEPLOYMENT_NAME: str | None = None           # e.g., "gpt-4"
    AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME: str | None = None # e.g., "text-embedding-ada-002"
    AZURE_OPENAI_API_VERSION: str = "2024-06-01"

    # ========================================================================
    # Azure AI Search Configuration
    # ========================================================================
    # Used for: Vector search over lending policy documents
    # Enables RAG (Retrieval Augmented Generation) for policy Q&A
    AZURE_SEARCH_ENDPOINT: str | None = None
    AZURE_SEARCH_KEY: str | None = None

    # ========================================================================
    # Azure AI Language Configuration
    # ========================================================================
    # Used for: Sentiment analysis, entity extraction
    # Helps agent understand user emotions and extract key information
    AZURE_LANGUAGE_ENDPOINT: str | None = None
    AZURE_LANGUAGE_KEY: str | None = None

    # ========================================================================
    # Anthropic Claude Configuration
    # ========================================================================
    # Alternative LLM provider to Azure OpenAI
    ANTHROPIC_API_KEY: str | None = None
    ANTHROPIC_MODEL: str | None = None  # e.g., "claude-3-sonnet-20240229"

    # ========================================================================
    # LangSmith Tracing Configuration
    # ========================================================================
    # Used for: Debugging, monitoring, and tracing LangChain operations
    # Helpful for understanding agent decision flow
    LANGSMITH_TRACING: bool = True
    LANGSMITH_ENDPOINT: str | None = None
    LANGSMITH_API_KEY: str | None = None
    LANGSMITH_PROJECT: str | None = None

    # ========================================================================
    # Application Settings
    # ========================================================================
    app_name: str = "AI Loan Processing Engine"
    debug: bool = False  # Enable for detailed logging and hot-reload

    # ========================================================================
    # Document Intelligence Cache
    # ========================================================================
    # Caching reduces API costs and improves response time
    # Documents are cached by content hash to avoid re-processing
    DOCUMENT_CACHE_ENABLED: bool = True
    DOCUMENT_CACHE_DIR: str = ".cache/document_intelligence"

    # ========================================================================
    # Pydantic Settings Configuration
    # ========================================================================
    # Defines how settings are loaded from environment
    model_config = SettingsConfigDict(
        env_file=os.path.join(BACKEND_DIR, ".env"),  # Load from .env file
        env_file_encoding="utf-8",
        case_sensitive=False,  # AZURE_OPENAI_KEY == azure_openai_key
        extra="ignore"         # Ignore unknown environment variables
    )


# ============================================================================
# Singleton Settings Instance
# ============================================================================
# Using lru_cache ensures only one Settings instance is created.
# 
# Benefits:
# - .env file is read only once at startup
# - All modules share the same configuration
# - Thread-safe access to settings

@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Get cached settings instance (singleton pattern)."""
    return Settings()


# Global settings instance for easy import
# Usage: from app.config import settings
settings = get_settings()
