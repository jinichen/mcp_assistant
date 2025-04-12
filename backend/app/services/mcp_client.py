"""
LangChain MCP Client - A client that integrates multiple tool servers
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional, Callable
import asyncio
import subprocess

from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

import httpx
from langchain.tools import Tool
from langchain.pydantic_v1 import BaseModel, Field
from functools import lru_cache
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class MCPClient:
    """
    MCP client responsible for loading tool configurations and invoking tools
    """
    def __init__(self, config_path: str):
        """
        Initialize MCP client
        
        Args:
            config_path: Path to the tool configuration file
        """
        self.config_path = config_path
        self.tools_config = {}
        self.processes = {}
        self._load_config()
        
    def _load_config(self):
        """Load tool configuration"""
        try:
            if not os.path.exists(self.config_path):
                # If the configuration file doesn't exist, create a default configuration
                default_config = {
                    "math": {
                        "command": "python",
                        "args": ["mcp_server/math/math_server.py"],
                        "transport": "stdio",
                        "description": "Solves mathematical expressions and equations"
                    },
                    "weather": {
                        "command": "python",
                        "args": ["mcp_server/weather/weather_server.py"],
                        "transport": "stdio",
                        "description": "Provides weather information for locations around the world"
                    },
                    "TestScenarioGenerator": {
                        "command": "python",
                        "args": ["mcp_server/TestScenarioGenerator/test_scenario_generator.py"],
                        "transport": "stdio",
                        "description": "Generates test scenarios, scripts, and data for testing APIs"
                    }
                }
                os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
                with open(self.config_path, 'w') as f:
                    json.dump(default_config, f, indent=2)
                
            with open(self.config_path, 'r') as f:
                self.tools_config = json.load(f)
                
            logger.info(f"Loaded MCP config: {self.tools_config}")
        except Exception as e:
            logger.error(f"Error loading MCP config: {e}")
            self.tools_config = {}
            
    def get_available_tools(self) -> List[str]:
        """Get a list of available tool IDs"""
        return list(self.tools_config.keys())
    
    def get_tool_info(self, tool_id: str) -> Dict[str, Any]:
        """Get tool information"""
        return self.tools_config.get(tool_id, {})
    
    async def invoke_tool(self, tool_id: str, query: str) -> str:
        """
        Invoke a specified tool
        
        Args:
            tool_id: Tool ID
            query: Query content
            
        Returns:
            Tool response result
        """
        if tool_id not in self.tools_config:
            raise ValueError(f"Tool '{tool_id}' not found in config")
        
        tool_config = self.tools_config[tool_id]
        transport = tool_config.get("transport")
        
        if transport == "stdio":
            return await self._invoke_stdio_tool(tool_id, tool_config, query)
        elif transport == "http":
            return await self._invoke_http_tool(tool_id, tool_config, query)
        else:
            raise ValueError(f"Unsupported transport '{transport}' for tool '{tool_id}'")
    
    async def _invoke_stdio_tool(self, tool_id: str, config: Dict[str, Any], query: str) -> str:
        """
        Invoke a tool using standard input/output
        
        Args:
            tool_id: Tool ID
            config: Tool configuration
            query: Query content
            
        Returns:
            Tool response result
        """
        process = self.processes.get(tool_id)
        if not process:
            logger.info(f"Starting process for tool '{tool_id}'")
            cmd = [config["command"]] + config.get("args", [])
            logger.info(f"Command: {' '.join(cmd)}")
            try:
                process = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdin=asyncio.subprocess.PIPE,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                self.processes[tool_id] = process
                logger.info(f"Process started with PID: {process.pid}")
            except Exception as e:
                logger.error(f"Failed to start process: {e}", exc_info=True)
                return f"Error: Could not start tool process: {str(e)}"
        
        try:
            # Send query to the tool process
            query_json = json.dumps({"query": query}) + "\n"
            logger.info(f"Sending query to tool: {query_json.strip()}")
            
            if process.stdin.is_closing():
                logger.error(f"Process stdin is closed, restarting process")
                # Try to close the current process
                try:
                    process.terminate()
                    await asyncio.wait_for(process.wait(), timeout=5.0)
                except:
                    pass
                
                # Restart the process
                del self.processes[tool_id]
                return await self._invoke_stdio_tool(tool_id, config, query)
            
            process.stdin.write(query_json.encode())
            await process.stdin.drain()
            
            # Read tool response with timeout
            try:
                response_line = await asyncio.wait_for(process.stdout.readline(), timeout=30.0)
                response_text = response_line.decode().strip()
                logger.info(f"Received response from tool: {response_text}")
                
                try:
                    response_json = json.loads(response_text)
                    result = response_json.get("result", "")
                    error = response_json.get("error")
                    
                    if error:
                        logger.error(f"Tool '{tool_id}' returned error: {error}")
                        return f"Error: {error}"
                    
                    return result
                except json.JSONDecodeError:
                    logger.error(f"Failed to parse JSON response from tool '{tool_id}': {response_text}")
                    return f"Error parsing tool response: {response_text}"
            except asyncio.TimeoutError:
                logger.error(f"Timeout waiting for response from tool '{tool_id}'")
                # Try to terminate the timed-out process
                try:
                    process.terminate()
                    await asyncio.wait_for(process.wait(), timeout=5.0)
                except:
                    pass
                
                # Remove from the process dictionary
                del self.processes[tool_id]
                return f"Error: Tool '{tool_id}' timed out after 30 seconds"
                
        except Exception as e:
            logger.error(f"Error invoking tool '{tool_id}': {e}", exc_info=True)
            return f"Error invoking tool: {str(e)}"
    
    async def _invoke_http_tool(self, tool_id: str, config: Dict[str, Any], query: str) -> str:
        """
        Invoke a tool using HTTP
        
        Args:
            tool_id: Tool ID
            config: Tool configuration
            query: Query content
            
        Returns:
            Tool response result
        """
        url = config.get("url")
        if not url:
            return f"Error: Missing URL for HTTP tool '{tool_id}'"
        
        headers = config.get("headers", {})
        headers.setdefault("Content-Type", "application/json")
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    json={"query": query},
                    headers=headers,
                    timeout=30.0
                )
                
                if response.status_code != 200:
                    logger.error(f"HTTP tool '{tool_id}' returned status code {response.status_code}")
                    return f"Error: HTTP tool returned status code {response.status_code}"
                
                try:
                    response_json = response.json()
                    result = response_json.get("result", "")
                    error = response_json.get("error")
                    
                    if error:
                        logger.error(f"HTTP tool '{tool_id}' returned error: {error}")
                        return f"Error: {error}"
                    
                    return result
                except json.JSONDecodeError:
                    logger.error(f"Failed to parse JSON response from HTTP tool '{tool_id}'")
                    return f"Error parsing HTTP tool response: {response.text}"
        except Exception as e:
            logger.error(f"Error invoking HTTP tool '{tool_id}': {e}", exc_info=True)
            return f"Error invoking HTTP tool: {str(e)}"
    
    async def start_servers(self):
        """Start all tool servers"""
        for tool_id, config in self.tools_config.items():
            if config.get("transport") == "stdio":
                await self.invoke_tool(tool_id, "ping")
    
    def get_tools(self) -> List[Tool]:
        """
        Get a list of LangChain-compatible tools
        
        Returns:
            List of LangChain Tool objects
        """
        tools = []
        
        for tool_id, config in self.tools_config.items():
            description = config.get("description", f"Tool {tool_id}")
            
            # Define a Pydantic model for the tool input
            class ToolInput(BaseModel):
                query: str = Field(description=f"Query for the {tool_id} tool")
            
            # Define an async function to invoke the tool
            async def _tool_func(query: str, _tool_id=tool_id):
                return await self.invoke_tool(_tool_id, query)
            
            # Define a sync wrapper for the async function
            def _sync_tool_func(query: str, _tool_id=tool_id):
                return asyncio.run(self.invoke_tool(_tool_id, query))
            
            # Create a LangChain Tool
            tool = Tool(
                name=tool_id,
                description=description,
                func=_sync_tool_func,
                args_schema=ToolInput,
                coroutine=_tool_func
            )
            
            tools.append(tool)
        
        return tools
    
    async def shutdown(self):
        """Shut down all tool processes"""
        for tool_id, process in self.processes.items():
            logger.info(f"Shutting down tool process '{tool_id}'")
            try:
                process.terminate()
                await asyncio.wait_for(process.wait(), timeout=5.0)
            except Exception as e:
                logger.error(f"Error shutting down tool process '{tool_id}': {e}", exc_info=True)

class MCPAssistant:
    """
    MCP assistant that integrates LLM and MCP tools
    """
    def __init__(self, config_path: str):
        """
        Initialize MCP assistant
        
        Args:
            config_path: Path to the tool configuration file
        """
        self.config_path = config_path
        self.config = self._load_config()
        self.llm = None
        self.mcp_client = None
        self.tools = []
        self.agent = None
        
    def _load_config(self) -> Dict[str, Any]:
        """
        Load configuration
        
        Returns:
            Configuration dictionary
        """
        # Default configuration
        default_config = {
            "llm": {
                "provider": "openai",
                "model": "gpt-3.5-turbo-1106",
                "temperature": 0.7
            },
            "system_message": """You are an AI assistant with access to various tools.
