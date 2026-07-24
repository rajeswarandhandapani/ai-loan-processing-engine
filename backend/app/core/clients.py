"""Factories for the external clients the app depends on.

Every Azure/LLM client is constructed here, exactly once, so the rest of the
code depends on plain objects it can be handed (and tests can fake). Nothing is
built at import time — the lifespan handler calls these during startup.
"""

from azure.ai.textanalytics import TextAnalyticsClient
from azure.core.credentials import AzureKeyCredential
from langchain_anthropic import ChatAnthropic
from langchain_community.vectorstores.azuresearch import AzureSearch
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_openai import AzureChatOpenAI, AzureOpenAIEmbeddings

from app.core.config import Settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# The Azure AI Search index built by scripts/index_lending_policy.py.
LENDING_POLICY_INDEX = "lending-policies"
# text-embedding-ada-002 output dimension; passed so the vector store does not
# need an embedding round-trip just to discover it at startup.
EMBEDDING_DIMENSIONS = 1536


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


def make_embeddings(settings: Settings) -> AzureOpenAIEmbeddings:
    """Create the Azure OpenAI embeddings client (used for RAG + indexing)."""
    return AzureOpenAIEmbeddings(
        azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
        api_key=settings.AZURE_OPENAI_API_KEY,
        azure_deployment=settings.AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME,
        api_version=settings.AZURE_OPENAI_API_VERSION,
    )


def make_vector_store(settings: Settings) -> AzureSearch:
    """Create the lending-policy vector store (pure vector similarity search)."""
    return AzureSearch(
        azure_search_endpoint=settings.AZURE_SEARCH_ENDPOINT,
        azure_search_key=settings.AZURE_SEARCH_KEY,
        index_name=LENDING_POLICY_INDEX,
        embedding_function=make_embeddings(settings),
        search_type="similarity",
        vector_search_dimensions=EMBEDDING_DIMENSIONS,
    )


def make_language_client(settings: Settings) -> TextAnalyticsClient:
    """Create the Azure AI Language client for sentiment/entity analysis."""
    if not settings.AZURE_LANGUAGE_ENDPOINT or not settings.AZURE_LANGUAGE_KEY:
        raise ValueError("Azure AI Language credentials not configured")
    return TextAnalyticsClient(
        endpoint=settings.AZURE_LANGUAGE_ENDPOINT,
        credential=AzureKeyCredential(settings.AZURE_LANGUAGE_KEY),
    )
