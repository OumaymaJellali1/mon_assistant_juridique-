from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from enum import Enum
from typing import List, Dict, Any

class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"

class ChatMessage(BaseModel):
    role: MessageRole
    content: str
    timestamp: Optional[datetime] = None

class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    user_id: Optional[str] = None

class ChatResponse(BaseModel):
    message: str
    conversation_id: str
    timestamp: datetime
    sources: List[Dict[str, Any]] = []
class HealthCheck(BaseModel):
    status: str
    timestamp: datetime
    version: str

class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
    timestamp: datetime