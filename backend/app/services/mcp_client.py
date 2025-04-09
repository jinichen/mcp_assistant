"""
LangChain MCP Client - A client that integrates multiple tool servers
Implements standard MCP protocol for LangChain integration
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

from app.services.llm_service import LLMService
from app.core.config import get_app_settings

import httpx
from langchain.tools import Tool
from langchain.pydantic_v1 import BaseModel, Field

logger = logging.getLogger(__name__)

settings = get_app_settings()

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
                        "args": ["app/tools/math_server.py"],
                        "transport": "stdio",
                        "description": "Solves mathematical expressions and equations"
                    },
                    "weather": {
                        "command": "python",
                        "args": ["app/tools/weather_server.py"],
                        "transport": "stdio",
                        "description": "Provides weather information for locations around the world"
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
                response_line = await asyncio.wait_for(process.stdout.readline(), timeout=10.0)
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
                return f"Error: Tool '{tool_id}' timed out after 10 seconds"
                
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
            raise ValueError(f"Missing 'url' in config for HTTP tool '{tool_id}'")
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    json={"query": query},
                    timeout=30.0
                )
                
                if response.status_code != 200:
                    logger.error(f"HTTP tool '{tool_id}' returned status {response.status_code}: {response.text}")
                    return f"Error: HTTP status {response.status_code}"
                
                response_json = response.json()
                result = response_json.get("result", "")
                error = response_json.get("error")
                
                if error:
                    logger.error(f"Tool '{tool_id}' returned error: {error}")
                    return f"Error: {error}"
                
                return result
                
        except Exception as e:
            logger.error(f"Error invoking HTTP tool '{tool_id}': {e}")
            return f"Error invoking tool: {str(e)}"
            
    async def start_servers(self):
        """Start all tool servers"""
        # Since tools are started on-demand when invoked, only perform basic checks here
        for tool_id, config in self.tools_config.items():
            if config.get("transport") == "stdio" and config.get("autostart", True):
                # Verify that the tool script exists
                if "args" in config and len(config["args"]) > 0:
                    script_path = config["args"][0]
                    if not os.path.isabs(script_path):
                        script_path = os.path.join(os.getcwd(), script_path)
                    
                    if not os.path.exists(script_path):
                        logger.warning(f"Tool script for '{tool_id}' not found: {script_path}")
    
    def get_tools(self) -> List[Tool]:
        """
        Get all available tools in LangChain tool format
        
        Returns:
            List of LangChain tools
        """
        tools = []
        
        for tool_id, config in self.tools_config.items():
            description = config.get("description", f"Tool for {tool_id}")
            
            # Create dynamic parameter model
            class ToolInput(BaseModel):
                query: str = Field(description=f"Query for the {tool_id} tool")
            
            # Create async callback function
            async def _tool_func(query: str, _tool_id=tool_id):
                return await self.invoke_tool(_tool_id, query)
            
            # Create synchronous wrapper function
            def _sync_tool_func(query: str, _tool_id=tool_id):
                return asyncio.run(self.invoke_tool(_tool_id, query))
            
            # Create LangChain tool
            tool = Tool(
                name=tool_id,
                description=description,
                func=_sync_tool_func,
                args_schema=ToolInput
            )
            
            tools.append(tool)
        
        return tools
    
    async def shutdown(self):
        """Close all processes"""
        for tool_id, process in self.processes.items():
            logger.info(f"Shutting down process for tool '{tool_id}'")
            try:
                process.terminate()
                await process.wait()
            except Exception as e:
                logger.error(f"Error terminating process for tool '{tool_id}': {e}")
                
        self.processes = {}

class MCPAssistant:
    """Chat assistant based on MCP tools and LangChain React Agent"""
    
    def __init__(self, config_path: str):
        """Initialize MCP assistant
        
        Args:
            config_path: Path to MCP tool configuration file
        """
        self.config_path = config_path
        self.mcp_config = self._load_config()
        self.mcp_client = None
        self.agent = None
        self.is_initialized = False
        
    def _load_config(self) -> Dict[str, Any]:
        """Load MCP tool configuration"""
        try:
            config_dir = os.path.dirname(self.config_path)
            if not os.path.exists(config_dir):
                os.makedirs(config_dir)
                
            # Check if tool scripts exist
            math_path = os.path.join(os.getcwd(), "app/tools/math_server.py")
            weather_path = os.path.join(os.getcwd(), "app/tools/weather_server.py")
            
            logger.info(f"Checking math script: {math_path}, exists: {os.path.exists(math_path)}")
            logger.info(f"Checking weather script: {weather_path}, exists: {os.path.exists(weather_path)}")
            logger.info(f"Current working directory: {os.getcwd()}")
            
            if not os.path.exists(self.config_path):
                # If the configuration file doesn't exist, create a default configuration
                default_config = {
                    "math": {
                        "command": "python",
                        "args": ["app/tools/math_server.py"],
                        "transport": "stdio"
                    },
                    "weather": {
                        "url": "http://localhost:8080/weather",
                        "transport": "http"
                    }
                }
                with open(self.config_path, 'w') as f:
                    json.dump(default_config, f, indent=2)
                    
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading MCP configuration: {e}")
            return {}
    
    async def initialize(self):
        """Initialize MCP client and Agent"""
        if self.is_initialized:
            return
        
        try:
            # Create MultiServerMCPClient client
            logger.info(f"Initializing MCP client with config: {self.mcp_config}")
            self.mcp_client = MultiServerMCPClient(self.mcp_config)
            await self.mcp_client.__aenter__()
            
            # Check if tools are loaded
            tools = self.mcp_client.get_tools()
            if not tools:
                logger.warning("No MCP tools were loaded. Check your configuration.")
            else:
                logger.info(f"Loaded {len(tools)} MCP tools: {[tool.name for tool in tools]}")
            
            # Tool calls must use a supported model - forcing OpenAI here
            logger.info("Using OpenAI model for tool support")
            model = ChatOpenAI(
                api_key=settings.OPENAI_API_KEY,
                base_url=settings.OPENAI_BASE_URL,
                model="gpt-4", # Use a model that definitely supports tool calls
                temperature=0,
            )
            
            # Create ReAct agent for answering user questions
            logger.info("Creating ReAct agent")
            self.agent = create_react_agent(model, tools)
            
            self.is_initialized = True
            logger.info("MCP Assistant initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing MCP Assistant: {e}", exc_info=True)
            if self.mcp_client:
                await self.mcp_client.__aexit__(None, None, None)
    
    async def process_message(self, message: str) -> str:
        """Process user message and return response
        
        Args:
            message: User message content
            
        Returns:
            Assistant response content
        """
        if not self.is_initialized:
            await self.initialize()
        
        try:
            logger.info(f"Processing message with MCP Assistant: '{message}'")
            logger.info(f"Available tools: {[tool.name for tool in self.mcp_client.get_tools()]}")
            
            # Use ReAct agent to process user message
            response = await self.agent.ainvoke({"messages": [HumanMessage(content=message)]})
            
            logger.info(f"Agent response type: {type(response)}")
            logger.info(f"Agent response: {response}")
            
            # Extract response content
            if hasattr(response, "messages") and response.messages:
                return response.messages[-1].content
            
            # If it's a dictionary format, try to extract the content field
            if isinstance(response, dict) and "messages" in response:
                messages = response["messages"]
                if messages and isinstance(messages, list) and len(messages) > 0:
                    return messages[-1].content
            
            # If unable to parse the response, return a friendly error message
            return "Sorry, I couldn't process your request."
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return f"Error processing message: {str(e)}"
    
    async def shutdown(self):
        """Close MCP client and resources"""
        if self.mcp_client:
            try:
                await self.mcp_client.__aexit__(None, None, None)
                self.is_initialized = False
                logger.info("MCP Assistant shutdown complete")
            except Exception as e:
                logger.error(f"Error shutting down MCP client: {e}")

# Singleton instance
_assistant = None

def get_mcp_assistant():
    """Get singleton instance of MCP assistant"""
    global _assistant
    if _assistant is None:
        config_path = os.path.join("app", "config", "mcp_tools.json")
        _assistant = MCPAssistant(config_path)
    return _assistant 