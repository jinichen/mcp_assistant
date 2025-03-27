import os
from typing import List, Dict, Any, AsyncGenerator, Optional, Union
from langchain_anthropic import ChatAnthropic
from langchain.schema import HumanMessage, AIMessage, SystemMessage
from dotenv import load_dotenv
from .model_factory import get_models_from_env

# Load environment variables
load_dotenv()

class AnthropicModel:
    """Anthropic Claude model adapter"""
    
    def __init__(self, model_name: str = "claude-3-opus-20240229"):
        self.model_name = model_name
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        self.llm = self._create_llm()
        
    async def generate(
        self, 
        messages: List[Dict[str, Any]], 
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        """Generate text response"""
        langchain_messages = self._convert_to_langchain_messages(messages)
        response = await self.llm.ainvoke(langchain_messages)
        return {
            "content": response.content,
            "model": self.model_name
        }
    
    async def astream(
        self, 
        messages: List[Dict[str, Any]], 
        temperature: float = 0.7,
        stream: bool = True
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Generate streaming text response"""
        # Ensure streaming parameter is True
        self.llm.streaming = True
        
        langchain_messages = self._convert_to_langchain_messages(messages)
        
        async for chunk in self.llm.astream(langchain_messages):
            yield {
                "content": chunk.content,
                "model": self.model_name
            }
    
    def _create_llm(self) -> ChatAnthropic:
        """Create LangChain ChatAnthropic model"""
        if not self.api_key:
            raise ValueError("Anthropic API key not found. Please set ANTHROPIC_API_KEY environment variable.")
        
        return ChatAnthropic(
            model=self.model_name,
            anthropic_api_key=self.api_key,
            temperature=0.7
        )
    
    def _convert_to_langchain_messages(self, messages: List[Dict[str, Any]]) -> List[Union[HumanMessage, AIMessage, SystemMessage]]:
        """Convert internal message format to LangChain message format"""
        langchain_messages = []
        
        for message in messages:
            role = message["role"]
            content = message.get("content", "")
            
            if role == "user":
                langchain_messages.append(HumanMessage(content=content))
            elif role == "assistant":
                langchain_messages.append(AIMessage(content=content))
            elif role == "system":
                langchain_messages.append(SystemMessage(content=content))
        
        return langchain_messages
    
    @staticmethod
    def get_available_models() -> List[str]:
        """Return list of available models"""
        # Try to get models from environment variable first
        env_models = get_models_from_env("anthropic")
        if env_models:
            return env_models
            
        # Fallback to hardcoded list
        return ["claude-3-opus-20240229", "claude-3-sonnet-20240229", "claude-3-haiku-20240307"]
    
    @staticmethod
    def get_provider() -> str:
        """Return provider name"""
        return "anthropic"