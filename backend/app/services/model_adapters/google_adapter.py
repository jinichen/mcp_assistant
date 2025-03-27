"""
Google Gemini model adapter
This module implements Google Gemini API specific request and response processing
"""
from typing import List, Dict, Any, Optional, AsyncGenerator
import time
import logging
import json
import traceback
import asyncio
import re

from langchain_google_genai import ChatGoogleGenerativeAI
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from langchain_mcp_adapters.tools import load_mcp_tools
from langgraph.prebuilt import create_react_agent

from .base_adapter import ModelAdapter

logger = logging.getLogger(__name__)

class GoogleAdapter(ModelAdapter):
    """Google model adapter for Gemini API request and response processing"""
    
    def __init__(self, api_key: str, api_base: str = None, model: str = "gemini-1.0-pro"):
        """Initialize Google adapter
        
        Args:
            api_key: Google API key
            api_base: Google API base URL
            model: Default model name
        """
        self.api_key = api_key
        self.api_base = api_base
        self.model = model
        self.timeout = 120  # Request timeout in seconds
        logger.info(f"Initializing Google adapter, model: {model}")
    
    async def chat_completion(
        self, 
        messages: List[Dict[str, Any]], 
        tools: Optional[List[Dict[str, Any]]] = None, 
        tool_choice: str = "auto",
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Process Google chat completion request
        
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
            logger.info(f"Google request started, model: {self.model}, session ID: {session_id or 'None'}")
            
            # Create Google client
            genai_client = genai.GenerativeModel(
                model_name=self.model
            )
            
            # Convert messages to Google format
            google_messages = []
            for msg in messages:
                role = msg.get("role")
                if role == "user":
                    google_role = "user"
                elif role == "assistant":
                    google_role = "model"
                elif role == "system":
                    google_role = "user"
                    # Add system indicator for system messages
                    msg["content"] = "SYSTEM: " + msg.get("content", "")
                else:
                    # Skip unsupported roles
                    logger.warning(f"Skipping unsupported role: {role}")
                    continue
                
                google_messages.append({
                    "role": google_role,
                    "parts": [{"text": msg.get("content", "")}]
                })
            
            # Start Google chat session
            chat = genai_client.start_chat(history=google_messages)
            
            # Prepare tools if provided
            generation_config = None
            if tools and len(tools) > 0:
                logger.info(f"Adding tools to request, count: {len(tools)}")
                
                # Convert OpenAI tools format to Google format
                tool_config = []
                for tool in tools:
                    google_tool = {
                        "function_declarations": []
                    }
                    
                    # Convert function definitions
                    function_data = tool.get("function", {})
                    function_name = function_data.get("name", "")
                    function_desc = function_data.get("description", "")
                    function_params = function_data.get("parameters", {})
                    
                    google_function = {
                        "name": function_name,
                        "description": function_desc,
                        "parameters": function_params
                    }
                    
                    google_tool["function_declarations"].append(google_function)
                    tool_config.append(google_tool)
                
                generation_config = {
                    "tools": tool_config
                }
            
            # Send request
            response = chat.send_message(
                "", 
                generation_config=generation_config
            )
            
            # Process response
            end_time = time.time()
            logger.info(f"Google request completed, time taken: {end_time - start_time:.2f} seconds")
            
            # Build standardized response format
            content = response.text
            completion_id = f"google-{int(time.time() * 1000)}"
            
            # Default response format
            standardized_response = {
                "id": completion_id,
                "timestamp": int(time.time()),
                "model": self.model,
                "choices": [
                    {
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": content
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
            
            # Handle tool calls if present
            function_calls = []
            if hasattr(response, "candidates") and response.candidates:
                for candidate in response.candidates:
                    if hasattr(candidate, "content") and candidate.content:
                        for part in candidate.content.parts:
                            if hasattr(part, "function_call") and part.function_call:
                                function_calls.append(part.function_call)
            
            if function_calls:
                logger.info(f"Received function calls: {len(function_calls)}")
                
                # Convert to OpenAI format
                tool_calls = []
                for i, fc in enumerate(function_calls):
                    tool_call = {
                        "id": f"call_{completion_id}_{i}",
                        "type": "function",
                        "function": {
                            "name": fc.name,
                            "arguments": json.dumps(fc.args)
                        }
                    }
                    tool_calls.append(tool_call)
                
                standardized_response["choices"][0]["message"]["tool_calls"] = tool_calls
                standardized_response["choices"][0]["finish_reason"] = "tool_calls"
                
                # Remove content if tools are called
                if tool_calls:
                    standardized_response["choices"][0]["message"]["content"] = None
            
            return standardized_response
            
        except Exception as e:
            end_time = time.time()
            logger.error(f"Google request failed, time taken: {end_time - start_time:.2f} seconds, error: {str(e)}")
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
        """Process Google streaming chat completion request
        
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
            logger.info(f"Google streaming request started, model: {self.model}, session ID: {session_id or 'None'}")
            
            # For Google API, get the full response first then simulate streaming
            response = await self.chat_completion(messages, tools, tool_choice, session_id)
            
            # Extract content from response
            content = response.get("choices", [{}])[0].get("message", {}).get("content", "")
            completion_id = response.get("id", f"google-stream-{int(time.time() * 1000)}")
            
            # Check for tool calls
            tool_calls = response.get("choices", [{}])[0].get("message", {}).get("tool_calls")
            
            # If there are tool calls, return them directly without streaming
            if tool_calls:
                logger.info(f"Returning tool calls directly without streaming")
                yield {
                    "id": completion_id,
                    "timestamp": int(time.time()),
                    "model": self.model,
                    "choices": [
                        {
                            "index": 0,
                            "delta": {
                                "role": "assistant",
                                "tool_calls": tool_calls
                            },
                            "finish_reason": None
                        }
                    ]
                }
                
                # Final chunk
                yield {
                    "id": completion_id,
                    "timestamp": int(time.time()),
                    "model": self.model,
                    "choices": [
                        {
                            "index": 0,
                            "delta": {},
                            "finish_reason": "tool_calls"
                        }
                    ]
                }
                
                end_time = time.time()
                logger.info(f"Google streaming request completed with tool calls, time taken: {end_time - start_time:.2f} seconds")
                return
            
            # Simulate streaming by chunking the response
            if content:
                chunk_size = 10  # Number of characters per chunk
                chunks = [content[i:i+chunk_size] for i in range(0, len(content), chunk_size)]
                
                # Stream content in chunks
                for chunk in chunks:
                    # Add a small delay to simulate streaming
                    await asyncio.sleep(0.05)
                    
                    yield {
                        "id": completion_id,
                        "timestamp": int(time.time()),
                        "model": self.model,
                        "choices": [
                            {
                                "index": 0,
                                "delta": {
                                    "role": "assistant",
                                    "content": chunk
                                },
                                "finish_reason": None
                            }
                        ]
                    }
            
            # Final chunk
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
            logger.info(f"Google streaming request completed, time taken: {end_time - start_time:.2f} seconds")
            
        except Exception as e:
            end_time = time.time()
            logger.error(f"Google streaming request failed, time taken: {end_time - start_time:.2f} seconds, error: {str(e)}")
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
        """Process MCP tool binding request, integrating Google models with MCP tools
        
        Args:
            messages: List of messages
            tools: Optional tool definitions
            tool_choice: Tool choice mode
            session_id: Session ID
            mcp_config: MCP configuration
        
        Returns:
            Standardized response
        """
        logger.info(f"Google MCP request started, model: {self.model}, session ID: {session_id or 'None'}")
        start_time = time.time()
        
        try:
            # Create Google LLM client
            llm = ChatGoogleGenerativeAI(
                model=self.model,
                google_api_key=self.api_key,
                temperature=0.7
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
                        # Look for nested content structures
                        if hasattr(agent_response, "messages") and agent_response.messages:
                            # Find the last assistant message
                            for message in reversed(agent_response.messages):
                                if hasattr(message, "type") and message.type == "ai" and hasattr(message, "content"):
                                    content = message.content
                                    # Remove content between <think> tags
                                    content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL).strip()
                                    if content:
                                        answer = content
                                        logger.info(f"Extracted content from messages: {answer}")
                                        break
                        
                        # If above method didn't get a result, try direct content attribute
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
                    logger.info(f"Google MCP request completed, time taken: {end_time - start_time:.2f} seconds")
                    
                    # Build standard response format
                    return {
                        "id": f"google-mcp-{int(time.time() * 1000)}",
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
            logger.error(f"Google MCP request failed, time taken: {end_time - start_time:.2f} seconds, error: {str(e)}")
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