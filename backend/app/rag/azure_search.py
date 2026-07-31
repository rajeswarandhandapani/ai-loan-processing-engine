"""Azure AI Search vector store — the hosted RAG backend.

Azure AI Search is a managed search service. The index behaves like a table whose
rows hold a text chunk plus its embedding vector; querying runs an approximate
nearest-neighbour (HNSW) search over those vectors.

Trade-off versus the local ChromaDB backend (chroma.py): nothing to run or back
up yourself and it scales past a single machine, but every query is a network
round-trip, it costs money, and you cannot use it offline.

LangChain's ``AzureSearch`` wrapper creates the index automatically on first
write if it does not exist, using its own schema: ``id``, ``content``,
``content_vector``, and a ``metadata`` field holding JSON. Retrieval parses that
JSON back into ``Document.metadata``, which is where ``title`` comes from in the
``search_lending_policy`` tool.
"""

from langchain_core.vectorstores import VectorStore

from app.core.config import Settings, is_configured
from app.core.logging import get_logger
from app.rag.embeddings import AZURE_EMBEDDING_DIMENSIONS, make_embeddings

logger = get_logger(__name__)

# The index built by scripts/index_lending_policy.py.
LENDING_POLICY_INDEX = "lending-policies"


def make_azure_search_store(settings: Settings) -> VectorStore:
    """Create the Azure AI Search vector store for lending policy chunks."""
    if not (
        is_configured(settings.AZURE_SEARCH_ENDPOINT) and is_configured(settings.AZURE_SEARCH_KEY)
    ):
        raise ValueError(
            "VECTOR_STORE_PROVIDER=azure requires AZURE_SEARCH_ENDPOINT and "
            "AZURE_SEARCH_KEY to be set to real values. "
            "Set VECTOR_STORE_PROVIDER=chroma to run locally instead."
        )

    # The index schema fixes the vector width at creation time, and this backend
    # is provisioned for ada-002's 1536 dimensions. A 384-dim local model would be
    # rejected by the service, so fail here with an actionable message instead.
    if (settings.EMBEDDING_PROVIDER or "local").lower() != "azure":
        raise ValueError(
            f"VECTOR_STORE_PROVIDER=azure only supports EMBEDDING_PROVIDER=azure "
            f"(the index is fixed at {AZURE_EMBEDDING_DIMENSIONS} dimensions), but "
            f"EMBEDDING_PROVIDER={settings.EMBEDDING_PROVIDER!r} is set. "
            "Use VECTOR_STORE_PROVIDER=chroma for local embeddings."
        )

    # Imported lazily: the local-only setup should not need langchain-community.
    from langchain_community.vectorstores.azuresearch import AzureSearch

    logger.info("Using Azure AI Search index: %s", LENDING_POLICY_INDEX)
    return AzureSearch(
        azure_search_endpoint=settings.AZURE_SEARCH_ENDPOINT,
        azure_search_key=settings.AZURE_SEARCH_KEY,
        index_name=LENDING_POLICY_INDEX,
        embedding_function=make_embeddings(settings),
        search_type="similarity",
        vector_search_dimensions=AZURE_EMBEDDING_DIMENSIONS,
    )


def delete_azure_search_index(settings: Settings) -> None:
    """Drop the index so the next write recreates it from scratch.

    Used by ``ingest_policy(reset=True)``. Missing index is not an error.
    """
    from azure.core.credentials import AzureKeyCredential
    from azure.core.exceptions import ResourceNotFoundError
    from azure.search.documents.indexes import SearchIndexClient

    client = SearchIndexClient(
        endpoint=settings.AZURE_SEARCH_ENDPOINT,
        credential=AzureKeyCredential(settings.AZURE_SEARCH_KEY),
    )
    try:
        client.delete_index(LENDING_POLICY_INDEX)
        logger.info("Deleted Azure AI Search index: %s", LENDING_POLICY_INDEX)
    except ResourceNotFoundError:
        logger.info("Index %s did not exist; nothing to delete", LENDING_POLICY_INDEX)
