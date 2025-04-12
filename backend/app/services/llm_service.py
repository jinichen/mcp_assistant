from typing import List, Dict, Any, Optional
import os
import traceback
import json
import asyncio
from functools import lru_cache
from dotenv import load_dotenv

# Langchain imports
from langchain.callbacks.base import BaseCallbackHandler
from langchain.schema import HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_nvidia_ai_endpoints import ChatNVIDIA

# Load environment variables from .env file
load_dotenv()

# Defer LangChain tracing setup to when it's actually needed
def setup_langchain_tracing():
    """Setup LangChain tracing if API key is provided."""
    if not hasattr(setup_langchain_tracing, "initialized"):
        langchain_api_key = os.getenv("LANGCHAIN_API_KEY")
        if langchain_api_key:
            os.environ["LANGCHAIN_API_KEY"] = langchain_api_key
            
            langchain_endpoint = os.getenv("LANGCHAIN_ENDPOINT")
            if langchain_endpoint:
                os.environ["LANGCHAIN_ENDPOINT"] = langchain_endpoint
            
            langchain_project = os.getenv("LANGCHAIN_PROJECT")
            if langchain_project:
                os.environ["LANGCHAIN_PROJECT"] = langchain_project
            
            langchain_tracing_v2 = os.getenv("LANGCHAIN_TRACING_V2")
            if langchain_tracing_v2:
                os.environ["LANGCHAIN_TRACING_V2"] = langchain_tracing_v2
        
        setup_langchain_tracing.initialized = True

