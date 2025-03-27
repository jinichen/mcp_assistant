from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

def add_cors_middleware(app: FastAPI) -> None:
    """Add CORS middleware to FastAPI application"""
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Allow all origins, should be restricted in production
        allow_credentials=True,
        allow_methods=["*"],  # Allow all methods
        allow_headers=["*"],  # Allow all headers
    )
    return app 