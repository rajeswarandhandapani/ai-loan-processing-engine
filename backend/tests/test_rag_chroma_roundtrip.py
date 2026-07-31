"""End-to-end test of the local RAG path: ingest into Chroma, then retrieve.

Uses a deterministic fake embedding rather than a real model so the test stays
fast and offline; the pipeline wiring under test is identical either way.
"""

from unittest.mock import Mock

import pytest
from langchain_core.embeddings import DeterministicFakeEmbedding

from app.agent.tools import make_tools
from app.rag.ingestion import SAMPLE_POLICY_TEXT, chunk_ids, split_policy_text
from app.services.session_store import SessionDocumentStore

pytest.importorskip("langchain_chroma")


@pytest.fixture
def policy_store(tmp_path):
    """A Chroma collection on disk, populated with the sample policy."""
    from langchain_chroma import Chroma

    store = Chroma(
        collection_name="test-lending-policies",
        embedding_function=DeterministicFakeEmbedding(size=16),
        persist_directory=str(tmp_path / "chroma"),
    )
    docs = split_policy_text(SAMPLE_POLICY_TEXT)
    store.add_documents(docs, ids=chunk_ids(docs))
    return store


def test_search_tool_retrieves_from_chroma(policy_store):
    tools = make_tools(lambda: policy_store, Mock(), SessionDocumentStore())
    search = next(t for t in tools if t.name == "search_lending_policy")

    result = search.invoke({"query": "minimum credit score"})

    assert result["total_count"] > 0
    assert result["results"][0]["title"] == "Small Business Lending Policy"
    assert result["results"][0]["content"]


def test_reingesting_updates_chunks_instead_of_duplicating(policy_store):
    docs = split_policy_text(SAMPLE_POLICY_TEXT)
    before = policy_store.get()["ids"]

    policy_store.add_documents(docs, ids=chunk_ids(docs))

    assert sorted(policy_store.get()["ids"]) == sorted(before)


def test_persisted_collection_is_readable_by_a_new_store_object(tmp_path):
    """Chroma writes to disk, so a fresh process can retrieve without re-ingesting."""
    from langchain_chroma import Chroma

    kwargs = {
        "collection_name": "persist-check",
        "embedding_function": DeterministicFakeEmbedding(size=16),
        "persist_directory": str(tmp_path / "chroma"),
    }
    docs = split_policy_text(SAMPLE_POLICY_TEXT)
    Chroma(**kwargs).add_documents(docs, ids=chunk_ids(docs))

    reopened = Chroma(**kwargs)
    assert reopened.similarity_search("collateral requirements", k=2)
