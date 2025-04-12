"""
MCP routes - API endpoints for MCP tool functionality
"""
import json
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.message import ChatRequest
from app.mcp import service as mcp_service

# Create router
router = APIRouter(prefix="/api/v1/mcp", tags=["MCP"])

# Models for additional endpoints
class Message(BaseModel):
    role: str
    content: str

class MCPChatRequest(BaseModel):
    messages: List[Message]

class ToolInfo(BaseModel):
    name: str
    description: str

class ToolInfoResponse(BaseModel):
    tools: List[ToolInfo]

class ChatResponse(BaseModel):
    message: str
    tool_info: Optional[Dict[str, Any]] = None

@router.get("/tools")
async def get_tools(current_user: User = Depends(get_current_user)):
    """List available MCP tools"""
    tools_data = await mcp_service.get_available_tools()
    
    tool_infos = []
    for tool in tools_data["tools"]:
        tool_infos.append(ToolInfo(
            name=tool["name"],
            description=tool["description"]
        ))
    
    return ToolInfoResponse(tools=tool_infos)

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