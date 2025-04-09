from typing import List, Dict, Any, Optional
import os
from langchain.callbacks.base import BaseCallbackHandler
from langchain.schema import HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_nvidia_ai_endpoints import ChatNVIDIA

from app.core.config import get_app_settings

settings = get_app_settings()

# Setup LangChain tracing if API key is provided
if settings.LANGCHAIN_API_KEY:
    os.environ["LANGCHAIN_API_KEY"] = settings.LANGCHAIN_API_KEY
    
    if settings.LANGCHAIN_ENDPOINT:
        os.environ["LANGCHAIN_ENDPOINT"] = settings.LANGCHAIN_ENDPOINT
    
    if settings.LANGCHAIN_PROJECT:
        os.environ["LANGCHAIN_PROJECT"] = settings.LANGCHAIN_PROJECT
    
    if settings.LANGCHAIN_TRACING_V2:
        os.environ["LANGCHAIN_TRACING_V2"] = settings.LANGCHAIN_TRACING_V2

class LLMService:
    """Service to handle interactions with various LLM providers."""
    
    @staticmethod
    def get_provider(provider_name: Optional[str] = None, model_name: Optional[str] = None):
        """Factory method to get LLM provider."""
        
        provider_name = provider_name or settings.DEFAULT_LLM_PROVIDER
        
        if provider_name == "openai":
            if not settings.OPENAI_API_KEY:
                raise ValueError("OpenAI API key is not set")
            
            model = model_name or settings.DEFAULT_OPENAI_MODEL
            return ChatOpenAI(
                api_key=settings.OPENAI_API_KEY,
                base_url=settings.OPENAI_BASE_URL,
                model=model,
                temperature=0.7,
            )
            
        elif provider_name == "google":
            if not settings.GOOGLE_API_KEY:
                raise ValueError("Google API key is not set")
                
            model = model_name or "gemini-1.5-pro"
            return ChatGoogleGenerativeAI(
                api_key=settings.GOOGLE_API_KEY,
                model=model,
                temperature=0.7,
            )
            
        elif provider_name == "anthropic":
            if not settings.ANTHROPIC_API_KEY:
                raise ValueError("Anthropic API key is not set")
                
            model = model_name or settings.DEFAULT_ANTHROPIC_MODEL
            return ChatAnthropic(
                api_key=settings.ANTHROPIC_API_KEY,
                model=model,
                temperature=0.7,
            )
            
        elif provider_name == "nvidia":
            if not settings.NVIDIA_API_KEY:
                raise ValueError("NVIDIA API key is not set")
                
            model = model_name or settings.DEFAULT_NVIDIA_MODEL
            return ChatNVIDIA(
                api_key=settings.NVIDIA_API_KEY,
                model=model,
                base_url=settings.NVIDIA_BASE_URL,
                temperature=0.7,
            )
            
        else:
            if not settings.OPENAI_API_KEY:
                raise ValueError("OpenAI API key is not set and no valid provider specified")
                
            print(f"Unsupported provider '{provider_name}', falling back to OpenAI")
            return ChatOpenAI(
                api_key=settings.OPENAI_API_KEY,
                base_url=settings.OPENAI_BASE_URL,
                model=settings.DEFAULT_OPENAI_MODEL,
                temperature=0.7,
            )
    
    @staticmethod
    async def generate_response(
        messages: List[Dict[str, str]],
        provider: Optional[str] = None,
        model: Optional[str] = None,
        callbacks: Optional[List[BaseCallbackHandler]] = None
    ) -> str:
        """Generate a response from the LLM provider."""
        
        llm = LLMService.get_provider(provider, model)
        
        # Convert to LangChain messages format
        lc_messages = []
        for msg in messages:
            if msg["role"] == "user":
                lc_messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                lc_messages.append(AIMessage(content=msg["content"]))
            elif msg["role"] == "system":
                lc_messages.append(SystemMessage(content=msg["content"]))
        
        # Add debug logs
        print(f"Provider: {provider}, Model: {model}")
        print(f"Messages: {lc_messages}")
        
        try:
            response = await llm.ainvoke(lc_messages)
            return response.content
        except Exception as e:
            print(f"Error calling LLM: {str(e)}")
            raise 