"""Shared pytest fixtures and fakes.

These let the whole suite run offline: a fake chat model stands in for the LLM,
and the FastAPI app's dependencies are overridden so no Azure client is built.
"""

from collections.abc import Iterable

import pytest
from langchain_core.language_models import GenericFakeChatModel
from langchain_core.messages import AIMessage

from app.agent.graph import build_graph


class FakeToolModel(GenericFakeChatModel):
    """A scripted chat model that also accepts `.bind_tools`.

    GenericFakeChatModel returns the messages it was given, one per call, but
    its `bind_tools` raises NotImplementedError — so we override it to be a
    no-op, which is all the graph needs.
    """

    def bind_tools(self, tools, **kwargs):  # noqa: ANN001, ANN003
        return self


def make_fake_model(messages: Iterable[AIMessage]) -> FakeToolModel:
    """Build a fake model that emits the given AI messages in order."""
    return FakeToolModel(messages=iter(messages))


def tool_call_message(tool_name: str, args: dict | None = None, call_id: str = "call_1") -> AIMessage:
    """An AI message that asks to call one tool."""
    return AIMessage(
        content="",
        tool_calls=[{"name": tool_name, "args": args or {}, "id": call_id}],
    )


@pytest.fixture
def build_agent():
    """Factory: build a compiled graph from a scripted model + tools."""

    def _build(messages: Iterable[AIMessage], tools: list):
        return build_graph(make_fake_model(messages), tools)

    return _build
