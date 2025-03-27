from typing import List, Dict, Any, Optional, AsyncGenerator, Union
import json
import logging
import os
import time
import traceback
from dotenv import load_dotenv
import asyncio
import requests
from requests.exceptions import RequestException
import uuid
import google.api_core.exceptions
import re
from uuid import UUID  # Add explicit import for UUID
from datetime import datetime
from pydantic import BaseModel

# Import langchain related packages
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, ToolMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_nvidia_ai_endpoints import ChatNVIDIA
from langchain_core.runnables import RunnablePassthrough
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import StructuredTool

# Import MCP related packages
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
# from langchain_mcp_adapters.tools import load_mcp_tools  # 注释掉有问题的导入
from app.services.mcp_tools import custom_load_mcp_tools as load_mcp_tools  # 使用自定义的工具加载函数
from langgraph.prebuilt import create_react_agent
from langchain_mcp_adapters.client import MultiServerMCPClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
llm = os.getenv("DEFAULT_MODEL", "gemini-2.5-pro-exp-03-25")

# Custom types for multimodal content
class ContentPart(BaseModel):
    """A part of a message content, can be either text or image"""
    type: str  # "text" or "image"
    text: Optional[str] = None
    image_url: Optional[Dict[str, str]] = None  # {"url": "http://..."} or {"url": "data:image/jpeg;base64,..."}

# Define message type for multimodal content
MultimodalContent = Union[str, List[ContentPart]]

