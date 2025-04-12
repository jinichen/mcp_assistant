from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.core.config import get_app_settings
from app.api.routes import api_router

logger = logging.getLogger(__name__)

def create_application() -> FastAPI:
    settings = get_app_settings()
    
    application = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        docs_url="/api/docs",
    )
    
    # Setup CORS middleware
    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include API routes
    application.include_router(api_router, prefix="/api/v1")
    
    # Try to register Prometheus metrics (if available)
    if hasattr(settings, 'METRICS_ENABLED') and settings.METRICS_ENABLED:
        try:
            from app.api.endpoints.metrics import init_metrics
            init_metrics(application)
        except ImportError:
            logger.warning("Prometheus metrics dependencies not installed, skipping metrics setup")
    
    # Return application
    return application

# Create single application instance to be imported by uvicorn
app = create_application()

# Register MCP components if needed
try:
    from app.mcp.register import register_mcp_components
    register_mcp_components(app)
    logger.info("MCP components registered successfully")
    
    # Force MCP initialization at startup
    from app.mcp.service import initialize_mcp
    import asyncio
    asyncio.create_task(initialize_mcp(force_init=True))
    logger.info("MCP initialization task scheduled")
except ImportError:
    logger.warning("MCP components not available, skipping MCP registration") 