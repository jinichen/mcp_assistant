import os
import json
import logging
from typing import List, Optional, Dict, Any
from pathlib import Path
from app.mcp_adapters.manager import MCPServiceManager
from app.mcp_adapters.client import MCPClient

# MCP client singleton
mcp_client = None

logger = logging.getLogger(__name__)

async def initialize_mcp_services(config_file: Optional[str] = None) -> List[str]:
    """
    Initialize MCP services
    
    Args:
        config_file: Configuration file path, if None use default configuration
        
    Returns:
        List of successfully registered service names
    """
    # Load configuration
    config = None
    
    try:
        # Load from specified configuration file
        if config_file:
            with open(config_file, 'r') as f:
                config = json.load(f)
        else:
            # Try to load from default path
            default_path = os.getenv("MCP_CONFIG_PATH", "./config/mcp_config.json")
            if os.path.exists(default_path):
                with open(default_path, 'r') as f:
                    config = json.load(f)
            else:
                # Load configuration from environment variables
                logger.warning("No MCP configuration file found, using environment variables")
    except Exception as e:
        logger.error(f"Error loading MCP configuration: {str(e)}")
        return []
    
    # Initialize MCP client
    manager = MCPServiceManager()
    
    # Register services from configuration
    if config:
        await manager.load_services_from_config(config)
    
    return manager.get_service_names()

# Async function for automatic initialization
async def auto_initialize_mcp():
    """Automatically initialize MCP services on application startup"""
    try:
        services = await initialize_mcp_services()
        if services:
            logger.info(f"Initialized MCP services: {services}")
        else:
            logger.warning("No MCP services initialized")
    except Exception as e:
        logger.error(f"Error initializing MCP services: {str(e)}")

# Get MCP tools
async def get_mcp_tools():
    """Get all available MCP tools"""
    manager = MCPServiceManager()
    return manager.get_all_tools()