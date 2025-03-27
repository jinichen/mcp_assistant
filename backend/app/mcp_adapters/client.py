import os
import asyncio
import logging
from typing import Optional, List, Dict, Any
from langchain.tools import BaseTool
from langchain.prompts.chat import ChatPromptTemplate

logger = logging.getLogger(__name__)

"""MCP client singleton, using the official MultiServerMCPClient implementation"""

class MCPClient:
    """
    MCP Client singleton wrapper around official MCP client
    
    This class manages a single instance of the MCP client to ensure
    consistent access across the application
    """
    _instance = None
    _client = None
    _is_connected = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MCPClient, cls).__new__(cls)
        return cls._instance
    
    async def connect(self) -> bool:
        """Initialize MCP service connection"""
        try:
            # Close existing connection
            if self._is_connected and self._client:
                await self.disconnect()
                
            # Create client but don't use context manager to close it
            try:
                from mcp.server import MultiServerMCPClient
                self._client = MultiServerMCPClient()
                await self._client.connect()
                self._is_connected = True
                logger.info("Connected to MCP services")
                return True
            except ImportError:
                logger.error("Failed to import MCP client. Is the package installed?")
                return False
        except Exception as e:
            logger.error(f"Failed to connect to MCP services: {str(e)}")
            self._is_connected = False
            return False
    
    async def disconnect(self) -> bool:
        """Close MCP service connection"""
        if self._is_connected and self._client:
            try:
                await self._client.disconnect()
                self._is_connected = False
                logger.info("Disconnected from MCP services")
                return True
            except Exception as e:
                logger.error(f"Error disconnecting from MCP services: {str(e)}")
                return False
        return True
    
    @property
    def is_connected(self) -> bool:
        """Check if MCP client is connected"""
        return self._is_connected and self._client is not None
    
    @property
    def client(self):
        """Get underlying MCP client instance"""
        if not self.is_connected:
            logger.warning("Attempting to access MCP client when not connected")
        return self._client
    
    def get_tools(self) -> List[BaseTool]:
        """Get available tools from MCP client"""
        if not self.is_connected or not self._client:
            return []
        
        try:
            return self._client.get_tools()
        except Exception as e:
            logger.error(f"Error getting MCP tools: {str(e)}")
            return []
    
    async def run_tool(self, tool_name: str, **kwargs) -> Any:
        """
        Run a specific MCP tool
        
        Args:
            tool_name: Name of the tool to run
            **kwargs: Tool arguments
            
        Returns:
            Tool execution result
        """
        if not self.is_connected or not self._client:
            raise ConnectionError("MCP client is not connected")
        
        try:
            return await self._client.run_tool(tool_name, **kwargs)
        except Exception as e:
            logger.error(f"Error running MCP tool {tool_name}: {str(e)}")
            raise
    
    async def __aenter__(self):
        """Context manager entry"""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        await self.disconnect()