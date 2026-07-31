"""Factories for the external clients the app depends on.

Every Azure/LLM client is constructed here, exactly once, so the rest of the
code depends on plain objects it can be handed (and tests can fake). Nothing is
built at import time — the lifespan handler calls these during startup.

The RAG stack (embeddings + vector store) has its own package: see app/rag/.
"""

from azure.ai.textanalytics import TextAnalyticsClient
from azure.core.credentials import AzureKeyCredential
from langchain_anthropic import ChatAnthropic
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_openai import AzureChatOpenAI

from app.core.config import Settings
from app.core.logging import get_logger

logger = get_logger(__name__)


def make_chat_model(settings: Settings) -> BaseChatModel:
    """Create the chat LLM for the configured provider."""
    if settings.LLM_PROVIDER == "anthropic":
        logger.info("Using Anthropic model: %s", settings.ANTHROPIC_MODEL)
        return ChatAnthropic(
            api_key=settings.ANTHROPIC_API_KEY,
            model=settings.ANTHROPIC_MODEL,
            max_tokens=2048,
            timeout=60.0,
            max_retries=2,
        )
    logger.info("Using Azure OpenAI deployment: %s", settings.AZURE_OPENAI_DEPLOYMENT_NAME)
    return AzureChatOpenAI(
        azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
        api_key=settings.AZURE_OPENAI_API_KEY,
        azure_deployment=settings.AZURE_OPENAI_DEPLOYMENT_NAME,
        api_version=settings.AZURE_OPENAI_API_VERSION,
        max_tokens=2048,
        timeout=60.0,
        max_retries=2,
    )


def make_language_client(settings: Settings) -> TextAnalyticsClient:
    """Create the Azure AI Language client for sentiment/entity analysis."""
    if not settings.AZURE_LANGUAGE_ENDPOINT or not settings.AZURE_LANGUAGE_KEY:
        raise ValueError("Azure AI Language credentials not configured")
    return TextAnalyticsClient(
        endpoint=settings.AZURE_LANGUAGE_ENDPOINT,
        credential=AzureKeyCredential(settings.AZURE_LANGUAGE_KEY),
    )
