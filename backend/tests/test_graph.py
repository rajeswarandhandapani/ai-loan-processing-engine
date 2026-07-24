"""Tests for the agent graph: tool-calling loop, memory, and timeout."""

import asyncio

import pytest
from langchain_core.messages import AIMessage, ToolMessage
from langchain_core.tools import tool

from app.agent.graph import build_graph, run_agent
from tests.conftest import make_fake_model, tool_call_message


@tool
def echo_tool(text: str) -> str:
    """Echo the given text back."""
    return f"echoed: {text}"


async def test_agent_calls_tool_then_answers(build_agent):
    graph = build_agent(
        messages=[
            tool_call_message("echo_tool", {"text": "hi"}),
            AIMessage(content="final answer"),
        ],
        tools=[echo_tool],
    )

    result = await graph.ainvoke(
        {"messages": [("user", "please echo hi")]},
        {"configurable": {"thread_id": "t1"}},
    )

    kinds = [type(m) for m in result["messages"]]
    assert ToolMessage in kinds
    tool_msg = next(m for m in result["messages"] if isinstance(m, ToolMessage))
    assert tool_msg.content == "echoed: hi"
    assert result["messages"][-1].content == "final answer"


async def test_run_agent_returns_last_message():
    graph = build_graph(make_fake_model([AIMessage(content="hello there")]), tools=[echo_tool])
    reply = await run_agent(graph, "hi", session_id="s1")
    assert reply == "hello there"


async def test_checkpointer_remembers_conversation():
    graph = build_graph(
        make_fake_model([AIMessage(content="one"), AIMessage(content="two")]),
        tools=[echo_tool],
    )
    await run_agent(graph, "first", session_id="same")
    await run_agent(graph, "second", session_id="same")

    state = graph.get_state({"configurable": {"thread_id": "same"}})
    # 2 user turns + 2 AI replies accumulate under the same thread_id.
    assert len(state.values["messages"]) == 4


async def test_run_agent_times_out(monkeypatch):
    graph = build_graph(make_fake_model([AIMessage(content="slow")]), tools=[echo_tool])

    async def slow_ainvoke(*args, **kwargs):
        await asyncio.sleep(0.2)

    monkeypatch.setattr(graph, "ainvoke", slow_ainvoke)
    monkeypatch.setattr("app.agent.graph.AGENT_TIMEOUT_SECONDS", 0.01)

    with pytest.raises(asyncio.TimeoutError):
        await run_agent(graph, "hi", session_id="s1")
