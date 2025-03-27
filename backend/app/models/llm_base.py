from typing import Dict, Any, List, Optional, AsyncIterator
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

@dataclass
class ChatMessage:
    role: str
    content: str
    name: Optional[str] = None

@dataclass
class ModelParameters:
    temperature: float = 0.7
    top_p: float = 1.0
    max_tokens: Optional[int] = None
    stream: bool = False
    
    def copy(self):
        return ModelParameters(
            temperature=self.temperature,
            top_p=self.top_p,
            max_tokens=self.max_tokens,
            stream=self.stream
        )

class LLMBase(ABC):
    """Base LLM interface, all model adapters must implement this"""
    
    @abstractmethod
    async def generate(self, 
                      messages: List[ChatMessage], 
                      parameters: ModelParameters = ModelParameters()) -> str:
        """Generate text response"""
        pass
    
    @abstractmethod
    async def generate_stream(self, 
                             messages: List[ChatMessage], 
                             parameters: ModelParameters = ModelParameters()) -> AsyncIterator[str]:
        """Generate streaming text response"""
        pass
    
    @property
    @abstractmethod
    def available_models(self) -> List[str]:
        """Return available models list"""
        pass
    
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return provider name"""
        pass