from fastapi import APIRouter, Request, Response
from fastapi.responses import StreamingResponse
import json
import logging
from app.mcp_adapters.manager import MCPServiceManager

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/sse")
async def handle_sse(request: Request):
    """Handle SSE connection requests"""
    try:
        # Get query parameters
        transport_type = request.query_params.get("transportType", "stdio")
        command = request.query_params.get("command")
        args = request.query_params.get("args")
        env = json.loads(request.query_params.get("env", "{}"))
        
        logger.info(f"Received SSE request: transport={transport_type}, command={command}, args={args}")
        
        # Get MCP service manager
        manager = MCPServiceManager()
        
        # Get service connector
        connector = manager.get_service_connector("calculator")
        if not connector:
            return Response(status_code=404, content="Calculator service not found")
        
        # Connect if not already connected
        if not connector.is_connected:
            success = await connector.connect()
            if not success:
                return Response(status_code=500, content="Failed to connect to calculator service")
        
        # Return success response
        return Response(status_code=200, content="Connected to calculator service")
        
    except Exception as e:
        logger.error(f"Error handling SSE request: {str(e)}")
        return Response(status_code=500, content=str(e)) 