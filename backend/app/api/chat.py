from typing import Optional, Dict, Any, List
from fastapi import APIRouter, HTTPException, Depends, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from uuid import UUID
import json
from app.models.api_models import (
    CreateSessionRequest, SendMessageRequest, 
    SessionResponse, MessageResponse, SessionListResponse,
    ProviderListResponse, ModelListResponse
)
from app.services.session_service import SessionService
from app.services.chat_service import ChatService
from app.models.model_factory import ModelFactory
from fastapi import Request, Response, BackgroundTasks
from pydantic import BaseModel
import logging
import asyncio

# 创建一个能够安全处理各种数据类型的StreamingResponse子类
class SafeStreamingResponse(StreamingResponse):
    """
    A StreamingResponse subclass that safely handles any data type by ensuring
    all yielded items are strings before encoding them.
    """
    async def stream_response(self, send) -> None:
        await send({
            "type": "http.response.start",
            "status": self.status_code,
            "headers": self.raw_headers,
        })

        async for chunk in self.body_iterator:
            # 确保所有chunk都是字符串，如果是字典则转换为JSON
            if isinstance(chunk, dict):
                chunk = f"data: {json.dumps(chunk)}\n\n"
            elif not isinstance(chunk, (str, bytes)):
                chunk = f"data: {json.dumps(str(chunk))}\n\n"
                
            if not isinstance(chunk, bytes):
                chunk = chunk.encode(self.charset)
                
            await send({"type": "http.response.body", "body": chunk, "more_body": True})
            
        await send({"type": "http.response.body", "body": b"", "more_body": False})

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()
session_service = SessionService()
chat_service = ChatService()
model_factory = ModelFactory()

# Create new session
@router.post("/sessions", response_model=SessionResponse)
async def create_session(request: CreateSessionRequest):
    session = session_service.create_session(
        name=request.name,
        provider=request.provider,
        model=request.model,
        system_message=request.system_message
    )
    return SessionResponse(
        id=session.id,
        name=session.name,
        created_at=session.created_at,
        updated_at=session.updated_at,
        message_count=len(session.messages)
    )

# Get session list
@router.get("/sessions", response_model=SessionListResponse)
async def get_sessions():
    sessions = session_service.get_all_sessions()
    return SessionListResponse(
        sessions=[
            SessionResponse(
                id=session.id,
                name=session.name,
                created_at=session.created_at,
                updated_at=session.updated_at,
                message_count=len(session.messages)
            )
            for session in sessions
        ]
    )

# Get single session
@router.get("/sessions/{session_id}", response_model=SessionResponse)
async def get_session(session_id: UUID):
    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return SessionResponse(
        id=session.id,
        name=session.name,
        created_at=session.created_at,
        updated_at=session.updated_at,
        message_count=len(session.messages)
    )

# Delete session
@router.delete("/sessions/{session_id}")
async def delete_session(session_id: UUID):
    success = session_service.delete_session(session_id)
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"success": True}

