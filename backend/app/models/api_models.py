from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID, uuid4

# Chat message model
class ChatMessageModel(BaseModel):
    role: str = Field(..., description="Message role: user, assistant or system")
    content: str = Field(..., description="Message content")
    timestamp: datetime = Field(default_factory=datetime.now, description="Message timestamp")

# Chat session model
class ChatSessionModel(BaseModel):
    id: UUID = Field(default_factory=uuid4, description="Session ID")
    name: str = Field(default="New Chat", description="Session name")
    messages: List[ChatMessageModel] = Field(default_factory=list, description="Session message history")
    created_at: datetime = Field(default_factory=datetime.now, description="Creation time")
    updated_at: datetime = Field(default_factory=datetime.now, description="Update time")
    
    # Model preferences
    provider: Optional[str] = Field(None, description="LLM provider")
    model: Optional[str] = Field(None, description="LLM model name")
    
    # User related (future extensible)
    user_id: Optional[str] = Field(None, description="User ID")

# API request model
class ChatRequestModel(BaseModel):
    name: Optional[str] = Field(None, description="Session name")
    provider: Optional[str] = Field(None, description="LLM provider")
    model: Optional[str] = Field(None, description="LLM model name")
    system_message: Optional[str] = Field(None, description="System prompt message")
    message: str
    
    session_id: Optional[UUID] = Field(None, description="Session ID, if empty a new session will be created")

# API response model
class SessionResponse(BaseModel):
    id: UUID = Field(..., description="Session ID")
    name: str = Field(..., description="Session name")
    created_at: datetime = Field(..., description="Creation time")
    updated_at: datetime = Field(..., description="Update time")
    message_count: int = Field(..., description="Message count")
    
class MessageResponse(BaseModel):
    session_id: UUID = Field(..., description="Session ID")
    message: ChatMessageModel = Field(..., description="Assistant reply message")
    
class SessionListResponse(BaseModel):
    sessions: List[SessionResponse] = Field(..., description="Session list")
    
class ProviderListResponse(BaseModel):
    providers: List[str] = Field(..., description="LLM provider list")

class ModelListResponse(BaseModel):
    models: Dict[str, List[str]] = Field(..., description="Model list grouped by provider")