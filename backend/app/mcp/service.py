"""
MCP service - Core functionality for handling tool calls using LangChain MCP adapters
"""
import logging
import os
import json
import asyncio
from typing import Dict, Any, List, Optional
from concurrent.futures import ThreadPoolExecutor

from fastapi import HTTPException
from fastapi.responses import StreamingResponse
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
from langchain.schema import HumanMessage, AIMessage, SystemMessage

from app.core.config import get_app_settings
from app.schemas.message import ChatRequest
from app.services.llm_service import LLMService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Global variables
mcp_client = None
mcp_agent = None
settings = get_app_settings()

# Client context for proper async resource management
mcp_client_ctx = None

# Flag to track if MCP is initialized
is_mcp_initialized = False

# Store configurations for lazy loading
mcp_config_cache = None

def load_mcp_config() -> Dict[str, Any]:
    """
    Load MCP configuration from config file
    
    Returns:
        Dict[str, Any]: Configuration dictionary for MCP tools
    """
    global mcp_config_cache
    
    # Return cached config if available
    if mcp_config_cache is not None:
        return mcp_config_cache
        
    try:
        settings = get_app_settings()
        config_path = settings.MCP_CONFIG_PATH
        
        absolute_path = os.path.join(os.getcwd(), config_path) if not os.path.isabs(config_path) else config_path
        
        if os.path.exists(absolute_path):
            logger.info(f"Loading MCP configuration from: {absolute_path}")
            with open(absolute_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                logger.info(f"Loaded configuration with {len(config)} tools")
                # Cache the configuration
                mcp_config_cache = config
                return config
        else:
            logger.warning(f"MCP config file not found at: {absolute_path}")
            mcp_config_cache = {}
            return {}
    except Exception as e:
        logger.error(f"Error loading MCP config: {str(e)}")
        mcp_config_cache = {}
        return {}

async def initialize_mcp(force_init: bool = False) -> bool:
    """
    Initialize MCP client and agent
    
    Args:
        force_init: Force initialization even if already initialized
    
    Returns:
        bool: True if initialization successful, False otherwise
    """
    global mcp_client, mcp_agent, mcp_client_ctx, is_mcp_initialized
    
    # Skip initialization if already done unless forced
    if is_mcp_initialized and not force_init:
        logger.info("MCP already initialized, skipping")
        return True
    
    logger.info("Starting MCP assistant initialization")
    
    try:
        # Load tool configuration
        mcp_config = load_mcp_config()
        if not mcp_config:
            logger.warning("No MCP configuration found, initialization aborted")
            return False
            
        # Log working directory for debugging purposes
        logger.info(f"Current working directory: {os.getcwd()}")
        
        # Convert relative paths to absolute paths and filter unsupported parameters
        filtered_config = {}
        for tool_name, tool_config in mcp_config.items():
            # Validate tool configuration
            if not isinstance(tool_config, dict):
                logger.error(f"Invalid configuration for tool {tool_name}: not a dictionary")
                continue
                
            if "args" not in tool_config:
                logger.warning(f"Tool {tool_name} has no args configuration")
                continue
                
            if not isinstance(tool_config["args"], list):
                logger.error(f"Invalid args configuration for tool {tool_name}: not a list")
                continue
                
            # Create filtered config with only required parameters
            filtered_config[tool_name] = {
                "command": tool_config["command"],
                "args": tool_config["args"],
                "transport": tool_config["transport"]
            }
            
            # Update path if relative
            if len(tool_config["args"]) > 0:
                tool_path = tool_config["args"][0]
                if not os.path.isabs(tool_path):
                    abs_path = os.path.join(os.getcwd(), tool_path)
                    filtered_config[tool_name]["args"][0] = abs_path
                    logger.info(f"Updated {tool_name} path to: {abs_path}")
        
        # Create MultiServerMCPClient (following example implementation)
        logger.info(f"Creating MultiServerMCPClient with configuration: {json.dumps(filtered_config, indent=2)}")
        
        # Initialize client in a separate task to avoid context issues
        async def init_client():
            ctx = MultiServerMCPClient(filtered_config)
            client = await ctx.__aenter__()
            return ctx, client
        
        # Run client initialization in a separate task
        mcp_client_ctx, mcp_client = await asyncio.create_task(init_client())
        
        # Get tool list
        tools = mcp_client.get_tools()
        logger.info(f"Retrieved {len(tools)} tools from MCP client")
        
        if not tools:
            logger.warning("No tools available from MCP client")
            await cleanup_mcp()
            return False
        
        # Log available tools
        tool_names = [tool.name for tool in tools]
        logger.info(f"Available tools: {tool_names}")
        
        # Get LLM model
        llm_service = LLMService()
        provider = settings.DEFAULT_LLM_PROVIDER
        
        # Select the default model based on provider
        if provider == "google":
            model = settings.DEFAULT_GOOGLE_MODEL 
        elif provider == "openai":
            model = settings.DEFAULT_OPENAI_MODEL
        elif provider == "anthropic":
            model = settings.DEFAULT_ANTHROPIC_MODEL
        elif provider == "nvidia":
            model = settings.DEFAULT_NVIDIA_MODEL
        else:
            model = settings.DEFAULT_OPENAI_MODEL
            
        logger.info(f"Using LLM provider: {provider}, model: {model}")
        
        model = llm_service.get_provider(provider, model)
        
        # Create React Agent (following example implementation)
        logger.info(f"Creating React Agent with {len(tools)} tools")
        mcp_agent = create_react_agent(model, tools)
        
        # Mark as initialized
        is_mcp_initialized = True
        
        logger.info("MCP assistant initialization completed successfully")
        return True
    except Exception as e:
        logger.error(f"Error initializing MCP assistant: {str(e)}", exc_info=True)
        # Clean up resources on error
        await cleanup_mcp()
        mcp_client = None
        mcp_agent = None
        is_mcp_initialized = False
        return False

async def cleanup_mcp() -> None:
    """Clean up MCP client resources"""
    global mcp_client, mcp_client_ctx, is_mcp_initialized
    if mcp_client_ctx:
        logger.info("Cleaning up MCP resources")
        try:
            # Exit async context properly
            await mcp_client_ctx.__aexit__(None, None, None)
        except Exception as e:
            logger.error(f"Error during MCP cleanup: {str(e)}")
        finally:
            mcp_client = None
            mcp_client_ctx = None
            is_mcp_initialized = False

async def handle_mcp_complete(request: ChatRequest) -> Dict[str, Any]:
    """
    Handle MCP chat completion request
    
    Args:
        request: ChatRequest with messages
        
    Returns:
        Dict with response messages
    """
    global mcp_agent
    
    if not request.messages:
        raise HTTPException(status_code=400, detail="No messages provided")
    
    # Lazy initialization of MCP when actually needed
    if not is_mcp_initialized:
        init_success = await initialize_mcp()
        if not init_success:
            logger.warning("Failed to initialize MCP, using standard LLM as fallback")
            return await _fallback_complete(request)
    
    if not mcp_agent:
        logger.warning("MCP agent not available, using standard LLM as fallback")
        return await _fallback_complete(request)
    
    try:
        # Extract user message
        user_message = request.messages[-1].content
        
        # Convert messages to format expected by agent
        formatted_messages = []
        for msg in request.messages:
            formatted_messages.append({"role": msg.role, "content": msg.content})
        
        # Invoke agent with message
        logger.info(f"Invoking MCP agent with message: {user_message[:50]}...")
        response = await mcp_agent.ainvoke({"messages": formatted_messages})
        
        return response
    except Exception as e:
        logger.error(f"Error in MCP chat completion: {str(e)}", exc_info=True)
        logger.warning("Falling back to standard LLM")
        return await _fallback_complete(request)

async def handle_mcp_stream(request: ChatRequest) -> StreamingResponse:
    """
    Handle streaming MCP chat completion request
    
    Args:
        request: ChatRequest with messages
        
    Returns:
        StreamingResponse with event stream
    """
    global mcp_agent
    
    if not request.messages:
        raise HTTPException(status_code=400, detail="No messages provided")
    
    # Lazy initialization of MCP when actually needed
    if not is_mcp_initialized:
        logger.info("MCP not initialized yet, initializing now...")
        init_success = await initialize_mcp()
        if not init_success:
            logger.warning("Failed to initialize MCP, using standard LLM as fallback")
            return await _fallback_stream(request)
    
    if not mcp_agent:
        logger.warning("MCP agent not available, using standard LLM as fallback")
        return await _fallback_stream(request)
    
    try:
        # Get latest user message
        user_message = request.messages[-1].content if request.messages else ""
        logger.info(f"Processing with React Agent, user message: {user_message[:100]}...")
        
        # Prepare Agent input (following example implementation)
        # Convert entire messages array to the correct format
        formatted_messages = []
        for msg in request.messages:
            if msg.role == "user":
                formatted_messages.append({"type": "human", "content": msg.content})
            elif msg.role == "assistant":
                formatted_messages.append({"type": "ai", "content": msg.content})
            elif msg.role == "system":
                formatted_messages.append({"type": "system", "content": msg.content})
                
        # Ensure there is at least one user message
        if not formatted_messages:
            formatted_messages.append({"type": "human", "content": user_message})
            
        # Build the agent input correctly
        agent_input = {"messages": formatted_messages}
        logger.info(f"Agent input format: {agent_input}")
        
        # Create async generator to handle streaming response
        async def response_stream():
            yield "data: " + json.dumps({"type": "start"}) + "\n\n"
            
            try:
                # Call React Agent
                logger.info(f"Invoking React Agent with message: {user_message[:50]}...")
                
                try:
                    # Call React Agent with 120 second timeout
                    logger.info("Starting React Agent call")
                    
                    try:
                        async with asyncio.timeout(120):
                            response = await mcp_agent.ainvoke(agent_input)
                            logger.info(f"React Agent response type: {type(response)}")
                            logger.info(f"React Agent response: {str(response)[:200]}...")
                            
                            # Extract pure text content
                            if isinstance(response, dict) and "messages" in response:
                                messages = response["messages"]
                                if messages and isinstance(messages, list) and len(messages) > 0:
                                    # Get the content of the last message
                                    last_message = messages[-1]
                                    
                                    # If it's a tool call result (content is empty but has function_call and tool output)
                                    if hasattr(last_message, 'additional_kwargs') and last_message.additional_kwargs.get('function_call') and 'tool_outputs' in response:
                                        # Directly use tool output as content
                                        tool_outputs = response.get('tool_outputs', [])
                                        if tool_outputs and len(tool_outputs) > 0:
                                            # Get the last tool output
                                            tool_output = tool_outputs[-1]
                                            if hasattr(tool_output, 'output'):
                                                yield f"data: {json.dumps({'content': tool_output.output})}\n\n"
                                            else:
                                                yield f"data: {json.dumps({'content': str(tool_output)})}\n\n"
                                        else:
                                            # Try to extract tool information from function_call
                                            if hasattr(last_message, 'additional_kwargs'):
                                                func_call = last_message.additional_kwargs.get('function_call', {})
                                                if isinstance(func_call, dict) and 'arguments' in func_call:
                                                    tool_name = func_call.get("name", "unknown")
                                                    tool_args = func_call.get("arguments", "{}")
                                                    yield f"data: {json.dumps({'content': 'Using tool: ' + tool_name + ', parameters: ' + tool_args + ', getting result...'})}\n\n"
                                                else:
                                                    yield f"data: {json.dumps({'content': 'Processing your request...'})}\n\n"
                                    # Otherwise, directly return content
                                    elif hasattr(last_message, 'content'):
                                        content = last_message.content
                                        yield f"data: {json.dumps({'content': content})}\n\n"
                                    elif isinstance(last_message, dict) and 'content' in last_message:
                                        content = last_message['content']
                                        yield f"data: {json.dumps({'content': content})}\n\n"
                                    else:
                                        # If content cannot be retrieved, try to convert the entire message to a string
                                        msg_str = str(last_message)
                                        if "content='" in msg_str:
                                            try:
                                                # Extract content from string
                                                content = msg_str.split("content='")[1].split("'")[0]
                                                yield f"data: {json.dumps({'content': content})}\n\n"
                                            except:
                                                yield f"data: {json.dumps({'content': msg_str})}\n\n"
                                        else:
                                            yield f"data: {json.dumps({'content': msg_str})}\n\n"
                                else:
                                    yield f"data: {json.dumps({'content': 'No response content available'})}\n\n"
                            else:
                                # Try to extract content directly from response
                                content = ""
                                if hasattr(response, 'content'):
                                    content = response.content
                                elif isinstance(response, str):
                                    content = response
                                else:
                                    content = str(response)
                                    
                                yield f"data: {json.dumps({'content': content})}\n\n"
                    except asyncio.TimeoutError:
                        logger.error("React Agent call timed out (120 seconds)")
                        yield f"data: {json.dumps({'content': 'Sorry, processing your request timed out. Please try asking again or use a different phrasing.'})}\n\n"
                except Exception as e:
                    logger.error(f"Error in React Agent processing: {str(e)}", exc_info=True)
                    yield f"data: {json.dumps({'error': str(e)})}\n\n"
                    yield "data: [DONE]\n\n"
            except Exception as e:
                logger.error(f"Error in React Agent processing: {str(e)}", exc_info=True)
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
                yield "data: [DONE]\n\n"
        
        return StreamingResponse(
            response_stream(),
            media_type="text/event-stream"
        )
    except Exception as e:
        logger.error(f"Error setting up MCP streaming: {str(e)}", exc_info=True)
        return await _fallback_stream(request)

async def _fallback_complete(request: ChatRequest) -> Dict[str, Any]:
    """
    Fallback to standard LLM for completion
    
    Args:
        request: ChatRequest with messages
        
    Returns:
        Dict with response messages
    """
    llm_service = LLMService()
    
    # Convert messages to LangChain format
    messages = []
    for msg in request.messages:
        if msg.role == "user":
            messages.append(HumanMessage(content=msg.content))
        elif msg.role == "assistant":
            messages.append(AIMessage(content=msg.content))
        else:
            messages.append(SystemMessage(content=msg.content))
    
    # Use standard LLM for response
    response = await llm_service.generate_response(messages)
    
    return {"messages": [{"role": "assistant", "content": response}]}

async def _fallback_stream(request: ChatRequest) -> StreamingResponse:
    """
    Fallback to standard LLM for streaming
    
    Args:
        request: ChatRequest with messages
        
    Returns:
        StreamingResponse with event stream
    """
    llm_service = LLMService()
    
    # Convert messages to LangChain format
    messages = []
    for msg in request.messages:
        if msg.role == "user":
            messages.append(HumanMessage(content=msg.content))
        elif msg.role == "assistant":
            messages.append(AIMessage(content=msg.content))
        else:
            messages.append(SystemMessage(content=msg.content))
    
    # Create streaming response with the standard LLM
    return StreamingResponse(
        llm_service.generate_response_stream(messages),
        media_type="text/event-stream"
    )

async def get_available_tools() -> Dict[str, List[Dict[str, str]]]:
    """
    Get list of available MCP tools
    
    Returns:
        Dict with list of tools
    """
    global mcp_client
    
    # Try to load from config if client not available
    if not mcp_client:
        logger.info("MCP client not available, loading tools from config")
        tool_configs = load_mcp_config()
        
        tools = []
        for name, config in tool_configs.items():
            tools.append({
                "name": name,
                "description": config.get("description", "No description available")
            })
        
        return {"tools": tools}
    
    # Get tools from client if available
    try:
        tools = mcp_client.get_tools()
        tool_list = []
        
        for tool in tools:
            tool_list.append({
                "name": tool.name,
                "description": tool.description
            })
        
        return {"tools": tool_list}
    except Exception as e:
        logger.error(f"Error getting available tools: {str(e)}", exc_info=True)
        return {"tools": []}

async def init_mcp_client(force_reload: bool = False):
    """
    Initialize or reinitialize MCP client
    
    Args:
        force_reload: Whether to force reinitialization even if client exists
        
    Returns:
        MCP client context or None
    """
    global mcp_client_ctx

    # Return existing client if initialized and reload not forced
    if mcp_client_ctx and not force_reload:
        return mcp_client_ctx

    logger.info("Initializing MCP client...")
    
    try:
        # Get application settings
        settings = get_app_settings()
        
        # Get LLM service
        llm_service = LLMService()
        
        # Get provider and model from settings
        provider = settings.DEFAULT_LLM_PROVIDER
        
        # Select the default model based on provider
        if provider == "google":
            model = settings.DEFAULT_GOOGLE_MODEL 
        elif provider == "openai":
            model = settings.DEFAULT_OPENAI_MODEL
        elif provider == "anthropic":
            model = settings.DEFAULT_ANTHROPIC_MODEL
        elif provider == "nvidia":
            model = settings.DEFAULT_NVIDIA_MODEL
        else:
            model = settings.DEFAULT_OPENAI_MODEL
            
        logger.info(f"Initializing MCP client with provider: {provider}, model: {model}")
        
        # Get LLM
        llm = llm_service.get_provider(provider, model)
        
        # Load tool configuration
        config = load_mcp_config()
        
        # If no configuration, return None
        if not config:
            logger.warning("No MCP config found, using regular LLM")
            return None
            
        # Attempt to initialize client
        try:
            mcp_client_ctx = MultiServerMCPClient(config)
            logger.info("MCP client initialized successfully")
            return mcp_client_ctx
        except Exception as e:
            logger.error(f"Error initializing MCP client: {str(e)}")
            return None
    except Exception as e:
        logger.error(f"Error in init_mcp_client: {str(e)}", exc_info=True)
        return None 