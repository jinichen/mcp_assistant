from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from datetime import datetime

from app.core.config import get_app_settings

settings = get_app_settings()

class MessageBase(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str

class MessageCreate(MessageBase):
    conversation_id: str
    provider: Optional[str] = None
    user_id: Optional[int] = None

class MessageInDB(MessageBase):
    id: int
    conversation_id: str
    provider: Optional[str] = None
    user_id: Optional[int] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

class ChatRequest(BaseModel):
    conversation_id: str
    messages: List[MessageBase]
    stream: Optional[bool] = False

class ChatResponse(BaseModel):
    conversation_id: str
    message: MessageBase
    provider: str 