"""Tests for provider selection in app/rag/ — the config-driven backend switch."""

import sys

import pytest

from app.core.config import Settings, is_configured
from app.rag.chroma import chroma_persist_path, policy_collection_name
from app.rag.embeddings import ChromaOnnxEmbeddings, embedding_model_slug, make_embeddings
from app.rag.vector_store import make_vector_store

AZURE_OPENAI = {
    "AZURE_OPENAI_ENDPOINT": "https://example.openai.azure.com/",
    "AZURE_OPENAI_API_KEY": "key",
    "AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME": "text-embedding-ada-002",
}
AZURE_SEARCH = {
    "AZURE_SEARCH_ENDPOINT": "https://example.search.windows.net",
    "AZURE_SEARCH_KEY": "key",
}


def make_settings(**overrides) -> Settings:
    """Settings built from explicit values only, ignoring the developer's .env."""
    return Settings(_env_file=None, **overrides)


# --- defaults ---------------------------------------------------------------


def test_defaults_are_fully_local():
    """A fresh checkout with no .env must run RAG without any cloud account."""
    settings = make_settings()
    assert settings.VECTOR_STORE_PROVIDER == "chroma"
    assert settings.EMBEDDING_PROVIDER == "local"


def test_default_embeddings_need_no_credentials():
    embeddings = make_embeddings(make_settings())
    assert isinstance(embeddings, ChromaOnnxEmbeddings)


# --- vector store selection -------------------------------------------------


def test_unknown_vector_store_provider_is_rejected():
    with pytest.raises(ValueError, match="Unknown VECTOR_STORE_PROVIDER"):
        make_vector_store(make_settings(VECTOR_STORE_PROVIDER="pinecone"))


def test_reset_rejects_unknown_provider_before_touching_a_backend():
    from app.rag.ingestion import reset_store

    with pytest.raises(ValueError, match="Unknown VECTOR_STORE_PROVIDER"):
        reset_store(make_settings(VECTOR_STORE_PROVIDER="pinecone"))


def test_azure_store_requires_search_credentials():
    settings = make_settings(VECTOR_STORE_PROVIDER="azure", **AZURE_OPENAI)
    with pytest.raises(ValueError, match="AZURE_SEARCH_ENDPOINT"):
        make_vector_store(settings)


def test_azure_store_rejects_local_embeddings():
    """The Azure index is fixed at 1536 dims, so a 384-dim local model cannot be used."""
    settings = make_settings(
        VECTOR_STORE_PROVIDER="azure", EMBEDDING_PROVIDER="huggingface", **AZURE_SEARCH
    )
    with pytest.raises(ValueError, match="VECTOR_STORE_PROVIDER=chroma"):
        make_vector_store(settings)


def test_chroma_store_is_created_without_any_azure_credentials(tmp_path):
    pytest.importorskip("langchain_chroma")
    settings = make_settings(
        VECTOR_STORE_PROVIDER="chroma",
        EMBEDDING_PROVIDER="azure",
        CHROMA_PERSIST_DIR=str(tmp_path),
        **AZURE_OPENAI,
    )
    store = make_vector_store(settings)
    assert store is not None


# --- embedding selection ----------------------------------------------------


def test_unknown_embedding_provider_is_rejected():
    with pytest.raises(ValueError, match="Unknown EMBEDDING_PROVIDER"):
        make_embeddings(make_settings(EMBEDDING_PROVIDER="cohere"))


def test_azure_embeddings_require_credentials():
    with pytest.raises(ValueError, match="AZURE_OPENAI_ENDPOINT"):
        make_embeddings(make_settings(EMBEDDING_PROVIDER="azure"))


def test_huggingface_embeddings_explain_the_missing_extra(monkeypatch):
    """Without the local-rag group installed, the error must say how to fix it."""
    monkeypatch.setitem(sys.modules, "langchain_huggingface", None)
    with pytest.raises(RuntimeError, match="uv sync --group local-rag"):
        make_embeddings(make_settings(EMBEDDING_PROVIDER="huggingface"))


# --- collection naming ------------------------------------------------------


def test_collection_name_differs_per_embedding_model():
    """Vectors from different models must never share a collection."""
    azure = make_settings(EMBEDDING_PROVIDER="azure", **AZURE_OPENAI)
    hugging_face = make_settings(
        EMBEDDING_PROVIDER="huggingface",
        HUGGINGFACE_EMBEDDING_MODEL="sentence-transformers/all-MiniLM-L6-v2",
    )
    onnx = make_settings(EMBEDDING_PROVIDER="local")

    names = {
        policy_collection_name(azure),
        policy_collection_name(hugging_face),
        policy_collection_name(onnx),
    }
    assert names == {
        "lending-policies-text-embedding-ada-002",
        "lending-policies-all-minilm-l6-v2",
        "lending-policies-all-minilm-l6-v2-onnx",
    }


def test_embedding_slug_is_collection_safe():
    settings = make_settings(
        EMBEDDING_PROVIDER="huggingface",
        HUGGINGFACE_EMBEDDING_MODEL="BAAI/bge-small-en-v1.5",
    )
    slug = embedding_model_slug(settings)
    assert slug == "bge-small-en-v1-5"
    assert all(char.isalnum() or char in "-_." for char in slug)


def test_relative_persist_dir_resolves_under_backend():
    path = chroma_persist_path(make_settings(CHROMA_PERSIST_DIR=".chroma"))
    assert path.is_absolute()
    assert path.name == ".chroma"


def test_absolute_persist_dir_is_used_as_is(tmp_path):
    assert chroma_persist_path(make_settings(CHROMA_PERSIST_DIR=str(tmp_path))) == tmp_path


# --- placeholder credentials ------------------------------------------------


def test_env_example_placeholders_do_not_count_as_configured():
    """A half-filled .env is normal; placeholders must not look like real values."""
    assert not is_configured("https://<your-resource>.search.windows.net")
    assert not is_configured("<your-search-admin-key>")
    assert not is_configured("")
    assert not is_configured(None)
    assert is_configured("https://real-resource.search.windows.net")


def test_azure_store_rejects_placeholder_credentials():
    """Otherwise this surfaces as a confusing DNS error deep inside the SDK."""
    settings = make_settings(
        VECTOR_STORE_PROVIDER="azure",
        EMBEDDING_PROVIDER="azure",
        AZURE_SEARCH_ENDPOINT="https://<your-resource>.search.windows.net",
        AZURE_SEARCH_KEY="<your-search-admin-key>",
    )
    with pytest.raises(ValueError, match="real values"):
        make_vector_store(settings)


def test_auto_parser_ignores_placeholder_document_intelligence_credentials():
    from app.rag.ingestion import resolve_pdf_parser

    settings = make_settings(
        POLICY_PDF_PARSER="auto",
        AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT="https://<your-resource>.cognitiveservices.azure.com/",
        AZURE_DOCUMENT_INTELLIGENCE_KEY="<your-document-intelligence-key>",
    )
    assert resolve_pdf_parser(settings) == "pypdf"