class ChatService:
    """Chat service class, handles chat requests and responses"""
    
    def __init__(self):
        """Initialize chat service"""
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "")
        self.google_api_key = os.getenv("GOOGLE_API_KEY", "")
        self.nvidia_api_key = os.getenv("NVIDIA_API_KEY", "")
        self.nvidia_api_base = os.getenv("NVIDIA_API_BASE", "https://integrate.api.nvidia.com/v1")
        
        # Print API key availability (without printing the actual key values)
        logger.info(f"OpenAI API key available: {bool(self.openai_api_key)}")
        logger.info(f"Google API key available: {bool(self.google_api_key)}")
        logger.info(f"NVIDIA API key available: {bool(self.nvidia_api_key)}")
        logger.info(f"NVIDIA API base URL: {self.nvidia_api_base}")
        
        # Initialize Google client
        if self.google_api_key:
            self.google_client = ChatGoogleGenerativeAI(
                model=llm,
                google_api_key=self.google_api_key,
                temperature=0.7
            )
        else:
            self.google_client = None
            logger.warning("Google API key not available, Google models will not be available")
        
        # Enable MCP if environment variable is set
        self.use_mcp = os.getenv("USE_MCP", "false").lower() == "true"
        # Initialize MCP configuration
        self.mcp_config = {}
        self.load_mcp_config()
        
    def load_mcp_config(self):
        """Load MCP configuration from JSON file"""
        try:
            # Get the absolute path to the config file
            current_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            config_path = os.path.join(current_dir, "..", "config", "mcp_config.json")
            logger.info(f"Trying to load MCP config file: {config_path}")
            
            if not os.path.exists(config_path):
                logger.warning(f"MCP configuration file not found: {config_path}")
                return None
            
            with open(config_path, 'r') as f:
                config_content = f.read()
                logger.info(f"Config file content: {config_content}")
                self.mcp_config = json.loads(config_content)
            
            logger.info(f"MCP configuration loaded: {config_path}")
            logger.info(f"MCP configuration content: {json.dumps(self.mcp_config, ensure_ascii=False)}")
            logger.info(f"MCP services list: {', '.join(self.mcp_config.keys())}")
            logger.info(f"Number of MCP services: {len(self.mcp_config)}")
            
            # Validate configuration
            for service_name, service_config in self.mcp_config.items():
                if "transport" not in service_config:
                    logger.error(f"Missing 'transport' in service config for {service_name}")
                    return None
                if "command" not in service_config:
                    logger.error(f"Missing 'command' in service config for {service_name}")
                    return None
                if "args" not in service_config:
                    logger.error(f"Missing 'args' in service config for {service_name}")
                    return None
                
        except Exception as e:
            logger.error(f"Error loading MCP configuration: {str(e)}")
            logger.error(traceback.format_exc())
    
    def _get_llm(self, model: str) -> Any:
        """Get the appropriate language model based on model type"""
        # First check if model is in any of the environment variable lists
        nvidia_models = os.getenv("NVIDIA_MODELS", "").split(",")
        google_models = os.getenv("GOOGLE_MODELS", "").split(",")
        openai_models = os.getenv("OPENAI_MODELS", "").split(",")
        anthropic_models = os.getenv("ANTHROPIC_MODELS", "").split(",")
        
        # Clean up whitespace from model names
        nvidia_models = [m.strip() for m in nvidia_models if m.strip()]
        google_models = [m.strip() for m in google_models if m.strip()]
        openai_models = [m.strip() for m in openai_models if m.strip()]
        anthropic_models = [m.strip() for m in anthropic_models if m.strip()]
        
        # Check if model supports multimodal inputs
        supports_multimodal = self._check_multimodal_support(model)
        
        # Check if model is in NVIDIA models list
        if model in nvidia_models or any(model == m.strip() for m in nvidia_models):
            # Extract actual model name from model string
            nvidia_model = model
            if model.startswith("nvidia-"):
                nvidia_model = model[7:]  # Remove "nvidia-" prefix
            
            # Special model name mappings
            if nvidia_model == "deepseek":
                nvidia_model = "deepseek-ai/deepseek-r1"
            elif nvidia_model == "llama-3":
                nvidia_model = "nvidia/llama-3.3-nemotron-super-49b-v1"
            elif nvidia_model == "gemma-3":
                nvidia_model = "google/gemma-3-27b-it"
            
            logger.info(f"Using NVIDIA model: {nvidia_model}")
            
            # Create NVIDIA model with tool support disabled for unsupported models
            return ChatNVIDIA(
                model=nvidia_model,
                nvidia_api_key=self.nvidia_api_key,
                base_url=self.nvidia_api_base,
                temperature=0.7,
                tools_enabled=False  # Disable tools by default for NVIDIA models
            )
        # Check if model is in OpenAI models list
        elif model in openai_models or model.startswith("gpt"):
            # Use OpenAI model
            logger.info(f"Using OpenAI model: {model}")
            
            # For GPT models that support vision
            if supports_multimodal:
                logger.info(f"Model {model} supports multimodal inputs")
                return ChatOpenAI(
                    model=model,
                    openai_api_key=self.openai_api_key,
                    temperature=0.7,
                    max_tokens=2000
            )
            else:
                return ChatOpenAI(
                    model=model,
                    openai_api_key=self.openai_api_key,
                    temperature=0.7
                )
        # Check if model is in Google models list
        elif model in google_models or model.startswith("gemini"):
            # Create Google client
            logger.info(f"Using Google model: {model}")
            
            # For Gemini models with vision support
            if supports_multimodal:
                logger.info(f"Model {model} supports multimodal inputs")
                return ChatGoogleGenerativeAI(
                    model=model,
                    google_api_key=self.google_api_key,
                    temperature=0.7,
                    convert_system_message_to_human=True
                )
            else:
                return ChatGoogleGenerativeAI(
                    model=model,
                    google_api_key=self.google_api_key,
                    temperature=0.7
                )
        # Check if model is in Anthropic models list
        elif model in anthropic_models or model.startswith("claude"):
            # Use Anthropic model via OpenAI API 
            logger.info(f"Using Anthropic model via OpenAI: {model}")
            
            # For Claude models with vision support
            if supports_multimodal:
                logger.info(f"Model {model} supports multimodal inputs")
                return ChatOpenAI(
                    model=model,
                    openai_api_key=self.openai_api_key,
                    temperature=0.7,
                    max_tokens=2000
                )
            else:
                return ChatOpenAI(
                    model=model,
                    openai_api_key=self.openai_api_key,
                    temperature=0.7
                )
        # Fallback to feature-based detection as a backup
        elif "deepseek" in model or "microsoft" in model or "phi" in model or "qwen" in model or "mixtral" in model or "llama" in model:
            # Treat as NVIDIA model
            logger.info(f"Using NVIDIA model (fallback detection): {model}")
            return ChatNVIDIA(
                model=model,
                nvidia_api_key=self.nvidia_api_key,
                base_url=self.nvidia_api_base,
                temperature=0.7,
                tools_enabled=False
            )
        else:
            # Default to Google (with warning)
            logger.warning(f"Unknown model type: {model} - defaulting to Google. Add to .env PROVIDER_MODELS if needed.")
            return ChatGoogleGenerativeAI(
                model=model,
                google_api_key=self.google_api_key,
                temperature=0.7
            )
    
    async def chat_completion(
        self, 
        messages: List[Dict[str, Any]], 
        model: str = "gemini-2.5-pro-exp-03-25", 
        tools: List[Dict[str, Any]] = None, 
        tool_choice: str = "auto",
        session_id: str = None
    ) -> Dict[str, Any]:
        """Process a chat completion request."""
        try:
            # Log key information
            logger.info(f"Chat completion with model: {model}")
            
            # Check if we're using MCP tools
            if tool_choice == "mcp":
                logger.info(f"Chat completion with MCP model: {model}")
                return await self._mcp_agent_chat_completion(messages, model, tools)
            
            # Standard chat completion without MCP
            llm = self._get_llm(model)  # Always get the model specified by the user
            
            # Create a unique response ID
            response_id = f"chatcmpl-{str(uuid.uuid4())}"
            created_time = int(time.time())
            
            # Process messages for the model
            processed_messages = self._convert_messages(messages)
            
            # Define functions for the model if tools are provided
            functions = []
            function_call = "none"
            
            if tools:
                functions = tools
                function_call = tool_choice

            # Call the model and get the response
            try:
                response = await llm.ainvoke(
                    processed_messages
                )
                
                # Extract content from the response
                content = ""
                if hasattr(response, "content"):
                    content = response.content
                    
                # Construct the response format
                choices = [{
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": content
                    },
                    "finish_reason": "stop"
                }]
                
                # Construct the final response
                result = {
                    "id": response_id,
                    "object": "chat.completion",
                    "created": created_time,
                    "model": model,  # Use the model specified by the user
                    "choices": choices,
                    "usage": {
                        "prompt_tokens": 0,
                        "completion_tokens": 0,
                        "total_tokens": 0
                    }
                }
                
                return result
            except Exception as model_error:
                logger.error(f"Error with model {model}: {str(model_error)}")
                logger.error(traceback.format_exc())
                
                # Return error response with the requested model
                return {
                    "id": response_id,
                    "object": "chat.completion",
                    "created": created_time,
                    "model": model,  # Keep using the requested model
                    "choices": [{
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": f"Error using model {model}: {str(model_error)}"
                        },
                        "finish_reason": "stop"
                    }],
                    "usage": {
                        "prompt_tokens": 0,
                        "completion_tokens": 0,
                        "total_tokens": 0
                    }
                }
            
        except Exception as e:
            logger.error(f"Error in chat completion: {str(e)}")
            logger.error(traceback.format_exc())
            
            # Return error response with the requested model
            return {
                "id": f"error-{str(uuid.uuid4())}",
                "object": "chat.completion",
                "created": int(time.time()),
                "model": model,  # Keep using the requested model
                "choices": [{
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": f"An error occurred: {str(e)}"
                    },
                    "finish_reason": "stop"
                }],
                "usage": {
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "total_tokens": 0
                }
            }
            
    async def _mcp_agent_chat_completion(self, messages: List[Dict[str, Any]], model: str, tools: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """Process a chat completion request with an MCP agent."""
        # Get the start time for performance measurement
        start_time = time.time()
        
        try:
            # Get the MCP configuration
            mcp_config = self._get_mcp_config()
            logger.info(f"MCP config: {json.dumps(mcp_config, indent=2)}")
            
            # Initialize an MCP client with the configuration
            client = MultiServerMCPClient(mcp_config)
            
            # Start the MCP client
            await client.__aenter__()
            
            try:
                # Get tools from the MCP client
                mcp_tools = client.get_tools()
                logger.info(f"Getting MCP tools...")
                logger.info(f"Available MCP tools: {mcp_tools}")
                
                # Create a React agent with the user-specified model (not a hardcoded one)
                logger.info(f"Creating React agent with model: {model}")
                
                # Get the LLM with appropriate configuration - use the model specified by the user
                llm = self._get_llm(model)
                
                # Convert messages to LangChain format
                lc_messages = self._convert_to_langchain_messages(messages)
                
                # Extract user message
                user_message = None
                for msg in reversed(lc_messages):
                    if isinstance(msg, HumanMessage):
                        user_message = msg
                        break
                
                if not user_message:
                    user_message = HumanMessage(content="What can you help me with?")
                
                # Check if the model supports tools
                tools_supported = True
                model_type = "standard"
                
                # Identify model type based on prefix
                if model.startswith("gemini"):
                    model_type = "google"
                    # First make sure the model is configured correctly
                    if hasattr(llm, 'client'):
                        # Set the required properties for Google models to work with React agent
                        llm.client.streaming = False
                elif "qwen" in model or "deepseek" in model:
                    # Known models that don't support tools well
                    tools_supported = False
                    model_type = "simple"
                    logger.info(f"Using simple chat completion for model {model} as it doesn't support tools")
                
                # Get just the user query as a plain string
                user_query = user_message.content
                logger.info(f"User query for {'React agent' if tools_supported else 'simple chat'}: {user_query}")
                
                # Handle differently based on whether tools are supported
                if tools_supported:
                    # Create React agent with tools for the specified model
                    agent = create_react_agent(
                        model=llm,
                        tools=mcp_tools
                    )
                    # Invoke the agent with the properly structured input format
                    agent_response = await agent.ainvoke({"messages": user_query})
                else:
                    # For models that don't support tools, just use a direct chat completion
                    agent_response = await llm.ainvoke(lc_messages)
                    
                    logger.info(f"Raw agent response: {agent_response}")
                
                # Extract content from agent response
                content = ""
                if isinstance(agent_response, dict):
                    logger.info("Agent response is a dictionary")
                    if "messages" in agent_response:
                        # Extract the last AI message from the conversation
                        messages = agent_response["messages"]
                        for msg in reversed(messages):
                            if isinstance(msg, AIMessage) and msg.content:
                                content = msg.content
                                logger.info(f"Found AI message content: {content}")
                                break
                    elif "output" in agent_response:
                        content = agent_response["output"]
                        logger.info("Using 'output' field from response")
                    elif "content" in agent_response:
                        content = agent_response["content"]
                        logger.info("Using 'content' field from response")
                    elif "response" in agent_response:
                        content = agent_response["response"]
                        logger.info("Using 'response' field from response")
                    else:
                        logger.warning(f"No recognized content field found in response. Keys: {list(agent_response.keys())}")
                elif isinstance(agent_response, str):
                    logger.info("Agent response is a string")
                    content = agent_response
                elif isinstance(agent_response, AIMessage):
                    logger.info("Agent response is an AIMessage")
                    content = agent_response.content
                    logger.info(f"Extracted content from AIMessage: {content}")
                else:
                    logger.warning(f"Unexpected response type: {type(agent_response)}")
                    # Try to get content attribute if it exists
                    if hasattr(agent_response, 'content'):
                        content = agent_response.content
                        logger.info(f"Extracted content from object with content attribute: {content}")
                
                if not content:
                    logger.warning("No content extracted from response, using default error message")
                    content = "I apologize, but I encountered an issue processing your request. Please try again."
                
                logger.info(f"Extracted content: {content}")
                
                # Create the final response structure
                response_id = f"chatcmpl-{str(uuid.uuid4())}"
                final_response = {
                    'id': response_id,
                    'object': 'chat.completion',
                    'created': int(time.time()),
                    'model': model,  # Use the model specified by the user
                    'choices': [
                        {
                            'index': 0,
                            'message': {
                                'role': 'assistant',
                                'content': content
                            },
                            'finish_reason': 'stop'
                        }
                    ],
                    'usage': {
                        'prompt_tokens': 0,
                        'completion_tokens': 0,
                        'total_tokens': 0
                    }
                }
                
                logger.info(f"Final response: {final_response}")
                logger.info(f"MCP Agent call completed successfully, time taken: {(time.time() - start_time):.2f} seconds")
                
                return final_response
            
            except Exception as e:
                logger.error(f"Error during model execution: {str(e)}")
                logger.error(traceback.format_exc())
                raise e
            
            finally:
                # Ensure the MCP client is properly closed
                await client.__aexit__(None, None, None)
                
        except google.api_core.exceptions.ResourceExhausted:
            logger.warning("Google API quota exhausted, but keeping user's selected model")
            # Return an error response with the user's model
            response_id = f"chatcmpl-{str(uuid.uuid4())}"
            error_response = {
                'id': response_id,
                'object': 'chat.completion',
                'created': int(time.time()),
                'model': model,  # Keep the user-specified model
                'choices': [
                    {
                        'index': 0,
                        'message': {
                            'role': 'assistant',
                            'content': "I apologize, but the API quota for this model has been exhausted. Please try again later."
                        },
                        'finish_reason': 'stop'
                    }
                ],
                'usage': {
                    'prompt_tokens': 0,
                    'completion_tokens': 0,
                    'total_tokens': 0
                }
            }
            
            logger.info(f"MCP Agent call failed due to quota exhaustion, time taken: {(time.time() - start_time):.2f} seconds")
            return error_response
            
        except Exception as e:
            elapsed_time = time.time() - start_time
            logger.error(f"MCP Agent call failed, time taken: {elapsed_time:.2f} seconds")
            logger.error(f"MCP Agent error details: {str(e)}")
            logger.error(f"Traceback (most recent call last):\n{traceback.format_exc()}")
            
            # Return an error response with the user's selected model
            response_id = f"chatcmpl-{str(uuid.uuid4())}"
            error_response = {
                'id': response_id,
                'object': 'chat.completion',
                'created': int(time.time()),
                'model': model,  # Keep the user-specified model
                'choices': [
                    {
                        'index': 0,
                        'message': {
                            'role': 'assistant',
                            'content': f"I apologize, but I encountered an error with the requested model: {str(e)}"
                        },
                        'finish_reason': 'stop'
                    }
                ],
                'usage': {
                    'prompt_tokens': 0,
                    'completion_tokens': 0,
                    'total_tokens': 0
                }
            }
            
            return error_response
    
    async def stream_chat_completion(
        self,
        messages: List[Dict[str, Any]],
        model: str,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: str = "auto",
        session_id: Optional[str] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream chat completion responses"""
        try:
            logger.info(f"Streaming chat completion, model: {model}")
            
            # If MCP is enabled and MCP services are configured, use MCP processing
            if self.use_mcp and self.mcp_config:
                async for chunk in self._mcp_stream_chat_completion(messages, model, tools, tool_choice, session_id):
                    yield chunk
                return
            
            # Convert messages to langchain format
            lc_messages = self._convert_to_langchain_messages(messages)
            
            # Get the appropriate model adapter
            provider = None
            if model.startswith("gpt"):
                provider = "openai"
            elif model.startswith("gemini"):
                provider = "google"
            else:
                provider = "nvidia"  # Default for other models
                
            # Try to get adapter from factory
            try:
                from app.services.model_adapters.factory import ModelAdapterFactory
                adapter_factory = ModelAdapterFactory()
                adapter = adapter_factory.get_adapter(model)
                
                # Stream through the adapter
                async for chunk in adapter.stream_chat_completion(messages, tools, tool_choice, session_id):
                    yield chunk
            except (ImportError, AttributeError, ValueError) as e:
                logger.warning(f"Adapter factory not available or adapter not found: {str(e)}")
                logger.warning("Falling back to direct model streaming")
                
                # Fallback to direct streaming based on model type
                if model.startswith("gpt"):
                    # OpenAI model streaming
                    async for chunk in self._stream_openai_chat(lc_messages, model, tools, tool_choice):
                        yield chunk
                elif model.startswith("nvidia") or model.startswith("mixtral") or model.startswith("llama") or "deepseek" in model or "gemma" in model:
                    # NVIDIA model streaming
                    async for chunk in self._stream_nvidia_chat(lc_messages, model, tools, tool_choice):
                        yield chunk
                else:
                    # Google model streaming (default)
                    async for chunk in self._stream_google_chat(lc_messages, model, tools, tool_choice):
                        yield chunk
            
        except Exception as e:
            logger.error(f"Error in stream_chat_completion: {str(e)}")
            logger.error(traceback.format_exc())
            yield {
                "error": str(e),
                "traceback": traceback.format_exc()
            }
    
    async def _stream_google_chat(
        self,
        messages: List[Any],
        model: str,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: str = "auto"
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream chat completion from Google model"""
        try:
            # Create Google client with the specified model
            llm = ChatGoogleGenerativeAI(
                model=model,
                google_api_key=self.google_api_key,
                temperature=0.7,
                streaming=True
            )
            
            async for chunk in llm.astream(messages):
                if chunk.content is not None:
                    content_json = json.dumps({"content": chunk.content, "model": model})
                    yield f"data: {content_json}\n\n"
            
        except Exception as e:
            logger.error(f"Error streaming Google chat: {str(e)}")
            error_json = json.dumps({"error": str(e)})
            yield f"data: {error_json}\n\n"
    
    async def _stream_openai_chat(
        self,
        messages: List[Any],
        model: str,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: str = "auto"
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream chat completion from OpenAI model"""
        try:
            # Create OpenAI client with the specified model
            llm = ChatOpenAI(
                model=model,
                openai_api_key=self.openai_api_key,
                temperature=0.7,
                streaming=True
            )
            
            # Setup tools if provided
            if tools:
                llm.tools = tools
                if tool_choice and tool_choice != "auto":
                    llm.tool_choice = {"type": "function", "function": {"name": tool_choice}}
            
            # Stream responses
            previous_content = ""
            async for chunk in llm.astream(messages):
                if chunk.content is not None:
                    # Only send the incremental content, not the entire accumulated content
                    new_content = chunk.content
                    if new_content.startswith(previous_content) and len(new_content) > len(previous_content):
                        # If the new content is an extension of previous content, only send the incremental part
                        delta_content = new_content[len(previous_content):]
                        previous_content = new_content
                    else:
                        # Otherwise send everything
                        delta_content = new_content
                        previous_content = new_content
                    
                    # Add a small delay to make the streaming effect more noticeable
                    await asyncio.sleep(0.1)
                    
                    response_data = {
                        "choices": [
                            {
                                "delta": {
                                    "content": delta_content
                                }
                            }
                        ],
                    "model": model
                }
                    content_json = json.dumps(response_data)
                    yield f"data: {content_json}\n\n"
            
        except Exception as e:
            logger.error(f"Error streaming OpenAI chat: {str(e)}")
            error_json = json.dumps({"error": str(e)})
            yield f"data: {error_json}\n\n"
    
    async def _stream_nvidia_chat(
        self,
        messages: List[Any],
        model: str,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: str = "auto"
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream chat completion from NVIDIA model"""
        try:
            # Extract actual model name if needed
            nvidia_model = model
            if model.startswith("nvidia-"):
                nvidia_model = model[7:]
            
            # Special model mappings
            if nvidia_model == "deepseek":
                nvidia_model = "deepseek-ai/deepseek-r1"
            elif nvidia_model == "llama-3":
                nvidia_model = "nvidia/llama-3.3-nemotron-super-49b-v1"
            elif nvidia_model == "gemma-3":
                nvidia_model = "google/gemma-3-27b-it"
            
            # Create NVIDIA client
            llm = ChatNVIDIA(
                model=nvidia_model,
                nvidia_api_key=self.nvidia_api_key,
                base_url=self.nvidia_api_base,
                temperature=0.7,
                streaming=True
            )
            
            # Stream responses with improved chunking
            previous_content = ""
            async for chunk in llm.astream(messages):
                if chunk.content is not None:
                    # Only send the incremental content, not the entire accumulated content
                    new_content = chunk.content
                    if new_content.startswith(previous_content) and len(new_content) > len(previous_content):
                        # If the new content is an extension of previous content, only send the incremental part
                        delta_content = new_content[len(previous_content):]
                        previous_content = new_content
                    else:
                        # Otherwise send everything
                        delta_content = new_content
                        previous_content = new_content
                    
                    # Add a small delay to make the streaming effect more noticeable
                    await asyncio.sleep(0.1)
                    
                    response_data = {
                "choices": [
                    {
                        "delta": {
                                    "content": delta_content
                                }
                            }
                        ],
                        "model": model
                    }
                    content_json = json.dumps(response_data)
                    yield f"data: {content_json}\n\n"
            
        except Exception as e:
            logger.error(f"Error streaming NVIDIA chat: {str(e)}")
            error_json = json.dumps({"error": str(e)})
            yield f"data: {error_json}\n\n"
    
    def _convert_to_langchain_messages(self, messages: List[Dict[str, Any]]) -> List[Union[HumanMessage, AIMessage, SystemMessage]]:
        """Convert chat messages to LangChain message format"""
        langchain_messages = []
        
        for message in messages:
            role = message.get("role", "")
            content = message.get("content", "")
            
            # Handle multimodal content (can be string or list of content parts)
            if isinstance(content, list):
                # For multimodal content, process each part
                processed_content = []
                
                for part in content:
                    if isinstance(part, dict):
                        if part.get("type") == "text":
                            # Text content
                            processed_content.append({"type": "text", "text": part.get("text", "")})
                        elif part.get("type") == "image":
                            # Image content
                            image_url = part.get("image_url", {}).get("url", "")
                            if image_url:
                                processed_content.append({
                                    "type": "image_url", 
                                    "image_url": {"url": image_url}
                                })
                
                if role == "user":
                    langchain_messages.append(HumanMessage(content=processed_content))
                elif role == "assistant":
                    langchain_messages.append(AIMessage(content=processed_content))
                elif role == "system":
                    # For system messages, convert multimodal to text as most models expect
                    # text-only system messages
                    text_parts = [part.get("text", "") for part in processed_content 
                                 if part.get("type") == "text"]
                    langchain_messages.append(SystemMessage(content=" ".join(text_parts)))
            else:
                # Regular text content (string)
                if role == "user":
                    langchain_messages.append(HumanMessage(content=content))
                elif role == "assistant":
                    langchain_messages.append(AIMessage(content=content))
                elif role == "system":
                    langchain_messages.append(SystemMessage(content=content))
        
        return langchain_messages
    
    def _convert_to_standard_format(self, lc_response: Any, model: str) -> Dict[str, Any]:
        """Convert LangChain response to standard API response format"""
        # Extract content from LangChain response
        if hasattr(lc_response, "content"):
            content = lc_response.content
        else:
            content = str(lc_response)
        
        # Create standard response format
        response = {
            "id": f"chatcmpl-{int(time.time() * 1000)}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": model,
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
                "prompt_tokens": 0,  # Would need token counter for accuracy
                "completion_tokens": 0,
                "total_tokens": 0
            }
        }
        
        return response

    def _build_error_response(self, model: str, error_message: str) -> Dict[str, Any]:
        """Build an error response in the standard format"""
        return {
            "id": f"response-{int(time.time() * 1000)}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": model,
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": error_message
                    },
                    "finish_reason": "stop"
                }
            ],
            "usage": {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0
            }
        }

    async def _google_chat_completion(
        self,
        messages: List[Dict[str, Any]],
        model: str,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: str = "auto",
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Process chat completion request using Google's model"""
        try:
            if not self.google_client:
                raise ValueError("Google client not initialized. Please check your Google API key.")
            
            # Convert messages to Google's format
            google_messages = []
            for msg in messages:
                # Handle different message types
                if isinstance(msg, SystemMessage):
                    # Google doesn't support system messages, prepend to first user message
                    if google_messages and isinstance(google_messages[0], HumanMessage):
                        google_messages[0].parts[0].text = f"{msg.content}\n\n{google_messages[0].parts[0].text}"
                elif isinstance(msg, HumanMessage):
                    google_messages.append({
                        "role": "user",
                        "parts": [{"text": msg.content}]
                    })
                elif isinstance(msg, AIMessage):
                    google_messages.append({
                        "role": "model",
                        "parts": [{"text": msg.content}]
                    })
                elif isinstance(msg, ToolMessage):
                    google_messages.append({
                        "role": "model",
                        "parts": [{"text": f"Tool response: {msg.content}"}]
                    })
            
            # Prepare request
            request = {
                "contents": google_messages,
                "generationConfig": {
                    "temperature": 0.7,
                    "topK": 40,
                    "topP": 0.95,
                    "maxOutputTokens": 1024,
                }
            }
            
            # Add tools if provided
            if tools:
                request["tools"] = tools
            
            # Send request to Google API
            response = await self.google_client.generate_content(request)
            
            # Process response
            if response.candidates and response.candidates[0].content:
                content = response.candidates[0].content.parts[0].text
                return {
                    "id": f"chatcmpl-{int(time.time() * 1000)}",
                    "object": "chat.completion",
                    "created": int(time.time()),
                    "model": model,
                    "choices": [
                        {
                            "index": 0,
                            "message": {
                                "role": "assistant",
                                "content": content
                            },
                            "finish_reason": "stop"
                        }
                    ]
                }
            else:
                raise Exception("No response from Google API")
                
        except Exception as e:
            logger.error(f"Error in Google chat completion: {str(e)}")
            logger.error(traceback.format_exc())
            raise

    async def _mcp_stream_chat_completion(
        self, 
        messages: List[Dict[str, str]], 
        model: str,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[Union[str, Dict[str, Any]]] = None,
        session_id: Optional[str] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Stream chat completion for MCP models.
        
        Args:
            messages: List of message dictionaries
            model: Model name
            tools: List of tools
            tool_choice: Tool choice
            session_id: Session ID
            
        Yields:
            Chunks of the response with content
        """
        try:
            logger.info(f"Streaming chat completion with MCP model: {model}")
            start_time = time.time()
            
            # First, get the full response - pass tools parameter
            response = await self._mcp_agent_chat_completion(
                messages=messages,
                model=model,
                tools=tools
            )
            
            if "error" in response:
                logger.error(f"Error in MCP streaming: {response['error']}")
                error_json = json.dumps({"error": response['error']})
                yield f"data: {error_json}\n\n"
                return
            
            # Get the content from the response
            if "choices" in response and len(response["choices"]) > 0:
                full_content = response["choices"][0]["message"]["content"]
            else:
                full_content = response.get("content", "")
            
            if not full_content:
                empty_json = json.dumps({"content": ""})
                yield f"data: {empty_json}\n\n"
                return
            
            # Simulate streaming by sending content in smaller chunks
            # Split content into sentences or smaller chunks
            chunks = re.split(r'(?<=[.!?])\s+', full_content)
            if len(chunks) <= 1:
                # If no sentence breaks, split by words
                chunks = full_content.split(" ")
            
            # 使用单词级别的块大小，每个块最多包含1-2个单词
            chunk_size = 1  # 每次只发送1个单词
            
            combined_chunks = []
            for i in range(0, len(chunks), chunk_size):
                end = min(i + chunk_size, len(chunks))
                if chunks[0] == "":  # Handle split creating empty first chunk
                    combined_chunks.append(" ".join(chunks[i+1:end]))
                else:
                    combined_chunks.append(" ".join(chunks[i:end]))
            
            # Stream chunks with a more noticeable delay
            for i, chunk in enumerate(combined_chunks):
                # 增加延迟使流式效果更明显
                await asyncio.sleep(0.2)  # 200ms延迟
                # 使用json模块确保内容正确转义
                content_json = json.dumps({"content": chunk})
                yield f"data: {content_json}\n\n"
            
            # Log streaming completion
            duration = time.time() - start_time
            logger.info(f"MCP streaming completed in {duration:.2f}s, sent {len(combined_chunks)} chunks")
            
        except Exception as e:
            logger.error(f"Error in MCP streaming: {str(e)}")
            error_json = json.dumps({"error": str(e)})
            yield f"data: {error_json}\n\n"

    async def stream_message(
        self,
        session_id: str,
        message_content: str,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream a message in a chat session"""
        try:
            # Get session data
            session_data = self._get_session_data(session_id)
            if not session_data:
                logger.error(f"Session {session_id} not found")
                error_json = json.dumps({"error": f"Session {session_id} not found"})
                yield f"data: {error_json}\n\n"
                return

            # Use provided model/provider or fall back to session defaults
            provider = provider or session_data.get("provider")
            model = model or session_data.get("model")
            
            # Add user message to history
            user_message = {"role": "user", "content": message_content}
            session_data["messages"].append(user_message)
            
            # Stream response based on provider
            messages = session_data["messages"]
            assistant_content = ""
            
            # Process streaming response
            async for chunk in self.stream_chat_completion(
                messages=messages,
                model=model,
                session_id=session_id
            ):
                # 直接传递经过正确JSON序列化的响应
                yield chunk
                
                # 尝试解析内容以累积到会话历史中
                try:
                    # 从data: {...}\n\n格式中提取JSON数据
                    if isinstance(chunk, str) and chunk.startswith("data: "):
                        json_str = chunk[6:].strip()
                        chunk_data = json.loads(json_str)
                        
                        # 提取内容
                        content = None
                        if "content" in chunk_data:
                            content = chunk_data["content"]
                        elif "choices" in chunk_data and len(chunk_data["choices"]) > 0:
                            if "delta" in chunk_data["choices"][0] and "content" in chunk_data["choices"][0]["delta"]:
                                content = chunk_data["choices"][0]["delta"]["content"]
                                
                        # 累积内容
                        if content:
                            assistant_content += content
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse JSON from chunk: {chunk}")
                except Exception as e:
                    logger.warning(f"Error while extracting content: {str(e)}")
                    
            # After streaming complete, add assistant message to history
            if assistant_content:
                assistant_message = {"role": "assistant", "content": assistant_content}
                session_data["messages"].append(assistant_message)
                
            # Update session data
            session_storage[session_id] = session_data
            
        except Exception as e:
            logger.error(f"Error streaming message: {str(e)}")
            error_json = json.dumps({"error": str(e)})
            yield f"data: {error_json}\n\n"

    def _get_session_data(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data from storage"""
        from app.services.session_storage import session_storage
        return session_storage.get(session_id)

    def _get_mcp_config(self):
        """Get the MCP configuration from the configured source."""
        if self.mcp_config:
            return self.mcp_config
        else:
            logger.warning("MCP configuration not found, using empty config")
            return {}

    def _convert_messages(self, messages: List[Dict[str, Any]]) -> List[Any]:
        """Convert standard message format to model-compatible format"""
        return self._convert_to_langchain_messages(messages)

    def _check_multimodal_support(self, model: str) -> bool:
        """Check if the model supports multimodal content (images)"""
        # Get multimodal supported models from environment variables
        vision_models = os.getenv("MULTIMODAL_OPENAI_MODELS", "").split(",")
        gemini_vision_models = os.getenv("MULTIMODAL_GOOGLE_MODELS", "").split(",")
        nvidia_vision_models = os.getenv("MULTIMODAL_NVIDIA_MODELS", "").split(",")
        
        # Clean whitespace
        vision_models = [m.strip() for m in vision_models if m.strip()]
        gemini_vision_models = [m.strip() for m in gemini_vision_models if m.strip()]
        nvidia_vision_models = [m.strip() for m in nvidia_vision_models if m.strip()]
        
        # Check if model is in any multimodal support list
        if (model in vision_models or 
            model in gemini_vision_models or 
            model in nvidia_vision_models):
            return True
        
        # Also check for specific model prefixes
        if (model.startswith("gpt-4-vision") or 
            model.startswith("gpt-4o") or 
            model.startswith("gemini") or 
            "vision" in model.lower()):
            return True
            
        return False

# Add comment about MCP configuration file format at the end of the code
"""
MCP configuration file example (config/mcp_config.json):
{
    "models": {
        "MODEL_NAME_1": {
            "server": "SERVER_NAME_1",
            "model": "ACTUAL_MODEL_NAME_1"
        },
        "MODEL_NAME_2": {
            "server": "SERVER_NAME_2",
            "model": "ACTUAL_MODEL_NAME_2"
        }
    },
    "servers": {
        "SERVER_NAME_1": "http://server1-address:port",
        "SERVER_NAME_2": "http://server2-address:port"
    }
}

Usage:
1. Create the config/mcp_config.json file
2. Set the environment variable USE_MCP=true
3. Optional: Set the environment variable MCP_CONFIG_PATH to specify the configuration file path
""" 