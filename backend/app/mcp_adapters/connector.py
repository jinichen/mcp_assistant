import asyncio
import logging
import subprocess
import os
import signal
import traceback
import json
import inspect
from typing import Dict, List, Optional, Any, Union

from mcp import ClientSession
from langchain_mcp_adapters.tools import load_mcp_tools
from langchain.tools import BaseTool

# Configure detailed logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class MCPServiceConnector:
    """MCP service connector, responsible for connecting to MCP services and loading tools"""
    
    def __init__(self, service_name: str, transport: str, **kwargs):
        """
        Initialize MCP service connector
        
        Args:
            service_name: service name
            transport: transport type ('stdio' or 'sse')
            **kwargs: other connection parameters
        """
        self.service_name = service_name
        self.transport = transport.lower()
        self.connection_params = kwargs
        self.tools: List[BaseTool] = []
        self.client_session: Optional[ClientSession] = None
        self.process = None
        self.initialized = False
    
    async def connect(self) -> bool:
        """
        Connect to MCP service
        
        Returns:
            True if connection is successful, False otherwise
        """
        if self.initialized:
            return True
            
        try:
            if self.transport == "stdio":
                command = self.connection_params.get("command")
                args = self.connection_params.get("args", [])
                
                logger.info(f"Connecting to {self.service_name} via stdio: {command} {' '.join(args)}")
                
                try:
                    # Create process directly
                    process = subprocess.Popen(
                        [command] + args,
                        stdin=subprocess.PIPE,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        universal_newlines=False,
                        bufsize=0
                    )
                    self.process = process
                    
                    # Check if process has started
                    if process.poll() is not None:
                        return_code = process.poll()
                        stderr_output = process.stderr.read()
                        logger.error(f"Process failed to start. Return code: {return_code}, stderr: {stderr_output}")
                        return False
                    
                    # Create custom read/write functions
                    async def read():
                        loop = asyncio.get_running_loop()
                        try:
                            data = await loop.run_in_executor(None, process.stdout.readline)
                            if data:
                                logger.debug(f"Read data: {data}")
                            return data
                        except Exception as e:
                            logger.error(f"Error reading from process: {e}")
                            raise
                    
                    class Writer:
                        def __init__(self, process):
                            self.process = process
                        
                        async def send(self, data):
                            try:
                                # Special handling for JSONRPCMessage type
                                if data.__class__.__name__ == 'JSONRPCMessage':
                                    # Get root object
                                    root = data.root
                                    
                                    # Build JSON object
                                    json_obj = {
                                        "jsonrpc": root.jsonrpc,
                                        "id": root.id
                                    }
                                    
                                    # Add method and params (if exists)
                                    if hasattr(root, 'method'):
                                        json_obj["method"] = root.method
                                        if hasattr(root, 'params'):
                                            json_obj["params"] = root.params
                                    
                                    # Add result (if exists)
                                    if hasattr(root, 'result'):
                                        json_obj["result"] = root.result
                                    
                                    # Add error (if exists)
                                    if hasattr(root, 'error'):
                                        json_obj["error"] = root.error
                                    
                                    # Convert to JSON string and add newline
                                    json_str = json.dumps(json_obj)
                                    bytes_data = (json_str + '\n').encode('utf-8')
                                
                                elif isinstance(data, bytes):
                                    # If already bytes, ensure newline
                                    if not data.endswith(b'\n'):
                                        bytes_data = data + b'\n'
                                    else:
                                        bytes_data = data
                                elif isinstance(data, str):
                                    # If string, encode to bytes
                                    bytes_data = (data + '\n').encode('utf-8')
                                else:
                                    # Try to convert directly to string
                                    try:
                                        json_str = str(data)
                                        bytes_data = (json_str + '\n').encode('utf-8')
                                    except:
                                        raise ValueError(f"Cannot serialize data of type {type(data)}")
                                
                                logger.debug(f"Sending data: {bytes_data}")
                                # Write data
                                self.process.stdin.write(bytes_data)
                                self.process.stdin.flush()
                            except Exception as e:
                                logger.error(f"Error writing to process: {e}")
                                logger.error(f"Data type: {type(data)}")
                                if hasattr(data, '__dict__'):
                                    logger.error(f"Data dict: {data.__dict__}")
                                raise
                    
                    write = Writer(process)
                    
                    # Create session
                    self.client_session = ClientSession(read, write)
                    try:
                        # Set timeout
                        await asyncio.wait_for(self.client_session.initialize(), timeout=10.0)
                    except asyncio.TimeoutError:
                        logger.error(f"Connection to {self.service_name} timed out")
                        # Read error output
                        if self.process and self.process.stderr:
                            stderr = self.process.stderr.read()
                            if stderr:
                                logger.error(f"Process stderr: {stderr.decode('utf-8', errors='replace')}")
                        return False
                    except Exception as e:
                        logger.error(f"Failed to initialize client session: {e}")
                        logger.error(traceback.format_exc())
                        return False
                    
                except Exception as e:
                    logger.error(f"Error setting up stdio connection: {e}")
                    logger.error(traceback.format_exc())
                    return False
                
            elif self.transport == "sse":
                url = self.connection_params.get("url")
                headers = self.connection_params.get("headers", {})
                
                logger.info(f"Connecting to {self.service_name} via SSE: {url}")
                
                try:
                    # Import SSE client
                    from mcp.client.sse import sse_client
                    client = sse_client(url, headers)
                    read = client.aread
                    write = client
                    
                    # Create session
                    self.client_session = ClientSession(read, write)
                    try:
                        # Set timeout
                        await asyncio.wait_for(self.client_session.initialize(), timeout=10.0)
                    except asyncio.TimeoutError:
                        logger.error(f"Connection to {self.service_name} via SSE timed out")
                        return False
                    
                except Exception as e:
                    logger.error(f"Error setting up SSE connection: {e}")
                    logger.error(traceback.format_exc())
                    return False
            
            else:
                logger.error(f"Unsupported transport: {self.transport}")
                return False
            
            # Load tools
            try:
                await self.load_tools()
                self.initialized = True
                return True
            except Exception as e:
                logger.error(f"Failed to load tools: {e}")
                logger.error(traceback.format_exc())
                return False
            
        except Exception as e:
            logger.error(f"Failed to connect to {self.service_name}: {e}")
            logger.error(traceback.format_exc())
            # Ensure resources are cleaned up
            if self.process:
                try:
                    self.process.terminate()
                    self.process = None
                except:
                    pass
            return False
    
    async def load_tools(self) -> List[BaseTool]:
        """
        Load tools provided by MCP service
        
        Returns:
            List of tools
        """
        if not self.client_session:
            raise ValueError("Not connected to MCP service")
        
        try:
            self.tools = await load_mcp_tools(self.client_session)
            logger.info(f"Loaded {len(self.tools)} tools from {self.service_name}")
            
            # Add service name prefix to tools
            for tool in self.tools:
                tool.name = f"{self.service_name.lower()}_{tool.name}"
                
            return self.tools
        except Exception as e:
            logger.error(f"Failed to load tools from {self.service_name}: {e}")
            logger.error(traceback.format_exc())
            return []
    
    async def disconnect(self):
        """Disconnect from MCP service"""
        if self.client_session:
            try:
                await self.client_session.close()
                self.client_session = None
                
                # If stdio connection, terminate process
                if self.process:
                    try:
                        self.process.terminate()
                        await asyncio.sleep(0.5)  # Give process some time to clean up
                        if self.process.poll() is None:  # If process is still running
                            self.process.kill()
                    except:
                        pass  # Process may already be terminated
                    
                    self.process = None
                
                self.initialized = False
                logger.info(f"Disconnected from {self.service_name}")
            except Exception as e:
                logger.error(f"Error disconnecting from {self.service_name}: {e}")
    
    def get_tools(self) -> List[BaseTool]:
        """Get list of loaded tools"""
        return self.tools
    
    async def __aenter__(self):
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.disconnect()