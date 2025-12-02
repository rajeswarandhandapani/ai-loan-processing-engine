from fastapi import APIRouter
from app.services.agent_service import AgentService
from app.models.chat_models import ChatRequest, ChatResponse



router = APIRouter(prefix="/chat", tags=["Chat"])
agent_service = AgentService()

@router.post("/")
async def chat(request: ChatRequest):
    response = await agent_service.chat(request.message, request.session_id)
    return ChatResponse(
        message=response,
        session_id=request.session_id
    )