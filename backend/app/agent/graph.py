"""The loan-officer agent as an explicit LangGraph state machine.

The graph is the classic ReAct loop, built by hand so every moving part is
visible:

    START -> agent -> (tool calls?) -> tools -> agent -> ... -> END

- `agent`   : calls the LLM (with tools bound) on the running message history.
- `tools`   : executes any tool calls the LLM requested (prebuilt ToolNode).
- routing   : `tools_condition` sends flow to `tools` when the last AI message
              contains tool calls, otherwise to END.

Conversation memory is provided by the checkpointer, keyed by `thread_id`
(which we set to the chat session_id).
"""

import asyncio
from pathlib import Path

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import BaseTool
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import START, MessagesState, StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.prebuilt import ToolNode, tools_condition

SYSTEM_PROMPT = (Path(__file__).parent / "prompts" / "loan_officer_system_prompt.md").read_text(
    encoding="utf-8"
)

# Hard ceiling on a single agent turn (tool loops included).
AGENT_TIMEOUT_SECONDS = 90.0


def build_graph(
    model: BaseChatModel,
    tools: list[BaseTool],
    checkpointer=None,
) -> CompiledStateGraph:
    """Compile the agent graph. Pass a checkpointer to persist conversations."""
    model_with_tools = model.bind_tools(tools)

    async def agent(state: MessagesState) -> dict:
        messages = [SystemMessage(SYSTEM_PROMPT), *state["messages"]]
        response = await model_with_tools.ainvoke(messages)
        return {"messages": [response]}

    builder = StateGraph(MessagesState)
    builder.add_node("agent", agent)
    builder.add_node("tools", ToolNode(tools))
    builder.add_edge(START, "agent")
    builder.add_conditional_edges("agent", tools_condition)  # -> "tools" or END
    builder.add_edge("tools", "agent")

    return builder.compile(checkpointer=checkpointer or InMemorySaver())


async def run_agent(graph: CompiledStateGraph, message: str, session_id: str) -> str:
    """Run one user turn through the graph and return the agent's reply text.

    `session_id` becomes the checkpointer `thread_id`, so each session keeps its
    own conversation history and tools can read it via ToolRuntime.
    """
    result = await asyncio.wait_for(
        graph.ainvoke(
            {"messages": [HumanMessage(message)]},
            {"configurable": {"thread_id": session_id}},
        ),
        timeout=AGENT_TIMEOUT_SECONDS,
    )
    return result["messages"][-1].content
