#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test script for MCP connector
Tests both calculator and DuckDuckGo search services
"""

import asyncio
import logging
import os
from dotenv import load_dotenv
from langchain_mcp_adapters.client import MultiServerMCPClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    """Main test function."""
    # Load environment variables
    load_dotenv()
    
    # Define server configurations
    server_configs = {
        "calculator": {
            "transport": "stdio",
            "command": "/opt/miniconda3/bin/python",
            "args": ["/Users/chenhongbo/ian/mcp-assistant/mcp-servers/calculator/calculator_server.py"]
        },
        "duckduckgo": {
            "transport": "stdio",
            "command": "/opt/miniconda3/bin/python",
            "args": ["/Users/chenhongbo/ian/mcp-assistant/mcp-servers/duckduckgo/duckduckgo_server.py"]
        }
    }
    
    # Connect to MCP services
    logger.info("Connecting to MCP services...")
    async with MultiServerMCPClient(server_configs) as client:
        logger.info("Connected to MCP services!")
        
        # Print client details
        print("\nClient details:")
        print(f"Client type: {type(client)}")
        print(f"Client attributes: {dir(client)}")
        
        # Print sessions
        print("\nSessions:")
        for server_name, session in client.sessions.items():
            print(f"  - Server: {server_name}")
            print(f"    Session: {session}")
            print(f"    Session type: {type(session)}")
            print(f"    Session attributes: {dir(session)}")
            
            # Try to list tools from this session
            try:
                tools = await session.list_tools()
                print(f"    Tools from list_tools(): {tools}")
            except Exception as e:
                print(f"    Error listing tools: {e}")
        
        # Print server name to tools mapping
        print("\nServer name to tools mapping:")
        for server_name, tools in client.server_name_to_tools.items():
            print(f"  - Server: {server_name}, Tools: {tools}")
        
        # Print all loaded tools
        tools = client.get_tools()
        print(f"\nLoaded {len(tools)} tools from get_tools():")
        for i, tool in enumerate(tools, 1):
            print(f"  - {i}: {tool.name}: {tool.description}")
        
        # Try direct connection to DuckDuckGo
        print("\nTrying direct connection to DuckDuckGo...")
        try:
            # Create a new client with DuckDuckGo configuration
            ddg_config = {
                "duckduckgo": {
                    "transport": "stdio",
                    "command": "/opt/miniconda3/bin/python",
                    "args": ["/Users/chenhongbo/ian/mcp-assistant/mcp-servers/duckduckgo/duckduckgo_server.py"]
                }
            }
            async with MultiServerMCPClient(ddg_config) as ddg_client:
                # List tools
                tools = await ddg_client.sessions["duckduckgo"].list_tools()
                print(f"DuckDuckGo tools: {tools}")
        except Exception as e:
            print(f"Error with direct connection: {e}")
        
        logger.info("Disconnecting...")
    
    logger.info("Disconnected")

if __name__ == "__main__":
    asyncio.run(main())