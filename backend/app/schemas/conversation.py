from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from datetime import datetime
import uuid

from app.core.config import get_app_settings
from app.models.conversation import ConversationType

settings = get_app_settings()

class ConversationBase(BaseModel):
    title: Optional[str] = None

class ConversationCreate(ConversationBase):
    conversation_type: ConversationType = ConversationType.TEXT
    provider: Optional[str] = None  # 如果为None，将使用默认提供商
    model: Optional[str] = None  # 如果为None，将使用默认模型

class ConversationUpdate(ConversationBase):
    title: Optional[str] = None
    provider: Optional[str] = None
    model: Optional[str] = None

class ConversationInDB(ConversationBase):
    id: str
    user_id: int
    title: Optional[str] = None
    provider: str
    model: Optional[str] = None
    conversation_type: ConversationType
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class ConversationResponse(BaseModel):
    id: str
    title: Optional[str] = None
    provider: str
    model: Optional[str] = None
    conversation_type: ConversationType
    created_at: datetime

def generate_conversation_id():
    return str(uuid.uuid4()) 