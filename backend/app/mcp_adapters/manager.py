import os
import json
import logging
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
from langchain.tools import BaseTool
from .connector import MCPServiceConnector

logger = logging.getLogger(__name__)

class MCPServiceManager:
    """MCP service manager, responsible for managing multiple MCP service connections"""
    
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        # Dictionary to store service connectors
        self._connectors: Dict[str, MCPServiceConnector] = {}
        self._initialized = True
        logger.info("MCP Service Manager initialized")
    
    async def register_service(
        self,
        service_name: str,
        transport: str,
        **kwargs
    ) -> bool:
        """
        Register a new MCP service
        
        Args:
            service_name: Service name
            transport: Transport type ('stdio' or 'sse')
            **kwargs: Other connection parameters
            
        Returns:
            Whether registration was successful
        """
        try:
            # Create service connector
            connector = MCPServiceConnector(
                service_name=service_name,
                transport=transport,
                **kwargs
            )
            
            # Store the connector
            self._connectors[service_name] = connector
            logger.info(f"Registered MCP service: {service_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to register MCP service {service_name}: {str(e)}")
            return False
    
    async def unregister_service(self, service_name: str) -> bool:
        """
        Unregister MCP service
        
        Args:
            service_name: Service name
            
        Returns:
            Whether unregistration was successful
        """
        if service_name in self._connectors:
            try:
                # Disconnect from service if connected
                if self._connectors[service_name].is_connected:
                    await self._connectors[service_name].disconnect()
                
                # Remove the connector
                del self._connectors[service_name]
                logger.info(f"Unregistered MCP service: {service_name}")
                return True
            except Exception as e:
                logger.error(f"Failed to unregister MCP service {service_name}: {str(e)}")
        return False
    
    def get_service_connector(self, service_name: str) -> Optional[MCPServiceConnector]:
        """Get MCP service connector"""
        return self._connectors.get(service_name)
    
    def get_all_service_connectors(self) -> Dict[str, MCPServiceConnector]:
        """Get all MCP service connectors"""
        return self._connectors
    
    def get_service_names(self) -> List[str]:
        """Get all MCP service names"""
        return list(self._connectors.keys())
    
    def get_tool_by_name(self, tool_name: str) -> Optional[BaseTool]:
        """
        Get a tool by its name
        
        Args:
            tool_name: Name of the tool to get
            
        Returns:
            Tool if found, None otherwise
        """
        for connector in self._connectors.values():
            for tool in connector.tools:
                if tool.name == tool_name:
                    return tool
        return None
    
    def get_all_tools(self) -> List[BaseTool]:
        """
        Get all available tools from all services
        
        Returns:
            List of all available tools
        """
        tools = []
        for connector in self._connectors.values():
            tools.extend(connector.tools)
        return tools
    
    async def connect_all_services(self) -> Dict[str, bool]:
        """Connect to all registered MCP services"""
        results = {}
        for service_name, connector in self._connectors.items():
            try:
                if not connector.is_connected:
                    success = await connector.connect()
                    results[service_name] = success
                else:
                    results[service_name] = True
            except Exception as e:
                logger.error(f"Failed to connect to service {service_name}: {str(e)}")
                results[service_name] = False
        return results
    
    async def disconnect_all_services(self) -> Dict[str, bool]:
        """Disconnect from all MCP services"""
        results = {}
        for service_name, connector in self._connectors.items():
            try:
                if connector.is_connected:
                    success = await connector.disconnect()
                    results[service_name] = success
                else:
                    results[service_name] = True
            except Exception as e:
                logger.error(f"Failed to disconnect from service {service_name}: {str(e)}")
                results[service_name] = False
        return results
    
    async def load_services_from_config(self, config: Dict[str, Any]) -> List[str]:
        """
        Load services from configuration dictionary
        
        Args:
            config: Configuration dictionary containing service definitions
            
        Returns:
            List of successfully registered service names
        """
        success_services = []
        
        # Extract service configurations
        models_config = config.get("models", {})
        servers_config = config.get("servers", {})
        
        for model_name, model_info in models_config.items():
            server_name = model_info.get("server")
            if not server_name or server_name not in servers_config:
                logger.warning(f"Server {server_name} not found for model {model_name}")
                continue
                
            server_url = servers_config.get(server_name)
            if not server_url:
                logger.warning(f"Server URL not defined for {server_name}")
                continue
            
            # Get transport type from server config
            server_config = servers_config.get(server_name, {})
            transport = server_config.get("transport", "stdio")  # Default to stdio if not specified
            
            # Prepare connection parameters based on transport type
            kwargs = {}
            if transport == "sse":
                kwargs = {
                    "url": server_url,
                    "model": model_info.get("model", model_name)
                }
            elif transport == "stdio":
                kwargs = {
                    "command": server_config.get("command", "python"),
                    "args": server_config.get("args", [])
                }
            
            success = await self.register_service(
                service_name=model_name,
                transport=transport,
                **kwargs
            )
            
            if success:
                success_services.append(model_name)
        
        # Connect to services
        await self.connect_all_services()
        
        return success_services