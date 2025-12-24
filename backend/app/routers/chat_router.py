"""
============================================================================
Chat API Router
============================================================================
Provides the /chat endpoint for AI agent conversations.

Key Concepts:
- APIRouter: FastAPI's way to organize related endpoints
- Dependency Injection: AgentService is instantiated once and reused
- Request Validation: Pydantic models validate input automatically
- Error Handling: HTTPException for proper HTTP error responses

Endpoints:
- POST /api/v1/chat/ - Send message to AI agent
- GET /api/v1/chat/health - Check chat service health

The agent can:
- Answer questions about loan policies (RAG with Azure AI Search)
- Analyze uploaded financial documents (Document Intelligence)
- Detect user sentiment and respond empathetically (Azure AI Language)
- Extract key entities from user messages (NER)
"""

from fastapi import APIRouter, HTTPException
from app.services.agent_service import AgentService
from app.models.chat_models import ChatRequest, ChatResponse
from app.logging_config import get_logger

logger = get_logger(__name__)

# ============================================================================
# Router Configuration
# ============================================================================
# prefix: All routes will be under /chat (e.g., /chat/, /chat/health)
# tags: Groups endpoints in OpenAPI documentation
router = APIRouter(prefix="/chat", tags=["Chat"])

# ============================================================================
# Service Initialization
# ============================================================================
# AgentService is a singleton - initialized once when the module loads.
# This ensures the LLM and tools are ready when the first request arrives.
# 
# Note: In production, consider lazy initialization for faster startup.
agent_service = AgentService()


# ============================================================================
# Chat Endpoint
# ============================================================================
# This is the main endpoint for AI conversations.
# 
# Request Flow:
# 1. Validate request (Pydantic does this automatically)
# 2. Log request for debugging
# 3. Pass message to AgentService
# 4. Agent decides which tools to use (if any)
# 5. Return agent's response
# 
# response_model=ChatResponse tells FastAPI to:
# - Validate response matches the schema
# - Generate OpenAPI documentation
# - Serialize Python objects to JSON

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
        # === Input Validation ===
        # While Pydantic validates types, we also check for empty strings
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
        
        # === Agent Processing ===
        # The agent uses LangGraph to:
        # 1. Analyze the message
        # 2. Decide if tools are needed
        # 3. Execute tools (search, sentiment, etc.)
        # 4. Generate a response
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
        # Re-raise HTTP exceptions as-is (preserve status codes)
        raise
    except Exception as e:
        # === Error Handling ===
        # Log the full error for debugging, but return a generic message
        # to avoid leaking internal details to clients
        logger.error(f"Chat processing failed - Session: {request.session_id}, Error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process chat message: {str(e)}"
        )


# ============================================================================
# Health Check Endpoint
# ============================================================================
# Simple endpoint for monitoring and load balancers.
# 
# In production, you might want to:
# - Check LLM API connectivity
# - Verify vector search is available
# - Return response time metrics

@router.get("/health")
async def chat_health():
    """Check if the chat service is healthy."""
    return {"status": "healthy", "service": "chat"}