import os
from typing import Dict, List, Optional, Type, Any
from dotenv import load_dotenv

# Import for type annotations (avoid circular imports)
if False:
    from .llm_base import LLMBase
    from .google_model import GoogleModel
    from .nvidia_model import NVIDIAModel
    from .openai_model import OpenAIModel
    from .anthropic_model import AnthropicModel
    # These will be implemented later

# Load environment variables
load_dotenv()

def get_models_from_env(provider: str) -> List[str]:
    """
    Get available models for a provider from environment variables
    
    Format: PROVIDER_MODELS=model1,model2,model3
    Example: GOOGLE_MODELS=gemini-1.5-pro,gemini-2.5-pro-exp-03-25
    """
    env_var = f"{provider.upper()}_MODELS"
    models_str = os.getenv(env_var, "")
    
    if not models_str:
        return []  # Return empty list if environment variable not set
    
    # Split by comma and strip whitespace
    return [model.strip() for model in models_str.split(",") if model.strip()]

class ModelFactory:
    """LLM model factory, responsible for creating and managing model instances from different providers"""
    
    _instance = None  # Singleton pattern
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def __init__(self):
        from .google_model import GoogleModel
        from .nvidia_model import NVIDIAModel
        from .openai_model import OpenAIModel
        from .anthropic_model import AnthropicModel
        
        # Dictionary to store model classes and instances
        self.model_classes = {
            "google": GoogleModel,
            "nvidia": NVIDIAModel,
            "openai": OpenAIModel,
            "anthropic": AnthropicModel
        }
        
        self.default_models = {
            "google": "gemini-1.5-pro",
            "nvidia": "mixtral-8x7b-instruct",
            "openai": "gpt-3.5-turbo",
            "anthropic": "claude-3-sonnet-20240229"
        }
        
        self.model_instances = {}
        self.default_provider = os.getenv("DEFAULT_PROVIDER", "google")
    
    def get_provider_models(self, provider: str) -> List[str]:
        """Get available models for a provider"""
        if provider in self.model_classes:
            model_class = self.model_classes[provider]
            return model_class.get_available_models()
        return []
    
    def get_all_providers(self) -> List[str]:
        """Get all available providers"""
        return list(self.model_classes.keys())
    
    def get_all_models(self) -> Dict[str, List[str]]:
        """Get all available models grouped by provider"""
        result = {}
        for provider in self.get_all_providers():
            result[provider] = self.get_provider_models(provider)
        return result
    
    def get_model_instance(self, provider: str, model_name: Optional[str] = None) -> Any:
        """Get or create a model instance for a specific provider and model"""
        if provider not in self.model_classes:
            raise ValueError(f"Unknown provider: {provider}")
        
        model_name = model_name or self.default_models.get(provider)
        
        # Create a key for the model instance cache
        instance_key = f"{provider}:{model_name}"
        
        # Return cached instance if available
        if instance_key in self.model_instances:
            return self.model_instances[instance_key]
        
        # Create new instance
        model_class = self.model_classes[provider]
        instance = model_class(model_name=model_name)
        
        # Cache the instance
        self.model_instances[instance_key] = instance
        
        return instance
    
    def get_default_model(self) -> Any:
        """Get the default model instance"""
        return self.get_model_instance(self.default_provider)