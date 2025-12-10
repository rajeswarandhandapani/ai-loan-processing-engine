from fastapi import APIRouter, HTTPException
from app.services.agent_service import AgentService
from app.models.chat_models import ChatRequest, ChatResponse
from app.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/chat", tags=["Chat"])
agent_service = AgentService()


@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """
    Process a chat message and return the AI agent's response.
    
    The agent can:
    - Answer questions about loan policies
    - Analyze uploaded financial documents
    - Detect user sentiment and respond empathetically
    - Extract key entities (loan amounts, business types, etc.)
    
    Args:
        request: ChatRequest containing the user message and session ID
        
    Returns:
        ChatResponse with the agent's reply and session ID
        
    Raises:
        HTTPException: If the chat processing fails
    """
    logger.info(f"Chat request received - Session: {request.session_id}")
    logger.debug(f"User message: {request.message[:100]}...")
    
    try:
        # Validate input
        if not request.message or not request.message.strip():
            raise HTTPException(
                status_code=400,
                detail="Message cannot be empty"
            )
        
        if not request.session_id or not request.session_id.strip():
            raise HTTPException(
                status_code=400,
                detail="Session ID is required"
            )
        
        # Process the message through the agent
        response = await agent_service.chat(
            message=request.message.strip(),
            session_id=request.session_id.strip()
        )
        
        logger.info(f"Chat response generated - Session: {request.session_id}")
        logger.debug(f"Agent response: {response[:100]}...")
        
        return ChatResponse(
            message=response,
            session_id=request.session_id
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"Chat processing failed - Session: {request.session_id}, Error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process chat message: {str(e)}"
        )


@router.get("/health")
async def chat_health():
    """Check if the chat service is healthy."""
    return {"status": "healthy", "service": "chat"}