class LLMService:
    """Service to handle interactions with various LLM providers."""
    
    @staticmethod
    @lru_cache(maxsize=None)
    def get_provider(provider_name: Optional[str] = None, model_name: Optional[str] = None, streaming: bool = False):
        """Factory method to get LLM provider with caching."""
        try:
            setup_langchain_tracing()
            
            provider_name = provider_name or os.getenv("DEFAULT_LLM_PROVIDER", "openai")
            
            # Try the requested provider first
            try:
                return LLMService._create_provider(provider_name, model_name, streaming)
            except Exception as e:
                print(f"Error initializing {provider_name} provider: {str(e)}")
                print(f"Traceback: {traceback.format_exc()}")
                
                # If the requested provider fails, try fallback providers
                fallback_providers = ["openai", "google", "anthropic", "nvidia"]
                for fallback in fallback_providers:
                    if fallback != provider_name:
                        try:
                            print(f"Trying fallback provider: {fallback}")
                            return LLMService._create_provider(fallback, None, streaming)
                        except Exception as fallback_e:
                            print(f"Fallback to {fallback} failed: {str(fallback_e)}")
                            continue
                
                # If all providers fail, raise the original error
                raise
        except Exception as e:
            print(f"Fatal error in get_provider: {str(e)}")
            print(f"Traceback: {traceback.format_exc()}")
            raise
    
    @staticmethod
    def _create_provider(provider_name: str, model_name: Optional[str] = None, streaming: bool = False):
        """Internal method to create a specific provider instance."""
        # Get temperature from environment variable or use default
        temperature = float(os.getenv("LLM_TEMPERATURE", "0.7"))
        
        # Get timeout from environment variable or use default
        timeout = int(os.getenv("LLM_REQUEST_TIMEOUT", "60"))
        
        if provider_name == "openai":
            openai_api_key = os.getenv("OPENAI_API_KEY")
            if not openai_api_key:
                raise ValueError("OpenAI API key is not set")
            
            model = model_name or os.getenv("DEFAULT_OPENAI_MODEL", "gpt-3.5-turbo")
            openai_base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
            
            print(f"Initializing OpenAI client with base_url: {openai_base_url}")
            print(f"Model: {model}")
            print(f"Streaming: {streaming}")
            
            return ChatOpenAI(
                api_key=openai_api_key,
                base_url=openai_base_url,
                model=model,
                temperature=temperature,
                streaming=streaming,
                request_timeout=timeout,
            )
            
        elif provider_name == "google":
            google_api_key = os.getenv("GOOGLE_API_KEY")
            if not google_api_key:
                raise ValueError("Google API key is not set")
                
            model = model_name or os.getenv("DEFAULT_GOOGLE_MODEL", "gemini-pro")
            if model.startswith("models/"):
                model = model[7:]
                
            return ChatGoogleGenerativeAI(
                api_key=google_api_key,
                model=model,
                temperature=temperature,
                streaming=streaming,
                request_timeout=timeout,
            )
            
        elif provider_name == "anthropic":
            anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
            if not anthropic_api_key:
                raise ValueError("Anthropic API key is not set")
                
            model = model_name or os.getenv("DEFAULT_ANTHROPIC_MODEL", "claude-3-opus-20240229")
            return ChatAnthropic(
                api_key=anthropic_api_key,
                model=model,
                temperature=temperature,
                streaming=streaming,
                request_timeout=timeout,
            )
            
        elif provider_name == "nvidia":
            nvidia_api_key = os.getenv("NVIDIA_API_KEY")
            if not nvidia_api_key:
                raise ValueError("NVIDIA API key is not set")
                
            model = model_name or os.getenv("DEFAULT_NVIDIA_MODEL", "mixtral_8x7b")
            nvidia_base_url = os.getenv("NVIDIA_BASE_URL", "https://api.nvidia.com/v1")
            
            return ChatNVIDIA(
                api_key=nvidia_api_key,
                model=model,
                base_url=nvidia_base_url,
                temperature=temperature,
                streaming=streaming,
                request_timeout=timeout,
            )
            
        else:
            raise ValueError(f"Unsupported provider: {provider_name}")
    
    @staticmethod
    async def generate_response(
        messages: List,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        callbacks: Optional[List[BaseCallbackHandler]] = None
    ) -> str:
        """Generate a response from the LLM provider."""
        
        try:
            llm = LLMService.get_provider(provider, model)
            
            # Convert to LangChain messages format
            lc_messages = LLMService._convert_to_langchain_messages(messages)
            
            try:
                response = await llm.ainvoke(lc_messages)
                return response.content
            except Exception as e:
                print(f"Error calling LLM: {str(e)}")
                print(f"Traceback: {traceback.format_exc()}")
                
                # Try fallback if available
                if provider:
                    try:
                        print("Attempting fallback to default provider")
                        llm = LLMService.get_provider(None, None)  # Use default provider
                        response = await llm.ainvoke(lc_messages)
                        return response.content
                    except Exception as fallback_e:
                        print(f"Fallback failed: {str(fallback_e)}")
                        raise e
                else:
                    raise
        except Exception as e:
            print(f"Error in generate_response: {str(e)}")
            print(f"Traceback: {traceback.format_exc()}")
            raise
    
    @staticmethod
    def _convert_to_langchain_messages(messages):
        """Convert messages to LangChain format."""
        lc_messages = []
        
        for message in messages:
            if isinstance(message, dict):
                if message.get("role") == "system":
                    lc_messages.append(SystemMessage(content=message["content"]))
                elif message.get("role") == "user":
                    lc_messages.append(HumanMessage(content=message["content"]))
                elif message.get("role") == "assistant":
                    lc_messages.append(AIMessage(content=message["content"]))
                else:
                    # Default to user message if role is unknown
                    lc_messages.append(HumanMessage(content=message.get("content", "")))
            elif isinstance(message, (HumanMessage, SystemMessage, AIMessage)):
                lc_messages.append(message)
            else:
                # If it's a string or other type, treat as user message
                lc_messages.append(HumanMessage(content=str(message)))
        
        return lc_messages
    
    @staticmethod
    async def generate_from_prompt(prompt: str, provider: Optional[str] = None, model: Optional[str] = None):
        """Generate content from a single prompt."""
        messages = [{"role": "user", "content": prompt}]
        return await LLMService.generate_response(messages, provider, model) 