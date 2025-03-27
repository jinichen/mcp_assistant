from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import StreamingResponse
from typing import List, Dict, Any, Optional
import json
import logging

from app.services.chat_service import ChatService
from app.models.model_factory import ModelFactory

# Set up routes
router = APIRouter(prefix="/chat", tags=["chat"])
chat_service = ChatService()
model_factory = ModelFactory()

@router.get("/models")
async def get_models(provider: Optional[str] = None):
    """Get available models for a provider, or all providers if not specified"""
    try:
        if provider:
            # Get models for specific provider
            models = model_factory.get_provider_models(provider)
            return {"models": {provider: models}}
        else:
            # Get all models grouped by provider
            all_models = model_factory.get_all_models()
            return {"models": all_models}
    except Exception as e:
        logging.error(f"Error getting models: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/completions")
async def chat_completions(request: Request):
    """Process chat requests and return responses"""
    try:
        body = await request.json()
        messages = body.get("messages", [])
        model = body.get("model", "gemini-1.5-pro")
        stream = body.get("stream", False)
        tools = body.get("tools", [])
        tool_choice = body.get("tool_choice", "auto")
        session_id = body.get("session_id")
        
        if stream:
            return StreamingResponse(
                chat_service.stream_chat_completion(messages, model, tools, tool_choice, session_id),
                media_type="text/event-stream"
            )
        else:
            response = await chat_service.chat_completion(messages, model, tools, tool_choice, session_id)
            return response
    except Exception as e:
        logging.error(f"Error in chat_completions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))