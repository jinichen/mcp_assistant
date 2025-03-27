"""
NVIDIA AI Foundation model adapter
This module implements NVIDIA API specific request and response processing
"""
from typing import List, Dict, Any, Optional, AsyncGenerator
import time
import logging
import json
import traceback
import asyncio
import re

from langchain_nvidia_ai_endpoints import ChatNVIDIA
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from langchain_mcp_adapters.tools import load_mcp_tools
from langgraph.prebuilt import create_react_agent

from .base_adapter import ModelAdapter

logger = logging.getLogger(__name__)

class NVIDIAAdapter(ModelAdapter):
    """NVIDIA model adapter for NVIDIA AI Foundation API"""
    
    def __init__(self, api_key: str, api_base: str, model: str = "nvidia-llama-3"):
        """Initialize NVIDIA adapter
        
        Args:
            api_key: NVIDIA API key
            api_base: NVIDIA API base URL
            model: Default model name
        """
        self.api_key = api_key
        self.api_base = api_base
        self.model = model
        self.temperature = 0.7
        self.timeout = 120  # Request timeout in seconds
        logger.info(f"Initializing NVIDIA adapter, model: {model}")
    
    def _get_actual_model_name(self, model: str) -> str:
        """Get the actual model name
        
        Args:
            model: Input model name
            
        Returns:
            Actual model name to use
        """
        # Extract actual model name from model string
        actual_model = model
        if model.startswith("nvidia-"):
            actual_model = model[7:]  # Remove "nvidia-" prefix
        
        # Specific model name mappings
        model_mapping = {
            "deepseek": "deepseek-ai/deepseek-r1",
            "llama-3": "nvidia/llama-3.3-nemotron-super-49b-v1",
            "gemma-3": "google/gemma-3-27b-it",
            "mixtral": "mistralai/mixtral-8x22b-instruct-v0.1",
            "mistral": "mistralai/mistral-large-latest"
        }
        
        # If it's a specific model, use the mapped name
        if actual_model in model_mapping:
            mapped_model = model_mapping[actual_model]
            logger.info(f"Model name mapping: {model} -> {mapped_model}")
            return mapped_model
        
        return actual_model
    
    async def chat_completion(
        self, 
        messages: List[Dict[str, Any]], 
        tools: Optional[List[Dict[str, Any]]] = None, 
        tool_choice: str = "auto",
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Process NVIDIA chat completion request
        
        Args:
            messages: List of messages
            tools: Optional tool definitions
            tool_choice: Tool choice mode
            session_id: Session ID
        
        Returns:
            Standardized API response
        """
        try:
            start_time = time.time()
            actual_model = self._get_actual_model_name(self.model)
            logger.info(f"NVIDIA request started, model: {self.model}({actual_model}), session ID: {session_id or 'None'}")
            
            # Create NVIDIA client
            client = ChatNVIDIA(
                model=actual_model,
                nvidia_api_key=self.api_key,
                base_url=self.api_base,
                temperature=self.temperature,
                request_timeout=self.timeout
            )
            
            # Prepare request parameters
            kwargs = {
                "messages": messages,
            }
            
            # Add tools and tool choice (if provided)
            if tools and len(tools) > 0:
                kwargs["tools"] = tools
                kwargs["tool_choice"] = tool_choice
            
            # Send request
            response = await client.ainvoke(kwargs)
            
            # Process response
            end_time = time.time()
            logger.info(f"NVIDIA request completed, time taken: {end_time - start_time:.2f} seconds")
            
            # Extract required data from response
            completion_id = f"nvidia-{int(time.time() * 1000)}"
            
            # Build standardized response format
            standardized_response = {
                "id": completion_id,
                "timestamp": int(time.time()),
                "model": self.model,
                "choices": [
                    {
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": response.content
                        },
                        "finish_reason": "stop"
                    }
                ],
                "usage": {
                    "prompt_tokens": getattr(response, "usage", {}).get("prompt_tokens", 0),
                    "completion_tokens": getattr(response, "usage", {}).get("completion_tokens", 0),
                    "total_tokens": getattr(response, "usage", {}).get("total_tokens", 0)
                }
            }
            
            # Handle tool calls
            if hasattr(response, "tool_calls") and response.tool_calls:
                standardized_response["choices"][0]["message"]["tool_calls"] = response.tool_calls
                standardized_response["choices"][0]["finish_reason"] = "tool_calls"
            
            return standardized_response
            
        except Exception as e:
            end_time = time.time()
            logger.error(f"NVIDIA request failed, time taken: {end_time - start_time:.2f} seconds, error: {str(e)}")
            logger.error(traceback.format_exc())
            
            # Return error response
            return {
                "id": f"error-{int(time.time() * 1000)}",
                "timestamp": int(time.time()),
                "model": self.model,
                "choices": [
                    {
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": f"An error occurred while processing the request: {str(e)}"
                        },
                        "finish_reason": "error"
                    }
                ],
                "usage": {
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "total_tokens": 0
                },
                "error": str(e)
            }
    
    async def stream_chat_completion(
        self, 
        messages: List[Dict[str, Any]], 
        tools: Optional[List[Dict[str, Any]]] = None, 
        tool_choice: str = "auto",
        session_id: Optional[str] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Process NVIDIA streaming chat completion request
        
        Args:
            messages: List of messages
            tools: Optional tool definitions
            tool_choice: Tool choice mode
            session_id: Session ID
        
        Yields:
            Streaming response chunks
        """
        try:
            start_time = time.time()
            actual_model = self._get_actual_model_name(self.model)
            logger.info(f"NVIDIA streaming request started, model: {self.model}({actual_model}), session ID: {session_id or 'None'}")
            
            # Create NVIDIA client
            client = ChatNVIDIA(
                model=actual_model,
                nvidia_api_key=self.api_key,
                base_url=self.api_base,
                temperature=self.temperature,
                request_timeout=self.timeout,
                streaming=True
            )
            
            # Prepare request parameters
            kwargs = {
                "messages": messages,
            }
            
            # Add tools and tool choice (if provided)
            if tools and len(tools) > 0:
                kwargs["tools"] = tools
                kwargs["tool_choice"] = tool_choice
            
            # Send streaming request
            stream = await client.astream(kwargs)
            completion_id = f"nvidia-stream-{int(time.time() * 1000)}"
            cumulative_content = ""
            
            # Process streaming response
            async for chunk in stream:
                # Accumulate content
                if hasattr(chunk, "content") and chunk.content is not None:
                    content_delta = chunk.content
                    cumulative_content += content_delta
                else:
                    content_delta = ""
                
                # Construct streaming response chunk
                yield {
                    "id": completion_id,
                    "timestamp": int(time.time()),
                    "model": self.model,
                    "choices": [
                        {
                            "index": 0,
                            "delta": {
                                "role": "assistant",
                                "content": content_delta
                            },
                            "finish_reason": None
                        }
                    ]
                }
            
            # Send final streaming response
            yield {
                "id": completion_id,
                "timestamp": int(time.time()),
                "model": self.model,
                "choices": [
                    {
                        "index": 0,
                        "delta": {},
                        "finish_reason": "stop"
                    }
                ]
            }
            
            end_time = time.time()
            logger.info(f"NVIDIA streaming request completed, time taken: {end_time - start_time:.2f} seconds")
            
        except Exception as e:
            end_time = time.time()
            logger.error(f"NVIDIA streaming request failed, time taken: {end_time - start_time:.2f} seconds, error: {str(e)}")
            logger.error(traceback.format_exc())
            
            # Return error response
            yield {
                "id": f"error-{int(time.time() * 1000)}",
                "timestamp": int(time.time()),
                "model": self.model,
                "choices": [
                    {
                        "index": 0,
                        "delta": {
                            "role": "assistant",
                            "content": f"An error occurred while processing the request: {str(e)}"
                        },
                        "finish_reason": "error"
                    }
                ],
                "error": str(e)
            }
    
    async def process_mcp_request(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: str = "auto",
        session_id: Optional[str] = None,
        mcp_config: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Process MCP tool binding request, integrating NVIDIA models with MCP tools
        
        Args:
            messages: List of messages
            tools: Optional tool definitions
            tool_choice: Tool choice mode
            session_id: Session ID
            mcp_config: MCP configuration
        
        Returns:
            Standardized response
        """
        logger.info(f"NVIDIA MCP request started, model: {self.model}, session ID: {session_id or 'None'}")
        start_time = time.time()
        
        try:
            # Get actual model name
            actual_model = self._get_actual_model_name(self.model)
            
            # Create NVIDIA LLM client
            llm = ChatNVIDIA(
                model=actual_model,
                nvidia_api_key=self.api_key,
                base_url=self.api_base,
                temperature=self.temperature,
                request_timeout=self.timeout
            )
            
            # Get the last user message
            last_user_message = ""
            for msg in reversed(messages):
                if msg.get("role") == "user":
                    last_user_message = msg.get("content", "")
                    break
            
            # Get calculator configuration
            calculator_config = mcp_config.get("calculator", {})
            command = calculator_config.get("command", "python")
            args = calculator_config.get("args", [])
            
            logger.info(f"Connecting to calculator MCP service: {command} {' '.join(args)}")
            
            # Create server parameters
            server_params = StdioServerParameters(
                command=command,
                args=args
            )
            
            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    # Initialize connection
                    await session.initialize()
                    
                    # Get MCP tools
                    mcp_tools = await load_mcp_tools(session)
                    
                    # Output tool details
                    for i, tool in enumerate(mcp_tools):
                        logger.info(f"MCP tool {i+1}: name={tool.name}, description={tool.description}")
                        if hasattr(tool, 'args_schema'):
                            schema_fields = getattr(tool.args_schema, "__fields__", {})
                            logger.info(f"Tool parameters: {list(schema_fields.keys())}")
                    
                    logger.info(f"Loaded MCP tools: {len(mcp_tools)}")
                    
                    # Create Agent
                    agent = create_react_agent(llm, mcp_tools)
                    
                    # Call Agent to process the request
                    logger.info(f"Calling Agent to process request: {last_user_message[:50]}...")
                    agent_response = await agent.ainvoke({"messages": last_user_message})
                    
                    # Process response - extract the content of the last AI message
                    answer = ""
                    try:
                        # Convert to string, extract message list
                        response_str = str(agent_response)
                        
                        # If the response is a message list, look for the last AIMessage
                        if "messages" in response_str and "AIMessage" in response_str:
                            # Iterate to get all AIMessages
                            ai_messages = []
                            for line in response_str.split("AIMessage"):
                                if "content=" in line:
                                    content_match = re.search(r"content='([^']*)'", line)
                                    if content_match and content_match.group(1):
                                        content = content_match.group(1)
                                        if content:  # Only keep non-empty content
                                            # Remove content between <think> tags
                                            content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL).strip()
                                            if content:  # Ensure processed content is not empty
                                                ai_messages.append(content)
                            
                            # Get the last non-empty AI message
                            if ai_messages:
                                answer = ai_messages[-1]
                                logger.info(f"Extracted last AI message: {answer}")
                        
                        # If above method didn't get a result, try other methods
                        if not answer and hasattr(agent_response, "content") and agent_response.content:
                            content = agent_response.content
                            # Remove content between <think> tags
                            content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL).strip()
                            if content:
                                answer = content
                                logger.info(f"Got result from content attribute: {answer}")
                        elif not answer and hasattr(agent_response, "response") and hasattr(agent_response.response, "content"):
                            content = agent_response.response.content
                            # Remove content between <think> tags
                            content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL).strip()
                            if content:
                                answer = content
                                logger.info(f"Got result from response.content attribute: {answer}")
                        elif not answer:
                            # As a last resort, return a short prompt
                            logger.warning(f"Unable to extract AI message content, returning default message")
                            answer = "Unable to extract calculation result, please try again"
                    except Exception as extract_error:
                        logger.error(f"Error extracting Agent response content: {str(extract_error)}")
                        logger.error(traceback.format_exc())
                        answer = "Error processing response, please try again"
                    
                    end_time = time.time()
                    logger.info(f"NVIDIA MCP request completed, time taken: {end_time - start_time:.2f} seconds")
                    
                    # Build standard response format
                    return {
                        "id": f"nvidia-mcp-{int(time.time() * 1000)}",
                        "timestamp": int(time.time()),
                        "model": self.model,
                        "choices": [
                            {
                                "index": 0,
                                "message": {
                                    "role": "assistant",
                                    "content": answer
                                },
                                "finish_reason": "stop"
                            }
                        ],
                        "usage": {
                            "prompt_tokens": len(last_user_message.split()) * 1.3,
                            "completion_tokens": len(answer.split()) * 1.3,
                            "total_tokens": (len(last_user_message.split()) + len(answer.split())) * 1.3
                        }
                    }
            
        except Exception as e:
            end_time = time.time()
            logger.error(f"NVIDIA MCP request failed, time taken: {end_time - start_time:.2f} seconds, error: {str(e)}")
            logger.error(traceback.format_exc())
            
            # Return error response
            return {
                "id": f"error-{int(time.time() * 1000)}",
                "timestamp": int(time.time()),
                "model": self.model,
                "choices": [
                    {
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": f"Error processing MCP request: {str(e)}"
                        },
                        "finish_reason": "error"
                    }
                ],
                "usage": {
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "total_tokens": 0
                },
                "error": str(e)
            } 