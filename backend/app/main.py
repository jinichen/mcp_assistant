from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
import logging
from app.services.mcp_client import get_mcp_assistant
from app.api.server import app as api_app  # Import original API application
from app.routers import chat as mcp_chat  # Import MCP router and rename

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

app = api_app  # Use the original API application

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Add API version prefix
API_V1_STR = "/api/v1"

# Add MCP router to the original application, using a dedicated prefix to avoid conflicts with existing routes
app.include_router(mcp_chat.router, prefix="/api/v1/mcp")

@app.on_event("startup")
async def startup_event():
    """Initialize services on app startup"""
    try:
        # Initialize MCP assistant
        logging.info("Starting MCP assistant initialization")
        mcp_assistant = get_mcp_assistant()
        await mcp_assistant.initialize()
        logging.info("MCP assistant initialization completed")
    except Exception as e:
        logging.error(f"Error during MCP assistant initialization: {e}", exc_info=True)

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on app shutdown"""
    # Close MCP assistant
    mcp_assistant = get_mcp_assistant()
    await mcp_assistant.shutdown()

@app.get("/")
async def root():
    return {"message": "AI Assistant API"} 