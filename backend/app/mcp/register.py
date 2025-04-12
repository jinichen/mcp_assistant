"""
MCP registration module - Integrates MCP functionality with the main application
"""
import logging
from fastapi import FastAPI
from app.mcp import service as mcp_service

logger = logging.getLogger(__name__)

def register_mcp_components(app: FastAPI):
    """
    Register MCP components with main application
    
    This registers routes and shutdown handlers, but does not 
    automatically initialize MCP tools. Tools will be initialized
    on first use to prevent unnecessary resource consumption.
    """
    
    # Try to import MCP routes
    try:
        from app.mcp.fixed_routes import router as mcp_router
        app.include_router(mcp_router)
        logger.info("MCP components registered with the main application")
    except ImportError as e:
        logger.warning(f"MCP routes not available: {str(e)}")
    
    # Only register the shutdown event
    # MCP will be lazily initialized on first use
    @app.on_event("shutdown")
    async def shutdown_mcp_service():
        logger.info("Shutting down MCP service")
        await mcp_service.cleanup_mcp() 