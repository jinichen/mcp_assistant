import asyncio
import os
from dotenv import load_dotenv
from app.mcp_adapters.client import MCPClient
from app.mcp_adapters.initialization import initialize_mcp_services, get_mcp_tools, close_mcp_services

# Load environment variables
load_dotenv()

async def test_mcp_client():
    # Test configuration
    config = {
        "calculator": {
            "transport": "stdio",
            "command": "python",
            "args": ["../mcp-servers/calculator/calculator_server.py"]
        }
    }
    
    # Get client instance
    client = MCPClient()
    
    # Initialize
    print("Initializing MCP client...")
    success = await client.initialize(config)
    
    if success:
        print("Initialization successful!")
        
        # Get tools
        tools = client.get_tools()
        print(f"Loaded {len(tools)} tools:")
        
        for tool in tools:
            print(f"  - {tool.name}: {tool.description}")
        
        # Close connection
        print("\nClosing client...")
        await client.close()
        print("Client closed")
    else:
        print("Initialization failed")

    # Test initialization function
    print("\nTesting initialization function...")
    services = await initialize_mcp_services()
    print(f"Initialized services: {services}")
    
    tools = get_mcp_tools()
    print(f"Available tools: {len(tools)}")
    
    await close_mcp_services()
    print("Services closed")

if __name__ == "__main__":
    asyncio.run(test_mcp_client())