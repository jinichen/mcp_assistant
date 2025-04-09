from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union
from app.schemas.chat import ChatRequest, ChatResponse, Message
import logging
from app.services.mcp_client import get_mcp_assistant

# Remove prefix, as the prefix will be added in main.py
router = APIRouter(tags=["mcp"])
logger = logging.getLogger(__name__)

# Extend ChatRequest to support MCP
class MCPChatRequest(ChatRequest):
    tool: Optional[str] = None
    conversation_id: Optional[str] = None  # Make it optional to simplify testing

@router.post("/complete", response_model=ChatResponse)
async def complete_chat(chat_request: MCPChatRequest):
    """Process chat requests using MCP client to automatically select appropriate tools"""
    
    # Get user message
    user_message = chat_request.messages[0].content if chat_request.messages else ""
    
    logger.info(f"Processing chat request with MCP assistant: {user_message}")
    
    if not user_message:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Message content cannot be empty"
        )
    
    try:
        # Process message with MCP assistant
        logger.info("Getting MCP assistant instance")
        mcp_assistant = get_mcp_assistant()
        logger.info(f"MCP assistant initialized: {mcp_assistant.is_initialized}")
        
        if not mcp_assistant.is_initialized:
            logger.info("MCP assistant not initialized, initializing now")
            await mcp_assistant.initialize()
            
        logger.info("Calling MCP assistant process_message")
        response_text = await mcp_assistant.process_message(user_message)
        logger.info(f"Got response from MCP assistant: {response_text[:100]}...")
        
        return ChatResponse(
            message=Message(role="assistant", content=response_text)
        )
    except Exception as e:
        logger.error(f"Error processing chat request: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing chat request: {str(e)}"
        ) 