You can use these tools to help answer questions and solve problems.
Always think step-by-step and use the appropriate tool when needed.
If you don't know something or can't find the answer, be honest about it."""
        }
        
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                    # Merge with default config for missing keys
                    for key, value in default_config.items():
                        if key not in config:
                            config[key] = value
                    return config
            else:
                # Save default config
                os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
                with open(self.config_path, 'w') as f:
                    json.dump(default_config, f, indent=2)
                return default_config
        except Exception as e:
            logger.error(f"Error loading config: {e}", exc_info=True)
            return default_config
    
    async def initialize(self):
        """Initialize the assistant"""
        from app.services.llm_service import LLMService
        
        # Initialize MCP client
        mcp_tools_config = os.path.join(os.path.dirname(self.config_path), "mcp_tools.json")
        self.mcp_client = MCPClient(mcp_tools_config)
        
        # Start tool servers
        await self.mcp_client.start_servers()
        
        # Get tools
        self.tools = self.mcp_client.get_tools()
        
        # Initialize LLM
        llm_config = self.config.get("llm", {})
        provider = llm_config.get("provider")
        model = llm_config.get("model")
        
        self.llm = LLMService.get_provider(provider, model)
        
        # Create the prompt template
        prompt = ChatPromptTemplate.from_messages([
            ("system", self.config.get("system_message", "")),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        
        # Create the agent
        self.agent = create_react_agent(self.llm, self.tools, prompt)
        
        logger.info("MCP Assistant initialized")
        
    async def process_message(self, message: str) -> str:
        """
        Process a user message
        
        Args:
            message: User message
            
        Returns:
            Assistant response
        """
        if not self.agent:
            await self.initialize()
        
        try:
            # Create state with empty history
            state = {
                "history": [],
                "input": message,
            }
            
            # Log the message for debugging
            logger.info(f"Processing message: {message}")
            
            # Execute the agent
            response = self.agent.invoke(state)
            
            # Extract the assistant's response
            if isinstance(response, dict) and "output" in response:
                result = response["output"]
            elif isinstance(response, list):
                # Look for the last AIMessage
                for msg in reversed(response):
                    if isinstance(msg, AIMessage):
                        result = msg.content
                        break
                else:
                    result = "I'm sorry, I couldn't process that request."
            else:
                result = str(response)
            
            # Log the response for debugging
            logger.info(f"Generated response: {result}")
            
            return result
        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=True)
            return f"I'm sorry, an error occurred: {str(e)}"
    
    async def shutdown(self):
        """Shut down the assistant"""
        if self.mcp_client:
            await self.mcp_client.shutdown()
        logger.info("MCP Assistant shut down")

@lru_cache()
def get_mcp_assistant():
    """
    Get a singleton instance of the MCP assistant
    
    Returns:
        MCPAssistant instance
    """
    config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "config", "mcp_assistant.json")
    return MCPAssistant(config_path) 