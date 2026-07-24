"""Tests for the agent tools built by make_tools()."""

from unittest.mock import Mock

from langchain_core.embeddings import DeterministicFakeEmbedding
from langchain_core.messages import AIMessage, ToolMessage
from langchain_core.vectorstores import InMemoryVectorStore

from app.agent.graph import build_graph
from app.agent.tools import make_tools
from app.services.session_store import SessionDocumentStore
from tests.conftest import make_fake_model, tool_call_message


def _get(tools, name):
    return next(t for t in tools if t.name == name)


def _policy_store() -> InMemoryVectorStore:
    return InMemoryVectorStore.from_texts(
        ["Maximum loan amount is $500,000", "Minimum credit score is 650"],
        embedding=DeterministicFakeEmbedding(size=16),
        metadatas=[{"title": "Loan Amounts"}, {"title": "Credit"}],
    )


def test_search_lending_policy_returns_titled_results():
    store = _policy_store()
    tools = make_tools(lambda: store, Mock(), SessionDocumentStore())
    result = _get(tools, "search_lending_policy").invoke({"query": "how much can I borrow"})

    assert result["total_count"] > 0
    assert "title" in result["results"][0]
    assert "content" in result["results"][0]


def test_search_lending_policy_wraps_errors():
    bad_store = Mock()
    bad_store.similarity_search.side_effect = RuntimeError("search backend down")
    tools = make_tools(lambda: bad_store, Mock(), SessionDocumentStore())

    result = _get(tools, "search_lending_policy").invoke({"query": "x"})
    assert "error" in result


def test_analyze_user_sentiment():
    sentiment = Mock(is_error=False, sentiment="positive", sentences=[])
    sentiment.confidence_scores = Mock(positive=0.9, neutral=0.05, negative=0.05)
    language_client = Mock()
    language_client.analyze_sentiment.return_value = [sentiment]

    tools = make_tools(lambda: Mock(), language_client, SessionDocumentStore())
    result = _get(tools, "analyze_user_sentiment").invoke({"text": "I love this!"})

    assert result["sentiment"] == "positive"
    assert result["confidence_scores"]["positive"] == 0.9


async def test_session_tool_reads_documents_via_runtime():
    store = SessionDocumentStore()
    store.add_document(
        session_id="sess-1",
        filename="statement.pdf",
        document_type="bank_statement",
        analysis={"fields": {"BankName": {"value": "Acme Bank"}}, "content": "…", "pages": [1]},
    )
    tools = make_tools(lambda: Mock(), Mock(), store)
    graph = build_graph(
        make_fake_model(
            [
                tool_call_message("get_analyzed_financial_documents_from_session"),
                AIMessage(content="done"),
            ]
        ),
        tools,
    )

    result = await graph.ainvoke(
        {"messages": [("user", "what did I upload?")]},
        {"configurable": {"thread_id": "sess-1"}},
    )

    tool_msg = next(m for m in result["messages"] if isinstance(m, ToolMessage))
    assert "statement.pdf" in tool_msg.content
    assert "Acme Bank" in tool_msg.content
