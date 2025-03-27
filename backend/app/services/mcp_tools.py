"""
Custom MCP tools loader that fixes the issue with list_tools vs get_tools
"""

import logging
import json
from typing import List, Any, Dict, Callable, Optional
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain.tools import BaseTool
from langchain_core.tools import Tool

logger = logging.getLogger(__name__)

async def custom_load_mcp_tools(client: MultiServerMCPClient) -> List[BaseTool]:
    """
    Load MCP tools from a MultiServerMCPClient instance
    
    This function replaces the buggy langchain_mcp_adapters.tools.load_mcp_tools
    by correctly using get_tools() instead of list_tools()
    
    Args:
        client: The MCP client instance
        
    Returns:
        A list of LangChain tools
    """
    tools = []
    
    # Add call_tool_async method to client if it doesn't exist
    if not hasattr(client, 'call_tool_async'):
        # This is a custom implementation of call_tool_async that uses the existing run_tool method
        async def call_tool_async(tool_name: str, tool_args: Dict[str, Any]) -> Any:
            """Call a tool asynchronously"""
            logger.info(f"Calling tool {tool_name} with args {tool_args}")
            # Use the run_tool method that should exist on the client
            try:
                if hasattr(client, 'run_tool'):
                    result = await client.run_tool(tool_name, tool_args)
                else:
                    # Fallback to synchronous call_tool if run_tool doesn't exist
                    result = client.call_tool(tool_name, tool_args)
                logger.info(f"Tool result: {result}")
                return result
            except Exception as e:
                logger.error(f"Error calling tool {tool_name}: {e}")
                return f"Error: {e}\n Please fix your mistakes."
        
        # Add the method to the client instance
        client.call_tool_async = call_tool_async.__get__(client)
    
    try:
        # Get MCP tools
        mcp_tools = client.get_tools()
        logger.info(f"Loaded {len(mcp_tools)} MCP tools")
        
        # Convert each MCP tool to a LangChain tool
        for i, tool in enumerate(mcp_tools):
            logger.info(f"Tool {i+1} details - Name: {getattr(tool, 'name', 'unknown')}")
            logger.info(f"Tool {i+1} description: {getattr(tool, 'description', 'no description')}")
            
            # Safely handle parameters which may not exist in StructuredTool
            params = {}
            if hasattr(tool, 'parameters'):
                params = tool.parameters
            elif hasattr(tool, 'args_schema'):
                params = getattr(tool, 'args_schema', {})
            logger.info(f"Tool {i+1} parameters: {params}")
            
            try:
                # Make search tool names more explicit
                name = getattr(tool, 'name', f"tool_{i}")
                description = getattr(tool, 'description', '')
                
                # Enhance tool descriptions based on functionality
                if "search" in name.lower():
                    name = "web_search" if name == "search" else name
                    description = f"USE THIS TOOL FOR SEARCH QUERIES. {description} This web search tool can find real-time information about current events, people, facts, or any topic you need information about."
                elif any(calc_term in name.lower() for calc_term in ["add", "multiply", "subtract", "divide", "calculator"]):
                    description = f"USE THIS TOOL FOR MATHEMATICAL CALCULATIONS. {description}"
                
                # Create a LangChain tool from the MCP tool
                langchain_tool = Tool(
                    name=name,
                    description=description,
                    func=lambda tool_name=name, client=client, **kwargs: client.call_tool(tool_name, kwargs),
                    coroutine=lambda tool_name=name, client=client, **kwargs: client.call_tool_async(tool_name, kwargs),
                )
                tools.append(langchain_tool)
                logger.info(f"Converted MCP tool to LangChain tool: {name}")
                
            except Exception as e:
                logger.error(f"Error converting MCP tool to LangChain tool: {e}")
        
        return tools
    except Exception as e:
        logger.error(f"Error loading MCP tools: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        # Return empty list if error occurs
        return [] 