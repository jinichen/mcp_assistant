import asyncio
import sys
import os
import logging

# Set Python path, add the parent directory of the current directory (backend directory)
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.mcp_adapters.client import MCPClient
from app.mcp_adapters.initialization import initialize_mcp_services, get_mcp_tools

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def load_and_test_tools():
    """Load and test MCP tools"""
    try:
        # Initialize MCP services
        services = await initialize_mcp_services()
        logger.info(f"Initialized services: {services}")
        
        # Get tools
        tools = get_mcp_tools()
        logger.info(f"Loaded {len(tools)} tools")
        
        if tools:
            for tool in tools:
                logger.info(f"Tool: {tool.name} - {tool.description}")
                
            # Test addition tool
            if any(t.name == "calculator.add" for t in tools):
                add_tool = next(t for t in tools if t.name == "calculator.add")
                result = await add_tool.ainvoke("2, 3")
                logger.info(f"Calculator.add(2, 3) = {result}")
        else:
            logger.warning("No tools found")
    except Exception as e:
        logger.error(f"Error loading MCP tools: {e}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    asyncio.run(load_and_test_tools())