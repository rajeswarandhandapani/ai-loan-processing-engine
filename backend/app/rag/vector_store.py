"""Vector store selection — the one place the app asks "where do the vectors live?"

Everything downstream (the ``search_lending_policy`` tool, the ingest script)
depends only on LangChain's ``VectorStore`` interface, which is why swapping
backends is a config change rather than a code change. The two methods that
matter:

* ``add_documents(docs, ids=...)`` — write chunks + their embeddings (ingestion)
* ``similarity_search(query, k=...)`` — embed the query, return the k nearest
  chunks as ``Document`` objects (retrieval)

Pick a backend with ``VECTOR_STORE_PROVIDER`` in .env: ``chroma`` (the default —
local, no setup) or ``azure`` (hosted).
"""

from langchain_core.vectorstores import VectorStore

from app.core.config import Settings
from app.rag.azure_search import make_azure_search_store
from app.rag.chroma import make_chroma_store


def make_vector_store(settings: Settings) -> VectorStore:
    """Create the lending-policy vector store for the configured provider."""
    provider = (settings.VECTOR_STORE_PROVIDER or "chroma").lower()

    if provider == "chroma":
        return make_chroma_store(settings)
    if provider == "azure":
        return make_azure_search_store(settings)

    raise ValueError(
        f"Unknown VECTOR_STORE_PROVIDER: {settings.VECTOR_STORE_PROVIDER!r}. "
        'Expected "azure" or "chroma".'
    )
