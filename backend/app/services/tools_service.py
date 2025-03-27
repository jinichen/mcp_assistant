from typing import List, Dict, Any, Optional
import logging
from app.mcp_adapters.manager import MCPServiceManager

logger = logging.getLogger(__name__)

async def execute_tool(tool_name: str, parameters: Dict[str, Any]) -> Any:
    """Execute a tool with the given parameters"""
    try:
        # Get MCP service manager
        manager = MCPServiceManager()
        
        # Get tool by name
        tool = manager.get_tool_by_name(tool_name)
        if not tool:
            raise ValueError(f"Tool '{tool_name}' not found")
            
        # Execute tool with parameters
        result = await tool.arun(**parameters)
        return result
        
    except Exception as e:
        logger.error(f"Error executing tool {tool_name}: {str(e)}")
        raise

def get_available_tools() -> List[Dict[str, Any]]:
    """Get a list of available tools in the system"""
    try:
        # Get MCP service manager
        manager = MCPServiceManager()
        
        # Get all tools
        tools = manager.get_all_tools()
        
        # Convert tools to OpenAI format
        formatted_tools = []
        for tool in tools:
            tool_def = {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": {}
                }
            }
            
            # Add parameter schema if available
            if hasattr(tool, 'args_schema'):
                schema = getattr(tool.args_schema, "__fields__", {})
                tool_def["function"]["parameters"] = {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
                
                for name, field in schema.items():
                    tool_def["function"]["parameters"]["properties"][name] = {
                        "type": str(field.type_),
                        "description": field.field_info.description
                    }
                    if field.required:
                        tool_def["function"]["parameters"]["required"].append(name)
                        
            formatted_tools.append(tool_def)
            
        return formatted_tools
        
    except Exception as e:
        logger.error(f"Error getting tools: {str(e)}")
        return [] 