# Send message
@router.post("/chat/{session_id}/messages")
async def send_message(
    session_id: str,
    request: MessageRequest,
):
    """Send a message to a chat session, supporting streaming"""
    try:
        logger.info(f"Chat message request: session_id={session_id}, provider={request.provider}, model={request.model}")
        
    if request.stream:
            # 使用StreamingResponse和generate_chat_message_stream生成器
        return StreamingResponse(
                content=generate_chat_message_stream(
                session_id=session_id,
                    message_content=request.content,
                provider=request.provider,
                model=request.model,
                parameters=request.parameters
            ),
            media_type="text/event-stream"
        )
        else:
            # 非流式响应处理
        response = await chat_service.send_message(
            session_id=session_id,
                message_content=request.content,
            provider=request.provider,
            model=request.model,
            parameters=request.parameters
        )
            return response
        
    except Exception as e:
        logger.error(f"Error sending message: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# 抽取聊天消息流生成器函数
async def generate_chat_message_stream(session_id, message_content, provider, model, parameters):
    """为聊天消息生成流式内容，确保字符串输出"""
    try:
        async for chunk in chat_service.stream_message(
            session_id=session_id,
            message_content=message_content,
            provider=provider,
            model=model,
            parameters=parameters
        ):
            # 直接传递service层返回的格式化字符串
            yield chunk
        
        # End of stream marker
        yield "data: [DONE]\n\n"
    except Exception as e:
        logger.error(f"Error in stream_message: {str(e)}")
        error_json = json.dumps({"error": str(e)})
        yield f"data: {error_json}\n\n"
        yield "data: [DONE]\n\n"

# WebSocket chat endpoint
@router.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    await websocket.accept()
    
    try:
        while True:
            # Receive WebSocket message
            data = await websocket.receive_text()
            request_data = json.loads(data)
            
            # Process message request
            session_id = request_data.get("session_id")
            if not session_id:
                # Create new session
                session = session_service.create_session(
                    provider=request_data.get("provider"),
                    model=request_data.get("model")
                )
                session_id = str(session.id)
                # Return session ID
                await websocket.send_json({"type": "session_created", "session_id": session_id})
            else:
                session_id = UUID(session_id)
            
            # Send message and get streaming response
            async for chunk in chat_service.stream_message(
                session_id=session_id,
                message_content=request_data.get("message", ""),
                provider=request_data.get("provider"),
                model=request_data.get("model"),
                parameters=request_data.get("parameters")
            ):
                # Safely handle different chunk types
                response_data = {"type": "chunk"}
                if isinstance(chunk, dict):
                    response_data["content"] = chunk
                else:
                    response_data["content"] = str(chunk)
                
                # Send streaming response
                await websocket.send_json(response_data)
            
            # Send completion signal
            await websocket.send_json({"type": "done"})
    
    except WebSocketDisconnect:
        # Client disconnected
        pass
    except Exception as e:
        # Error occurred
        if websocket.client_state.CONNECTED:
            await websocket.send_json({"type": "error", "message": str(e)})

# Get available providers list
@router.get("/providers", response_model=ProviderListResponse)
async def get_providers():
    providers = model_factory.get_available_providers()
    return ProviderListResponse(providers=providers)

# Get available models list
@router.get("/models", response_model=ModelListResponse)
async def get_models(provider: Optional[str] = None):
    models = model_factory.get_available_models(provider)
    return ModelListResponse(models=models)

class ChatRequest(BaseModel):
    messages: List[Dict[str, Any]]
    model: str = "gemini-2.0-pro-exp-02-05"
    tools: Optional[List[Dict[str, Any]]] = None
    tool_choice: Optional[str] = "auto"
    stream: bool = False

@router.post("/chat/completions")
async def chat_completions(request: ChatRequest):
    """
    Endpoint for chat completions, supporting both streaming and non-streaming responses.
    """
    try:
        logger.info(f"Chat completion request: {request.model}, streaming={request.stream}")
        
        # 如果请求流式响应
        if request.stream:
            # 使用StreamingResponse并传递生成器函数
            return StreamingResponse(
                content=generate_chat_stream(
                    messages=request.messages,
                    model=request.model,
                    tools=request.tools,
                    tool_choice=request.tool_choice,
                    session_id=request.session_id
                ),
            media_type="text/event-stream"
        )
    else:
            # 非流式响应
            response = await chat_service.chat_completion(
                messages=request.messages,
                model=request.model,
                tools=request.tools,
                tool_choice=request.tool_choice,
                session_id=request.session_id
            )
            return response
            
    except Exception as e:
        logger.error(f"Error in chat_completions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# 抽取生成器函数，确保它总是返回字符串而不是字典
async def generate_chat_stream(messages, model, tools, tool_choice, session_id):
    """Generate streaming chat content, ensuring string outputs"""
    try:
        async for chunk in chat_service.stream_chat_completion(
            messages=messages,
            model=model,
            tools=tools,
            tool_choice=tool_choice,
            session_id=session_id
        ):
            # 直接传递service层返回的格式化字符串
            yield chunk
            
        # 发送结束标记
        yield "data: [DONE]\n\n"
    except Exception as e:
        logger.error(f"Streaming generation event error: {str(e)}")
        error_json = json.dumps({"error": str(e)})
        yield f"data: {error_json}\n\n"
        yield "data: [DONE]\n\n"

class SSERequest(BaseModel):
    """Request model for SSE streaming API"""
    query: str
    model: str = "gemini-1.5-pro"
    provider: Optional[str] = None

@router.get("/sse-chat")
async def sse_chat_endpoint(request: SSERequest):
    """Server-Sent Events endpoint for chat"""
    try:
        logger.info(f"SSE Chat request: query={request.query}, model={request.model}")
        
        # 使用StreamingResponse和generate_sse_stream生成器函数
        return StreamingResponse(
            content=generate_sse_stream(request),
            media_type="text/event-stream"
        )
    except Exception as e:
        logger.error(f"Error in SSE chat: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# 抽取SSE生成器函数，确保它总是返回字符串
async def generate_sse_stream(request):
    """Generate SSE streaming content, ensuring string outputs"""
    try:
        # 创建用户消息
        user_message = {"role": "user", "content": request.query}
        messages = [user_message]
        
        async for chunk in chat_service.stream_chat_completion(
            messages=messages,
            model=request.model,
            tools=None,
            tool_choice=None,
            session_id=None
        ):
            # 处理来自chat_service的data格式响应，转换为SSE格式
            if chunk.startswith("data: "):
                try:
                    # 提取JSON数据
                    json_str = chunk[6:].strip()
                    data = json.loads(json_str)
                    
                    # 检查数据类型，相应地构建SSE事件
                    if "error" in data:
                        yield f"event: error\ndata: {json_str}\n\n"
                    elif "content" in data:
                        # 将content作为纯文本传递，不需要JSON包装
                        yield f"event: data\ndata: {data['content']}\n\n"
                    elif "choices" in data and len(data["choices"]) > 0:
                        # 处理OpenAI/NVIDIA格式
                        if "delta" in data["choices"][0] and "content" in data["choices"][0]["delta"]:
                            content = data["choices"][0]["delta"]["content"]
                            yield f"event: data\ndata: {content}\n\n"
                    else:
                        # 直接传递JSON数据
                        yield f"event: data\ndata: {json_str}\n\n"
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse JSON from chunk: {chunk}")
                    # 退回到直接传递内容
                    yield f"event: data\ndata: {chunk[6:].strip()}\n\n"
            else:
                # 处理没有data:前缀的内容
                yield f"event: data\ndata: {chunk}\n\n"
                
        # 发送结束标记
        yield f"event: end\ndata: complete\n\n"
        except Exception as e:
        logger.error(f"SSE generation error: {str(e)}")
        error_json = json.dumps({"error": str(e)})
        yield f"event: error\ndata: {error_json}\n\n"
        yield f"event: end\ndata: error\n\n"