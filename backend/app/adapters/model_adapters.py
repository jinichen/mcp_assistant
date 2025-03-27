"""Model adapters, handling differences between various models."""

from typing import Dict, Any, List, Optional
from langchain.tools import BaseTool
import copy
import logging
import re

logger = logging.getLogger(__name__)

class ToolNameAdapter:
    """Adapt tool names for different models"""
    
    @staticmethod
    def adapt_tool_name(tool_name: str, model_type: str) -> str:
        """Adjust tool name based on model type"""
        if model_type.startswith("gpt-"):
            # OpenAI needs to replace periods
            adapted_name = tool_name.replace(".", "_")
            logger.debug(f"Adapted tool name for {model_type}: {tool_name} -> {adapted_name}")
            return adapted_name
        # Other models keep the original name
        return tool_name
    
    @staticmethod
    def restore_tool_name(adapted_name: str) -> str:
        """Restore adapted name to original name"""
        original_name = adapted_name.replace("_", ".")
        logger.debug(f"Restored tool name: {adapted_name} -> {original_name}")
        return original_name

    @staticmethod
    def adapt_tools(tools: List[BaseTool], model_type: str) -> List[BaseTool]:
        """Adjust tool list for specific models"""
        adapted_tools = []
        
        for tool in tools:
            # Create a copy of the tool
            adapted_tool = copy.deepcopy(tool)
            
            # Adapt tool name
            original_name = tool.name
            adapted_name = ToolNameAdapter.adapt_tool_name(original_name, model_type)
            adapted_tool.name = adapted_name
            
            adapted_tools.append(adapted_tool)
            
        logger.info(f"Adapted {len(tools)} tools for model {model_type}")
        return adapted_tools

def adapt_tool_names(tools: List[Dict[str, Any]], model: str) -> List[Dict[str, Any]]:
    """Adapt tool names for different models"""
    adapted_tools = []
    
    for tool in tools:
        tool_copy = tool.copy()
        tool_copy['name'] = adapt_name_for_model(tool['name'], model)
        adapted_tools.append(tool_copy)
    
    return adapted_tools

def adapt_name_for_model(name: str, model: str) -> str:
    """Adjust tool name based on model type"""
    if model.startswith("gpt"):
        # OpenAI needs to replace periods
        return name.replace(".", "_")
    else:
        # Other models keep the original name
        return name

def revert_adapted_name(adapted_name: str, original_name: str) -> str:
    """Restore adapted name to original name"""
    # This simple implementation works for the current adaptation logic
    # If adaptation logic becomes more complex, this function needs to be updated
    return original_name

def adapt_tools_for_model(tools: List[Dict[str, Any]], model: str) -> List[Dict[str, Any]]:
    """Adjust tool list for specific models"""
    if not tools:
        return []
    
    # Create a copy of tools
    adapted_tools = []
    
    for tool in tools:
        # Adapt tool names
        tool_copy = tool.copy()
        tool_copy['name'] = adapt_name_for_model(tool['name'], model)
        adapted_tools.append(tool_copy)
    
    return adapted_tools