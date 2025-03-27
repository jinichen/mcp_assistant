import asyncio
import os
from dotenv import load_dotenv
from app.mcp_adapters.manager import MCPServiceManager
from app.mcp_adapters.initialization import initialize_mcp_services

# Load environment variables
load_dotenv()

async def test_mcp_manager():
    # Get manager instance
    manager = MCPServiceManager()
    
    # Register services from config file
    print("Initializing services from config...")
    services = await initialize_mcp_services()
    
    print(f"Initialized services: {services}")
    
    # Or manually register services
    # await manager.register_service(
    #     service_name="Calculator",
    #     transport="stdio",
    #     command="python",
    #     args=["../mcp-servers/calculator/calculator_server.py"]
    # )
    
    # Get all services
    service_names = manager.get_service_names()
    print(f"Registered services: {service_names}")
    
    # Get all tools
    tools = manager.get_all_tools()
    print(f"Available tools ({len(tools)}):")
    
    for tool in tools:
        print(f"  - {tool.name}: {tool.description}")
    
    # Disconnect all connections
    print("\nDisconnecting all services...")
    await manager.disconnect_all()
    print("All services disconnected")

if __name__ == "__main__":
    asyncio.run(test_mcp_manager())