"""
============================================================================
Chat API Data Models
============================================================================
Pydantic models for the chat API endpoints.

Key Concepts:
- Pydantic BaseModel: Automatic validation and serialization
- Type Hints: Define expected data types
- Field: Additional validation and default values

These models:
- Validate incoming requests automatically
- Generate OpenAPI documentation
- Provide IDE autocompletion
- Serialize responses to JSON
"""

from datetime import datetime
from pydantic import BaseModel, Field


# ============================================================================
# Chat Message Model
# ============================================================================
# Represents a single message in a conversation.
# Used internally for conversation history tracking.
class ChatMessage(BaseModel):
    """A single message in the chat conversation."""
    role: str              # 'user' or 'assistant'
    content: str           # The actual message text
    timestamp: datetime = Field(default_factory=datetime.now)  # Auto-set to now


# ============================================================================
# Chat Request Model
# ============================================================================
# Validates incoming POST /chat requests.
# Pydantic automatically returns 422 Unprocessable Entity if validation fails.
class ChatRequest(BaseModel):
    """Request body for the chat endpoint."""
    message: str      # User's message to the AI agent
    session_id: str   # Unique session identifier for conversation context


# ============================================================================
# Chat Response Model
# ============================================================================
# Defines the response structure returned by the chat endpoint.
# FastAPI uses this for response serialization and documentation.
class ChatResponse(BaseModel):
    """Response body from the chat endpoint."""
    message: str      # AI agent's response
    session_id: str   # Echo back session ID for client verification