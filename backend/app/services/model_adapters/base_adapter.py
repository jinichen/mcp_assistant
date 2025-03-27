"""
Base model adapter interface
This module defines the base interface that all model adapters must implement
"""
from typing import List, Dict, Any, Optional, AsyncGenerator, Generator, Union
from abc import ABC, abstractmethod

from langchain_core.messages import AIMessage

class ModelAdapter(ABC):
    """Base model adapter interface"""
    
    @abstractmethod
    async def chat_completion(
        self, 
        messages: List[Dict[str, Any]], 
        model: str,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[Union[str, Dict[str, Any]]] = None,
        session_id: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Process chat completion request

        Args:
            messages: Chat history messages in the format of [{role: content}]
            model: Model name
            tools: Optional tools to use in the completion request
            tool_choice: Optional tool choice preference
            session_id: Optional session identifier
            **kwargs: Additional model-specific parameters

        Returns:
            Response dictionary with completion result
        """
        pass
    
    @abstractmethod
    async def stream_chat_completion(
        self, 
        messages: List[Dict[str, Any]], 
        model: str,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[Union[str, Dict[str, Any]]] = None,
        session_id: Optional[str] = None,
        **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Process streaming chat completion request

        Args:
            messages: Chat history messages in the format of [{role: content}]
            model: Model name
            tools: Optional tools to use in the completion request
            tool_choice: Optional tool choice preference
            session_id: Optional session identifier
            **kwargs: Additional model-specific parameters

        Returns:
            Generator yielding response chunks
        """
        pass
    
    @abstractmethod
    async def process_mcp_request(
        self,
        messages: List[Dict[str, Any]],
        model: str,
        agent,
        mcp_enabled_tools: List[Dict[str, Any]],
        session_id: Optional[str] = None,
        **kwargs
    ) -> AIMessage:
        """Process a request using MCP tool

        Args:
            messages: Chat history messages in the format of [{role: content}]
            model: Model name to use
            agent: MCP agent instance
            mcp_enabled_tools: List of MCP tools available
            session_id: Optional session identifier
            **kwargs: Additional model-specific parameters

        Returns:
            AIMessage with content from the language model
        """
        pass 