"""
MCP routes - API endpoints for MCP tool functionality
"""
import json
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from langchain_core.runnables.config import RunnableConfig

from app.mcp.service import get_mcp_client, get_mcp_agent
from app.core.deps import get_current_user, get_current_active_user
from app.models.user import User
from app.core.auth import get_current_user
from app.schemas.message import ChatRequest
from app.mcp import service as mcp_service

# Create router
router = APIRouter(prefix="/api/v1/mcp", tags=["MCP"])

# Models
class Message(BaseModel):
    role: str
    content: str

class MCPChatRequest(BaseModel):
    messages: List[Message]

class ToolInfo(BaseModel):
    id: str
    name: str
    description: str
    transport: str

class ToolInfoResponse(BaseModel):
    tools: List[ToolInfo]

class ChatResponse(BaseModel):
    message: str
    tool_info: Optional[Dict[str, Any]] = None

@router.post("/tools")
async def list_tools(current_user: User = Depends(get_current_user)):
    """List available MCP tools"""
    return await mcp_service.get_available_tools()

@router.post("/complete")
async def complete_chat(
    request: ChatRequest, 
    current_user: User = Depends(get_current_user)
):
    """Complete chat using MCP tools"""
    return await mcp_service.handle_mcp_complete(request)

@router.post("/stream")
async def stream_chat(
    request: ChatRequest, 
    current_user: User = Depends(get_current_user)
):
    """Stream chat completion using MCP tools"""
    return await mcp_service.handle_mcp_stream(request)

@router.get("/tools", response_model=ToolInfoResponse)
async def list_tools(current_user: User = Depends(get_current_active_user)):
    """List all available MCP tools"""
    mcp_client = get_mcp_client()
    if not mcp_client:
        raise HTTPException(status_code=500, detail="MCP client not initialized")
    
    try:
        tools = mcp_client.get_tools()
        tool_infos = []
        
        for tool in tools:
            tool_infos.append(ToolInfo(
                id=tool.name,
                name=tool.name.capitalize(),
                description=tool.description,
                transport="mcp"
            ))
        
        return ToolInfoResponse(tools=tool_infos)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list tools: {str(e)}")

@router.post("/complete", response_model=ChatResponse)
async def complete_chat(
    request: MCPChatRequest,
    current_user: User = Depends(get_current_user)
):
    """Process chat requests using the React agent with MCP tools"""
    mcp_agent = get_mcp_agent()
    if not mcp_agent:
        raise HTTPException(status_code=500, detail="MCP agent not initialized")
    
    # Check if messages are empty
    if not request.messages or len(request.messages) == 0:
        raise HTTPException(status_code=400, detail="No messages provided")
    
    # Get the user message
    user_message = request.messages[-1].content
    if not user_message or user_message.strip() == "":
        raise HTTPException(status_code=400, detail="Empty user message")
    
    try:
        # Convert messages to the format expected by the agent
        input_messages = []
        for msg in request.messages:
            if msg.role == "user":
                input_messages.append({"type": "human", "content": msg.content})
            elif msg.role == "assistant":
                input_messages.append({"type": "ai", "content": msg.content})
        
        # Invoke the agent with the message
        response = await mcp_agent.ainvoke({"messages": input_messages})
        
        # Extract the response content
        result = ""
        if hasattr(response, 'content'):
            # Direct LangChain message object
            result = response.content
        elif isinstance(response, dict):
            if "messages" in response:
                # Get the last AI message from array
                for msg in reversed(response["messages"]):
                    if isinstance(msg, dict) and msg.get("type") == "ai":
                        result = msg.get("content", "")
                        break
                    elif hasattr(msg, "type") and msg.type == "ai":
                        result = msg.content
                        break
                else:
                    result = "No response generated"
            else:
                # Try to extract content from other response formats
                result = response.get("output", str(response))
        else:
            result = str(response)
        
        # Remove potential tags and quotes
        clean_result = result
        if '<think>' in clean_result and '</think>' in clean_result:
            think_start = clean_result.find('<think>')
            think_end = clean_result.find('</think>') + len('</think>')
            clean_result = clean_result[:think_start] + clean_result[think_end:]
            clean_result = clean_result.strip()
        
        # Fix incorrect line breaks
        clean_result = clean_result.replace('/n', '\n')
        
        # Return only clean content
        return ChatResponse(
            message=clean_result,
            tool_info={"agent": "react_agent"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process chat request: {str(e)}")

@router.post("/stream")
async def stream_chat(
    request: MCPChatRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """Process streaming chat requests using React agent"""
    mcp_agent = get_mcp_agent()
    if not mcp_agent:
        raise HTTPException(status_code=500, detail="MCP agent not initialized")
    
    # Check if messages are empty
    if not request.messages or len(request.messages) == 0:
        raise HTTPException(status_code=400, detail="No messages provided")
    
    # Get user message
    user_message = request.messages[-1].content
    if not user_message or user_message.strip() == "":
        raise HTTPException(status_code=400, detail="Empty user message")
    
    async def generate():
        try:
            # Convert to agent's expected format
            input_messages = []
            for msg in request.messages:
                if msg.role == "user":
                    input_messages.append({"type": "human", "content": msg.content})
                elif msg.role == "assistant":
                    input_messages.append({"type": "ai", "content": msg.content})
            
            # Prepare streaming configuration
            config = RunnableConfig(
                callbacks=None,
                tags=["mcp", "streaming"],
            )
            
            # Call agent using streaming interface
            async for chunk in mcp_agent.astream({"messages": input_messages}, config=config):
                # Extract chunk content
                result = ""
                if hasattr(chunk, 'content'):
                    result = chunk.content
                elif isinstance(chunk, dict):
                    # Handle different dict formats
                    if "messages" in chunk:
                        # Get the last message
                        messages = chunk["messages"]
                        if messages and len(messages) > 0:
                            last_msg = messages[-1]
                            if isinstance(last_msg, dict) and "content" in last_msg:
                                result = last_msg["content"]
                            elif hasattr(last_msg, "content"):
                                result = last_msg.content
                            else:
                                result = str(last_msg)
                        else:
                            result = ""
                    elif "content" in chunk:
                        result = chunk["content"]
                    elif "output" in chunk:
                        result = chunk["output"]
                    else:
                        result = str(chunk)
                else:
                    result = str(chunk)
                
                # Clean result content
                clean_result = result
                
                # Remove thinking tags
                if '<think>' in clean_result:
                    think_parts = clean_result.split('<think>')
                    for i in range(1, len(think_parts)):
                        if '</think>' in think_parts[i]:
                            think_parts[i] = think_parts[i].split('</think>', 1)[1]
                    clean_result = ''.join(think_parts)
                
                # Fix incorrect line breaks
                clean_result = clean_result.replace('/n', '\n')
                
                # Send clean content chunk
                if clean_result:
                    yield f"data: {json.dumps({'content': clean_result})}\n\n"
            
            # Send end event
            yield "data: [DONE]\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
            yield "data: [DONE]\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream"
        }
    ) 