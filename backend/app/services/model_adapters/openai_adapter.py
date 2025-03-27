"""
OpenAI model adapter
This module implements OpenAI API specific request and response processing
"""
from typing import List, Dict, Any, Optional, AsyncGenerator, Union
import time
import logging
import json
import traceback
import asyncio
import re
import os

from langchain_openai import ChatOpenAI
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from langchain_mcp_adapters.tools import load_mcp_tools
from langgraph.prebuilt import create_react_agent
from openai import OpenAI, AsyncOpenAI
from langchain_core.messages import AIMessage

from .base_adapter import ModelAdapter

logger = logging.getLogger(__name__)

class OpenAIAdapter(ModelAdapter):
    """OpenAI model adapter for GPT models"""
    
    def __init__(self):
        """Initialize the OpenAI adapter with API key"""
        api_key = os.environ.get("OPENAI_API_KEY", "")
        if not api_key:
            logger.warning("OpenAI API key not found in environment variables")
        
        # Initialize OpenAI clients
        self.client = OpenAI(api_key=api_key)
        self.async_client = AsyncOpenAI(api_key=api_key)
    
    def chat_completion(self, 
                       messages: List[Dict[str, Any]], 
                       model: str,
                       tools: Optional[List[Dict[str, Any]]] = None,
                       tool_choice: Optional[Union[str, Dict[str, Any]]] = None,
                       session_id: Optional[str] = None,
                       **kwargs) -> Dict[str, Any]:
        """Process chat completion request using OpenAI API

        Args:
            messages: Chat history messages in the format of [{role: content}]
            model: OpenAI model name
            tools: Optional tools to use in the completion request
            tool_choice: Optional tool choice preference
            session_id: Optional session identifier
            **kwargs: Additional model-specific parameters

        Returns:
            Response dictionary with completion result
        """
        start_time = time.time()
        logger.info(f"Processing OpenAI chat completion request, model: {model}")
        
        try:
            # Prepare request parameters
            params = {
                "model": model,
                "messages": messages,
                "temperature": kwargs.get("temperature", 0.7),
                "top_p": kwargs.get("top_p", 0.95),
                "presence_penalty": kwargs.get("presence_penalty", 0),
                "frequency_penalty": kwargs.get("frequency_penalty", 0)
            }
            
            # Add max tokens if provided
            if "max_tokens" in kwargs:
                params["max_tokens"] = kwargs["max_tokens"]
                
            # Add tools if provided
            if tools:
                params["tools"] = tools
                if tool_choice:
                    params["tool_choice"] = tool_choice
            
            # Make API request
            response = self.client.chat.completions.create(**params)
            
            # Convert response to dict
            response_dict = self._response_to_dict(response)
            
            elapsed_time = time.time() - start_time
            logger.info(f"OpenAI chat completion completed in {elapsed_time:.2f}s")
            
            return response_dict
            
        except Exception as e:
            logger.error(f"OpenAI chat completion error: {str(e)}")
            elapsed_time = time.time() - start_time
            return {
                "error": True,
                "message": f"OpenAI API error: {str(e)}",
                "elapsed_time": elapsed_time
            }
    
    def stream_chat_completion(self, 
                              messages: List[Dict[str, Any]], 
                              model: str,
                              tools: Optional[List[Dict[str, Any]]] = None,
                              tool_choice: Optional[Union[str, Dict[str, Any]]] = None,
                              session_id: Optional[str] = None,
                              **kwargs) -> AsyncGenerator[Dict[str, Any], None]:
        """Process streaming chat completion request using OpenAI API

        Args:
            messages: Chat history messages in the format of [{role: content}]
            model: OpenAI model name
            tools: Optional tools to use in the completion request
            tool_choice: Optional tool choice preference
            session_id: Optional session identifier
            **kwargs: Additional model-specific parameters

        Returns:
            Generator yielding response chunks
        """
        start_time = time.time()
        logger.info(f"Processing OpenAI streaming chat completion, model: {model}")
        
        try:
            # Prepare request parameters
            params = {
                "model": model,
                "messages": messages,
                "temperature": kwargs.get("temperature", 0.7),
                "top_p": kwargs.get("top_p", 0.95),
                "presence_penalty": kwargs.get("presence_penalty", 0),
                "frequency_penalty": kwargs.get("frequency_penalty", 0),
                "stream": True
            }
            
            # Add max tokens if provided
            if "max_tokens" in kwargs:
                params["max_tokens"] = kwargs["max_tokens"]
                
            # Add tools if provided
            if tools:
                params["tools"] = tools
                if tool_choice:
                    params["tool_choice"] = tool_choice
            
            # Make streaming API request
            response_stream = self.client.chat.completions.create(**params)
            
            # Yield streaming chunks
            for chunk in response_stream:
                yield self._response_to_dict(chunk)
            
            elapsed_time = time.time() - start_time
            logger.info(f"OpenAI streaming chat completion completed in {elapsed_time:.2f}s")
            
        except Exception as e:
            logger.error(f"OpenAI streaming chat completion error: {str(e)}")
            elapsed_time = time.time() - start_time
            yield {
                "error": True,
                "message": f"OpenAI API error: {str(e)}",
                "elapsed_time": elapsed_time
            }
    
    def process_mcp_request(self,
                           messages: List[Dict[str, Any]],
                           model: str,
                           agent,
                           mcp_enabled_tools: List[Dict[str, Any]],
                           session_id: Optional[str] = None,
                           **kwargs) -> AIMessage:
        """Process a request using MCP tool with OpenAI API

        Args:
            messages: Chat history messages in the format of [{role: content}]
            model: OpenAI model name to use
            agent: MCP agent instance
            mcp_enabled_tools: List of MCP tools available
            session_id: Optional session identifier
            **kwargs: Additional model-specific parameters

        Returns:
            AIMessage with content from the language model
        """
        start_time = time.time()
        logger.info(f"Processing MCP request with OpenAI model: {model}, session: {session_id}")
        
        try:
            # Get LLM response through the MCP agent
            agent_response = agent.invoke(
                {"input": messages[-1]["content"]}
            )
            
            # Extract content from agent response
            content = None
            
            # Try to get content from various response formats
            if hasattr(agent_response, 'messages') and agent_response.messages:
                for message in agent_response.messages:
                    if hasattr(message, 'content') and message.content:
                        content = message.content
                        break
            
            # If no content found in messages, try to get it directly
            if not content and hasattr(agent_response, 'content'):
                content = agent_response.content
            
            # If still no content, try to get it from response attribute
            if not content and hasattr(agent_response, 'response') and hasattr(agent_response.response, 'content'):
                content = agent_response.response.content
            
            # Last resort: convert entire response to string
            if not content:
                content = str(agent_response)
            
            elapsed_time = time.time() - start_time
            logger.info(f"MCP request with OpenAI model completed in {elapsed_time:.2f}s")
            
            return AIMessage(content=content)
            
        except Exception as e:
            logger.error(f"MCP request with OpenAI model error: {str(e)}")
            return AIMessage(content=f"Error processing MCP request: {str(e)}")
    
    def _response_to_dict(self, response) -> Dict[str, Any]:
        """Convert OpenAI response object to dictionary
        
        Args:
            response: OpenAI API response object
            
        Returns:
            Dictionary representation of the response
        """
        # Use built-in model dict conversion if available
        if hasattr(response, "model_dump"):
            return response.model_dump()
        
        # Manual conversion for older OpenAI versions
        if hasattr(response, "__dict__"):
            return vars(response)
        
        # Fallback: convert to JSON and back to dict
        return json.loads(json.dumps(response, default=str)) 