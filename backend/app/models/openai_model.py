import os
from typing import Dict, Any, List, Optional, Union, AsyncIterator
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.outputs import ChatGenerationChunk
from .llm_base import LLMBase, ChatMessage, ModelParameters
from .model_factory import get_models_from_env

# Load environment variables
load_dotenv()

class OpenAIModel(LLMBase):
    """OpenAI model adapter"""
    
    def __init__(self, model_name: str = "gpt-3.5-turbo"):
        self.model_name = model_name
        self.api_key = os.getenv("OPENAI_API_KEY")
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
    ) -> AsyncIterator[Dict[str, Any]]:
        """Generate streaming text response"""
        # Ensure streaming parameter is True
        self.llm.streaming = True
        
        langchain_messages = self._convert_to_langchain_messages(messages)
        
        async for chunk in self.llm.astream(langchain_messages):
            yield {
                "content": chunk.content,
                "model": self.model_name
            }
    
    def _create_llm(self) -> ChatOpenAI:
        """Create LangChain ChatOpenAI model"""
        if not self.api_key:
            raise ValueError("OpenAI API key not found. Please set OPENAI_API_KEY environment variable.")
        
        return ChatOpenAI(
            model=self.model_name,
            openai_api_key=self.api_key,
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
        env_models = get_models_from_env("openai")
        if env_models:
            return env_models
            
        # Fallback to hardcoded list
        return [
            "gpt-4-turbo-preview",
            "gpt-4",
            "gpt-4-32k",
            "gpt-3.5-turbo",
            "gpt-3.5-turbo-16k",
        ]
    
    @staticmethod
    def get_provider() -> str:
        """Return provider name"""
        return "openai"