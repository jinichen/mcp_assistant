from fastapi import APIRouter, HTTPException, Path, Depends, Query
from typing import Dict, Any, List, Optional
import logging
import json
import re

from app.services.tools_service import execute_tool, get_available_tools

# Set up router
router = APIRouter(
    prefix="/tools",
    tags=["tools"],
)
logger = logging.getLogger(__name__)

@router.post("/{tool_name}")
async def execute_tool_endpoint(
    tool_name: str = Path(..., description="Tool name to execute"),
    parameters: Dict[str, Any] = {},
):
    """Execute a tool with the given parameters"""
    
    # Get tool name and parameters
    if tool_name.endswith(".call"):
        tool_name = tool_name[:-5]  # Remove ".call" suffix if present
    
    logging.info(f"Executing tool: {tool_name}, parameters: {parameters}")
    
    try:
        # Execute tool through service
        result = await execute_tool(tool_name, parameters)
        return {"result": result}
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logging.error(f"Error executing tool {tool_name}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error executing tool: {str(e)}")
    
@router.get("/")
async def list_tools():
    """Get list of available tools"""
    return {"tools": get_available_tools()}