# Import routes
from fastapi import APIRouter, HTTPException
from typing import Optional
from app.models.model_factory import ModelFactory
import logging

# Create logger
logger = logging.getLogger(__name__)

# Create main router
router = APIRouter()

# Get model factory instance
model_factory = ModelFactory()

# Add models endpoint directly to main router
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
        logger.error(f"Error getting models: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Import sub-routes
from app.api.routes import sessions  
from app.routes import chat, tools
from app.routes import upload

# Include sub-routes
router.include_router(chat.router)
router.include_router(tools.router)
router.include_router(sessions.router)
router.include_router(upload.router)

__all__ = ["router"] 