import asyncio
import sys
import os
import logging

# Get the directory of the current file
current_dir = os.path.dirname(os.path.abspath(__file__))
# Add backend directory to Python path
backend_dir = os.path.dirname(current_dir)  # Get backend directory (parent directory of scripts)
sys.path.insert(0, backend_dir)

# Get project root directory (mcp-assistant directory)
project_root = os.path.dirname(backend_dir)  # Parent directory of backend directory

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Now try to import modules
from app.mcp_adapters.client import MCPClient
from app.mcp_adapters.initialization import get_mcp_tools
from app.models.chat import ChatCompletionRequest, ChatMessage
from app.services.chat_service import ChatService

async def test_full_integration():
    """Test full integration"""
    try:
        # Get MCP client instance
        client = MCPClient()
        
        # Build the correct path to calculator_server.py
        calculator_path = os.path.join(project_root, "mcp-servers", "calculator", "calculator_server.py")
        logger.info(f"Calculator server path: {calculator_path}")
        
        # Check if the file exists
        if not os.path.exists(calculator_path):
            logger.error(f"Calculator server file not found at: {calculator_path}")
            return
        
        # Initialize the client directly here, instead of using the initialization module
        config = {
            "calculator": {
                "transport": "stdio",
                "command": "python",
                "args": [calculator_path]  # Use absolute path
            }
        }
        
        logger.info("Initializing MCP client directly...")
        success = await client.initialize(config)
        if not success:
            logger.error("Failed to initialize MCP client")
            return
            
        logger.info("MCP client initialized successfully")
        
        # Get tools
        tools = client.get_tools()
        logger.info(f"Loaded {len(tools)} tools")
        logger.info(f"Available tool names: {[tool.name for tool in tools]}")
        
        # Create chat service
        chat_service = ChatService()
        
        # Create a test request
        request = ChatCompletionRequest(
            model="gpt-3.5-turbo",
            messages=[
                ChatMessage(role="system", content="You are a helpful assistant that can use tools."),
                ChatMessage(role="user", content="What is 25 + 17?")
            ],
            temperature=0.7,
            tools=[
                {
                    "type": "function",
                    "function": {
                        "name": "Add two numbers together",
                        "description": "Add two numbers together",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "a": {"type": "number"},
                                "b": {"type": "number"}
                            },
                            "required": ["a", "b"]
                        }
                    }
                }
            ]
        )
        
        # Generate reply
        logger.info("Generating chat completion...")
        response = await chat_service.generate_chat_completion(request)
        
        # Print results
        logger.info(f"Response: {response}")
        logger.info(f"Content: {response.choices[0].message.content}")
        
        # Check if there are tool calls
        if response.choices[0].message.tool_calls:
            logger.info("Tool calls detected:")
            for tool_call in response.choices[0].message.tool_calls:
                logger.info(f"  Tool: {tool_call.function.name}")
                logger.info(f"  Args: {tool_call.function.arguments}")
                
                # Try to execute tool calls
                # Find tool by name, considering both original name and converted name
                tool_name = tool_call.function.name
                original_name = "Add two numbers together"  # We know the actual name
                
                # Try to find with the provided name
                tool = next((t for t in tools if t.name == tool_name), None)
                
                # If not found, try with the original name
                if tool is None and tool_name != original_name:
                    tool = next((t for t in tools if t.name == original_name), None)
                    
                if tool:
                    logger.info(f"  Found tool: {tool.name}")
                    result = await tool.ainvoke(tool_call.function.arguments)
                    logger.info(f"  Result: {result}")
                else:
                    logger.error(f"  Tool not found: {tool_name} or {original_name}")
        
    except Exception as e:
        logger.error(f"Error in full integration test: {e}")
        import traceback
        logger.error(traceback.format_exc())
    finally:
        # Close the client in the same function
        logger.info("Closing MCP client...")
        client = MCPClient()  # Get singleton instance
        await client.close()
        logger.info("MCP client closed")

if __name__ == "__main__":
    asyncio.run(test_full_integration())