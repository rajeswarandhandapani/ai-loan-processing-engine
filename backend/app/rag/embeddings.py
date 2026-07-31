"""Embedding models — the first half of any RAG pipeline.

An embedding model turns text into a fixed-length vector of floats. Chunks that
mean similar things land close together in that vector space, which is what makes
"find me the policy section about credit scores" work without keyword matching.

The same model must be used for indexing and for querying. Mixing models (or even
two versions of one model) produces vectors that are not comparable, so the
vector store and the embeddings are always built together — see vector_store.py.

Three providers:

* ``local``       — the default. ``all-MiniLM-L6-v2`` (384 dimensions) running on
                    ONNX Runtime, which ships with ChromaDB. Nothing extra to
                    install and no cloud account; the ~80 MB model downloads once.
* ``huggingface`` — the same family of models through sentence-transformers,
                    which lets you swap in any model from the Hub via
                    ``HUGGINGFACE_EMBEDDING_MODEL``. Needs the optional extras
                    (``uv sync --group local-rag``) because it pulls PyTorch.
* ``azure``       — Azure OpenAI ``text-embedding-ada-002`` (1536 dimensions).
                    Highest quality, but a network call per embed and it costs
                    money.

Selected with ``EMBEDDING_PROVIDER`` in .env.
"""

from langchain_core.embeddings import Embeddings

from app.core.config import Settings, is_configured
from app.core.logging import get_logger

logger = get_logger(__name__)

# Output dimension of text-embedding-ada-002. Azure AI Search needs this up front
# to define the index schema; ChromaDB infers it from the first vector instead.
AZURE_EMBEDDING_DIMENSIONS = 1536

# The model ChromaDB bundles. Named here so the collection name can reflect it.
LOCAL_ONNX_MODEL = "all-MiniLM-L6-v2"


def make_embeddings(settings: Settings) -> Embeddings:
    """Create the embedding model for the configured provider.

    Returns the LangChain ``Embeddings`` interface, so callers only ever depend
    on ``embed_query`` / ``embed_documents`` and never on which provider is live.
    """
    provider = (settings.EMBEDDING_PROVIDER or "local").lower()

    if provider == "local":
        return _make_local_onnx_embeddings()
    if provider == "huggingface":
        return _make_huggingface_embeddings(settings)
    if provider == "azure":
        return _make_azure_embeddings(settings)

    raise ValueError(
        f"Unknown EMBEDDING_PROVIDER: {settings.EMBEDDING_PROVIDER!r}. "
        'Expected "local", "huggingface", or "azure".'
    )


class ChromaOnnxEmbeddings(Embeddings):
    """Adapts ChromaDB's bundled ONNX embedder to LangChain's ``Embeddings`` interface.

    Chroma's embedding functions take a list of strings and return a list of
    vectors; LangChain wants ``embed_documents`` / ``embed_query`` returning plain
    floats. This is the whole adapter — it exists so the rest of the RAG code can
    stay provider-agnostic.
    """

    def __init__(self) -> None:
        from chromadb.utils.embedding_functions import DefaultEmbeddingFunction

        self._embed = DefaultEmbeddingFunction()

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        # Chroma returns numpy float32 arrays; convert so callers get plain floats.
        return [[float(value) for value in vector] for vector in self._embed(texts)]

    def embed_query(self, text: str) -> list[float]:
        return self.embed_documents([text])[0]


def _make_local_onnx_embeddings() -> Embeddings:
    """Local ONNX embeddings — the zero-setup default."""
    logger.info("Using local ONNX embeddings: %s (bundled with ChromaDB)", LOCAL_ONNX_MODEL)
    return ChromaOnnxEmbeddings()


def _make_azure_embeddings(settings: Settings) -> Embeddings:
    """Azure OpenAI embeddings (hosted, 1536-dim)."""
    if not (
        is_configured(settings.AZURE_OPENAI_ENDPOINT)
        and is_configured(settings.AZURE_OPENAI_API_KEY)
    ):
        raise ValueError(
            "EMBEDDING_PROVIDER=azure requires AZURE_OPENAI_ENDPOINT and "
            "AZURE_OPENAI_API_KEY to be set to real values. "
            "Set EMBEDDING_PROVIDER=local to embed on your machine instead."
        )

    # Imported here rather than at module scope so the local-only setup never
    # pays for the Azure SDK import chain.
    from langchain_openai import AzureOpenAIEmbeddings

    logger.info(
        "Using Azure OpenAI embeddings: %s", settings.AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME
    )
    return AzureOpenAIEmbeddings(
        azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
        api_key=settings.AZURE_OPENAI_API_KEY,
        azure_deployment=settings.AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME,
        api_version=settings.AZURE_OPENAI_API_VERSION,
    )


def _make_huggingface_embeddings(settings: Settings) -> Embeddings:
    """Local sentence-transformers embeddings (offline, free, CPU)."""
    try:
        from langchain_huggingface import HuggingFaceEmbeddings
    except ImportError as exc:
        raise RuntimeError(
            "EMBEDDING_PROVIDER=huggingface needs the optional local-rag extras. "
            "Install them with:  uv sync --group local-rag"
        ) from exc

    logger.info("Using local HuggingFace embeddings: %s", settings.HUGGINGFACE_EMBEDDING_MODEL)
    # The model is downloaded to the HuggingFace cache on first use (~90 MB for
    # all-MiniLM-L6-v2), then loaded from disk on every later run.
    return HuggingFaceEmbeddings(model_name=settings.HUGGINGFACE_EMBEDDING_MODEL)


def embedding_model_slug(settings: Settings) -> str:
    """A short, filesystem/collection-safe name for the active embedding model.

    Used to keep vectors from different models in separate Chroma collections —
    see chroma.py for why mixing them is a hard error.
    """
    provider = (settings.EMBEDDING_PROVIDER or "local").lower()
    if provider == "local":
        # Distinct from the huggingface slug: same model, different runtime, so
        # keeping the vectors apart avoids any cross-runtime rounding surprises.
        raw = f"{LOCAL_ONNX_MODEL}-onnx"
    elif provider == "huggingface":
        raw = settings.HUGGINGFACE_EMBEDDING_MODEL.split("/")[-1]
    else:
        raw = settings.AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME or "azure-openai"
    return "".join(char if char.isalnum() else "-" for char in raw.lower()).strip("-")
