"""Chat endpoints — talk to the loan-officer agent."""

from fastapi import APIRouter, Depends, HTTPException
from langgraph.graph.state import CompiledStateGraph

from app.agent.graph import run_agent
from app.api.deps import get_graph
from app.core.errors import friendly_error
from app.core.logging import get_logger
from app.models import ChatRequest, ChatResponse

logger = get_logger(__name__)
router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("/", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    graph: CompiledStateGraph = Depends(get_graph),
) -> ChatResponse:
    """Send a message to the agent and return its reply."""
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    if not request.session_id.strip():
        raise HTTPException(status_code=400, detail="Session ID is required")

    logger.info("Chat request - session: %s", request.session_id)
    try:
        reply = await run_agent(graph, request.message.strip(), request.session_id.strip())
    except Exception as exc:  # noqa: BLE001 — surface a friendly message, log the detail
        logger.exception("Chat failed for session %s", request.session_id)
        raise HTTPException(status_code=500, detail=friendly_error(exc)) from exc

    return ChatResponse(message=reply, session_id=request.session_id)


@router.get("/health")
async def chat_health() -> dict:
    """Liveness check for the chat service."""
    return {"status": "healthy", "service": "chat"}
