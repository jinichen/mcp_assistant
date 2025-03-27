import logging
import os
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Set logging level
logging.basicConfig(level=logging.INFO)

# Load environment variables
load_dotenv()

# Initialize default model
os.environ.setdefault("DEFAULT_MODEL", "gemini-1.5-pro")
os.environ.setdefault("DEFAULT_PROVIDER", "google")

# Create FastAPI application
app = FastAPI(
    title="AI Chat API",
    description="REST API for AI chat services",
    version="0.1.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins, should be restricted in production
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)

# Import and include routes
from app.api.routes import router as api_router

# Register routes
app.include_router(api_router, prefix="/api")

@app.get("/")
async def root():
    return {"message": "Welcome to AI Chat API", "status": "online"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)