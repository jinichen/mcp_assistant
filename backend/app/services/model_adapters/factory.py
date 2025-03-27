"""
Model adapter factory
This module helps select the appropriate adapter for a given model
"""
import os
import logging
from typing import Dict, Type

from .base_adapter import ModelAdapter
from .openai_adapter import OpenAIAdapter
from .google_adapter import GoogleAdapter
from .nvidia_adapter import NvidiaAdapter

logger = logging.getLogger(__name__)

class ModelAdapterFactory:
    """Factory class for creating model adapters"""
    
    _adapters: Dict[str, Type[ModelAdapter]] = {}
    
    @classmethod
    def register(cls, prefix: str, adapter_class: Type[ModelAdapter]) -> None:
        """Register an adapter for a model prefix
        
        Args:
            prefix: Model name prefix (e.g., "gpt-" for OpenAI models)
            adapter_class: Adapter class to handle this model type
        """
        cls._adapters[prefix] = adapter_class
        logger.debug(f"Registered adapter {adapter_class.__name__} for prefix '{prefix}'")
    
    @classmethod
    def create(cls, model: str) -> ModelAdapter:
        """Create an appropriate adapter instance for the given model
        
        Args:
            model: Model name (e.g., "gpt-4", "gemini-pro", etc.)
            
        Returns:
            An instance of the appropriate model adapter
            
        Raises:
            ValueError: If no adapter is registered for the model
        """
        # Find the matching adapter based on model name prefix
        for prefix, adapter_class in cls._adapters.items():
            if model.startswith(prefix):
                logger.debug(f"Using {adapter_class.__name__} for model '{model}'")
                return adapter_class()
        
        # If no adapter found, raise error
        raise ValueError(f"No adapter registered for model '{model}'")


# Register standard adapters
ModelAdapterFactory.register("gpt-", OpenAIAdapter)  # For OpenAI models
ModelAdapterFactory.register("gemini-", GoogleAdapter)  # For Google models
ModelAdapterFactory.register("claude-", OpenAIAdapter)  # For Anthropic models (via OpenAI API)
ModelAdapterFactory.register("deepseek-", NvidiaAdapter)  # For NVIDIA models

# Register adapter types
ModelAdapterFactory.register_adapter("openai", OpenAIAdapter)
ModelAdapterFactory.register_adapter("google", GoogleAdapter)
ModelAdapterFactory.register_adapter("nvidia", NVIDIAAdapter) 