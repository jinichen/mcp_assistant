import os
import json
import logging
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class MCPServiceConfig:
    """MCP service configuration management"""
    
    @staticmethod
    def load_from_file(file_path: str) -> Dict[str, Any]:
        """Load configuration from a JSON file"""
        try:
            with open(file_path, 'r') as f:
                config = json.load(f)
            logger.info(f"Loaded MCP service config from {file_path}")
            return config
        except Exception as e:
            logger.error(f"Failed to load MCP service config from {file_path}: {str(e)}")
            return {}
    
    @staticmethod
    def get_default_config_path() -> Optional[str]:
        """Get the default configuration file path"""
        # Try several possible locations
        possible_locations = [
            "./mcp_config.json",
            "./config/mcp_config.json",
            os.path.expanduser("~/.mcp/config.json"),
            "/etc/mcp/config.json"
        ]
        
        for location in possible_locations:
            if os.path.exists(location):
                return location
        
        return None
    
    @staticmethod
    def load_from_env() -> Dict[str, Any]:
        """Load configuration from environment variables"""
        config = {
            "servers": {},
            "models": {}
        }
        
        # Find all environment variables starting with MCP_SERVICE_
        mcp_vars = {k: v for k, v in os.environ.items() if k.startswith("MCP_SERVICE_")}
        
        for var_name, value in mcp_vars.items():
            # Get service name: MCP_SERVICE_NAME_CONFIG -> name
            if "_" not in var_name[12:]:
                continue
                
            service_name, config_key = var_name[12:].split("_", 1)
            service_name = service_name.lower()
            config_key = config_key.lower()
            
            # Ensure service configuration dictionary exists
            if service_name not in config["models"]:
                config["models"][service_name] = {}
            
            # Add configuration item
            config["models"][service_name][config_key] = value
            
            # Special case for server URLs
            if config_key == "server_url":
                server_name = service_name
                config["servers"][server_name] = value
                
                if "server" not in config["models"][service_name]:
                    config["models"][service_name]["server"] = server_name
        
        return config
    
    @staticmethod
    def load_config() -> Dict[str, Any]:
        """
        Load MCP service configuration from file and environment variables.
        Environment variables take precedence over file configuration.
        
        Returns:
            A dictionary containing MCP service configuration
        """
        config = {}
        
        # Try to load from default config file
        default_path = MCPServiceConfig.get_default_config_path()
        if default_path:
            config.update(MCPServiceConfig.load_from_file(default_path))
        
        # Load from environment variables (overrides file config)
        env_config = MCPServiceConfig.load_from_env()
        if env_config:
            MCPServiceConfig.deep_update(config, env_config)
        
        return config
    
    @staticmethod
    def deep_update(original: Dict[str, Any], update: Dict[str, Any]) -> Dict[str, Any]:
        """
        Recursively update a dictionary with another dictionary
        
        Args:
            original: Original dictionary to be updated
            update: Dictionary with values to update
            
        Returns:
            Updated dictionary
        """
        for key, value in update.items():
            if key in original and isinstance(original[key], dict) and isinstance(value, dict):
                MCPServiceConfig.deep_update(original[key], value)
            else:
                original[key] = value
        return original

# For backward compatibility
load_config_from_file = MCPServiceConfig.load_from_file
get_default_config_path = MCPServiceConfig.get_default_config_path
load_config_from_env = MCPServiceConfig.load_from_env
load_config = MCPServiceConfig.load_config
deep_update = MCPServiceConfig.deep_update