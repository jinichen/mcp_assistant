from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field

class Function(BaseModel):
    """Function definition in tool calls"""
    name: str
    arguments: str

class ToolCall(BaseModel):
    """Tool call definition"""
    id: str
    type: str = "function"
    function: Function

class Delta(BaseModel):
    """Incremental message content"""
    content: Optional[str] = None
    role: Optional[str] = None
    tool_calls: Optional[List[ToolCall]] = None

class Message(BaseModel):
    """Chat message model"""
    role: str
    content: Optional[str] = None
    name: Optional[str] = None
    tool_calls: Optional[List[ToolCall]] = None

class Choice(BaseModel):
    """Choice in chat completion response"""
    index: int
    message: Message
    finish_reason: Optional[str] = None

class StreamingChoice(BaseModel):
    """Choice in streaming chat completion response"""
    index: int
    delta: Delta
    finish_reason: Optional[str] = None

class LegacyStreamingChoice(BaseModel):
    """Choice in streaming chat completion response (compatible with older versions)"""
    index: int
    message: Optional[Message] = None
    delta: Optional[Delta] = None
    finish_reason: Optional[str] = None

class Usage(BaseModel):
    """Usage information"""
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int

class ChatCompletionResponse(BaseModel):
    """Chat completion response"""
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[Choice]
    usage: Optional[Usage] = None

class ChatCompletionStreamResponse(BaseModel):
    """Streaming chat completion response"""
    id: str
    object: str = "chat.completion.chunk"
    created: int
    model: str
    choices: List[StreamingChoice]
    usage: Optional[Usage] = None

class ChatCompletionRequest(BaseModel):
    """Chat completion request"""
    model: str
    messages: List[Message]
    temperature: Optional[float] = 0.7
    top_p: Optional[float] = 1.0
    n: Optional[int] = 1
    stream: Optional[bool] = False
    stop: Optional[Union[str, List[str]]] = None
    max_tokens: Optional[int] = None
    presence_penalty: Optional[float] = 0.0
    frequency_penalty: Optional[float] = 0.0
    logit_bias: Optional[Dict[str, float]] = None
    user: Optional[str] = None
    functions: Optional[List[Dict[str, Any]]] = None
    function_call: Optional[Union[str, Dict[str, Any]]] = None
    # New field for tools
    tools: Optional[List[Dict[str, Any]]] = None
    tool_choice: Optional[Union[str, Dict[str, Any]]] = None