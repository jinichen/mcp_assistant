from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union

class Message(BaseModel):
    role: str
    content: str
    name: Optional[str] = None
    
class ChatRequest(BaseModel):
    conversation_id: str
    messages: List[Message]
    model: Optional[str] = None
    
class ChatResponse(BaseModel):
    message: Message
    model_used: Optional[str] = None
    tokens_used: Optional[int] = None
    tool_info: Optional[Dict[str, Any]] = None 