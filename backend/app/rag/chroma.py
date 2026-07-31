"""ChromaDB vector store — the local RAG backend.

Chroma is an embedded vector database: no server, no account, no network. It
keeps vectors and their text in a directory on disk (``CHROMA_PERSIST_DIR``),
much like SQLite does for relational data. Point it at a directory and it either
opens what is there or creates it.

Trade-off versus Azure AI Search (azure_search.py): free, offline, and instant to
set up, but it lives on one machine and is sized for a single process.

Vectors are grouped into *collections* (the rough equivalent of an index). A
collection's dimension is fixed by whatever was written into it first, so vectors
from two different embedding models can never share one. Rather than let that
surface as a confusing runtime error, the collection name here carries the
embedding model's name: switching ``EMBEDDING_PROVIDER`` simply targets a
different collection, which you then populate by re-running the ingest script.
"""

from pathlib import Path

from langchain_core.vectorstores import VectorStore

from app.core.config import BACKEND_DIR, Settings
from app.core.logging import get_logger
from app.rag.embeddings import embedding_model_slug, make_embeddings

logger = get_logger(__name__)

# Base name for the lending policy collection; the embedding model slug is
# appended to it (e.g. "lending-policies-all-minilm-l6-v2").
POLICY_COLLECTION_PREFIX = "lending-policies"


def policy_collection_name(settings: Settings) -> str:
    """Collection name for the active embedding model.

    Chroma requires 3-512 chars of ``[a-z0-9._-]`` starting and ending
    alphanumerically, which the slug already satisfies.
    """
    return f"{POLICY_COLLECTION_PREFIX}-{embedding_model_slug(settings)}"


def chroma_persist_path(settings: Settings) -> Path:
    """Absolute path to the Chroma data directory (relative paths resolve to backend/)."""
    configured = Path(settings.CHROMA_PERSIST_DIR)
    return configured if configured.is_absolute() else BACKEND_DIR / configured


def make_chroma_store(settings: Settings) -> VectorStore:
    """Create the local Chroma vector store for lending policy chunks."""
    try:
        from langchain_chroma import Chroma
    except ImportError as exc:
        raise RuntimeError(
            "VECTOR_STORE_PROVIDER=chroma needs langchain-chroma. Install it with:  uv sync"
        ) from exc

    persist_dir = chroma_persist_path(settings)
    collection = policy_collection_name(settings)
    logger.info("Using local Chroma collection %s at %s", collection, persist_dir)

    # Chroma creates the directory and the collection on demand, so this is safe
    # to call before anything has been ingested — searches just return nothing.
    return Chroma(
        collection_name=collection,
        embedding_function=make_embeddings(settings),
        persist_directory=str(persist_dir),
    )
