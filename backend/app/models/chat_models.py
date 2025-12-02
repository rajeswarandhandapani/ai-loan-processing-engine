from datetime import datetime
from pydantic import BaseModel, Field

class ChatMessage(BaseModel):
    role: str
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)
    
class ChatRequest(BaseModel):
    message: str
    session_id: str

class ChatResponse(BaseModel):
    message: str
    session_id: str