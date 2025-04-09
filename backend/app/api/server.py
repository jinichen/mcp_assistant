from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_app_settings
from app.api.routes import api_router

def create_application() -> FastAPI:
    settings = get_app_settings()
    
    application = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json"
    )
    
    # Set CORS middleware
    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include API router
    application.include_router(api_router, prefix=settings.API_V1_STR)
    
    return application

app = create_application() 