#!/usr/bin/env python3
"""
Independent MCP server, specifically for handling tool call requests
using LangChain MCP adapters
"""
import logging
import os
import json
from typing import List, Optional, Dict, Any

import uvicorn
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from fastapi.responses import StreamingResponse
from langchain_core.runnables.config import RunnableConfig
from langchain_core.messages import HumanMessage, AIMessage

from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI
from app.services.llm_service import LLMService
from app.core.config import get_app_settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Create FastAPI application
app = FastAPI(title="MCP Tools API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, this should be restricted to specific domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MCP client and agent
mcp_client = None
mcp_agent = None

# Get application settings
settings = get_app_settings()

# Request and response models
class Message(BaseModel):
    role: str
    content: str

class MCPChatRequest(BaseModel):
    messages: List[Message]

class ToolInfo(BaseModel):
    id: str
    name: str
    description: str
    transport: str

class ToolInfoResponse(BaseModel):
    tools: List[ToolInfo]

class ChatResponse(BaseModel):
    message: str
    tool_info: Optional[Dict[str, Any]] = None

def load_mcp_config():
    """Load MCP tool configuration from JSON file"""
    config_path = os.path.join(os.getcwd(), "app/config/mcp_tools.json")
    if not os.path.exists(config_path):
        logger.warning(f"MCP config file not found at {config_path}")
        # Create basic default config
        config = {
            "math": {
                "command": "python",
                "args": [os.path.join(os.getcwd(), "app/tools/math/math_server.py")],
                "transport": "stdio",
                "description": "Solves mathematical expressions and equations"
            }
        }
    else:
        with open(config_path, 'r') as f:
            config = json.load(f)
            
        # Update paths to be absolute
        for tool_id, tool_config in config.items():
            if "args" in tool_config and len(tool_config["args"]) > 0:
                # If path is relative, make it absolute
                if not os.path.isabs(tool_config["args"][0]):
                    tool_config["args"][0] = os.path.join(os.getcwd(), tool_config["args"][0])
    
    logger.info(f"Loaded MCP config: {config}")
    return config

@app.on_event("startup")
async def startup_event():
    """Initialize MCP client when server starts"""
    global mcp_client, mcp_agent
    try:
        logger.info("Starting MCP assistant initialization")
        
        # Load tool configuration
        mcp_config = load_mcp_config()
        
        # Report tool paths
        for tool_id, config in mcp_config.items():
            tool_path = config["args"][0] if "args" in config and len(config["args"]) > 0 else None
            if tool_path:
                logger.info(f"Tool '{tool_id}' path: {tool_path}, exists: {os.path.exists(tool_path)}")
        
        logger.info(f"Current working directory: {os.getcwd()}")
        
        # Initialize MCP client
        mcp_client = MultiServerMCPClient(mcp_config)
        
        # Initialize language model for the agent
        model_name = settings.DEFAULT_OPENAI_MODEL
        if settings.DEFAULT_LLM_PROVIDER == "google":
            from langchain_google_genai import ChatGoogleGenerativeAI
            # 获取模型名称
            google_model = settings.DEFAULT_GOOGLE_MODEL or "gemini-1.5-pro"
            # 移除可能存在的"models/"前缀，因为langchain_google_genai会自动添加
            if google_model.startswith("models/"):
                google_model = google_model[7:]
            
            model = ChatGoogleGenerativeAI(
                model=google_model,
                temperature=0.7,
                google_api_key=settings.GOOGLE_API_KEY
            )
        else:  # Default to OpenAI
            model = ChatOpenAI(
                model=model_name,
                temperature=0.7,
                api_key=settings.OPENAI_API_KEY,
                base_url=settings.OPENAI_BASE_URL
            )
        
        # Initialize the agent with tools from MCP client
        mcp_agent = create_react_agent(model, mcp_client.get_tools())
        
        logger.info("MCP assistant initialization completed successfully")
    except Exception as e:
        logger.error(f"Error initializing MCP assistant: {str(e)}", exc_info=True)
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources when server shuts down"""
    global mcp_client
    if mcp_client:
        # MultiServerMCPClient doesn't have aclose method, it's an async context manager
        # We can just log shutdown without trying to close it
        logger.info("MCP assistant shutdown completed")

@app.get("/")
async def root():
    """Root route, returns server status"""
    return {"status": "MCP Tools API is running"}

@app.get("/api/v1/mcp/tools", response_model=ToolInfoResponse)
async def list_tools():
    """List all available MCP tools"""
    global mcp_client
    if not mcp_client:
        raise HTTPException(status_code=500, detail="MCP client not initialized")
    
    try:
        tools = mcp_client.get_tools()
        tool_infos = []
        
        for tool in tools:
            tool_infos.append(ToolInfo(
                id=tool.name,
                name=tool.name.capitalize(),
                description=tool.description,
                transport="mcp"
            ))
        
        return ToolInfoResponse(tools=tool_infos)
    except Exception as e:
        logger.error(f"Error listing tools: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to list tools: {str(e)}")

@app.post("/api/v1/mcp/complete", response_model=ChatResponse)
async def complete_chat(request: MCPChatRequest):
    """Process chat requests using the React agent with MCP tools"""
    global mcp_agent
    if not mcp_agent:
        raise HTTPException(status_code=500, detail="MCP agent not initialized")
    
    # Check if messages are empty
    if not request.messages or len(request.messages) == 0:
        raise HTTPException(status_code=400, detail="No messages provided")
    
    # Get the user message
    user_message = request.messages[-1].content
    if not user_message or user_message.strip() == "":
        raise HTTPException(status_code=400, detail="Empty user message")
    
    try:
        logger.info(f"Processing chat request with MCP agent")
        logger.info(f"User message: {user_message}")
        
        # Convert messages to the format expected by the agent
        input_messages = []
        for msg in request.messages:
            if msg.role == "user":
                input_messages.append({"type": "human", "content": msg.content})
            elif msg.role == "assistant":
                input_messages.append({"type": "ai", "content": msg.content})
        
        # Invoke the agent with the message
        response = await mcp_agent.ainvoke({"messages": input_messages})
        
        # Extract the response content
        result = ""
        if hasattr(response, 'content'):
            # Direct LangChain message object
            result = response.content
        elif isinstance(response, dict):
            if "messages" in response:
                # Get the last AI message from array
                for msg in reversed(response["messages"]):
                    if isinstance(msg, dict) and msg.get("type") == "ai":
                        result = msg.get("content", "")
                        break
                    elif hasattr(msg, "type") and msg.type == "ai":
                        result = msg.content
                        break
                else:
                    result = "No response generated"
            else:
                # Try to extract content from other response formats
                result = response.get("output", str(response))
        else:
            result = str(response)
        
        logger.info(f"Agent response: {result[:100]}...")
        
        # 除去可能的标签和引号
        clean_result = result
        if '<think>' in clean_result and '</think>' in clean_result:
            think_start = clean_result.find('<think>')
            think_end = clean_result.find('</think>') + len('</think>')
            clean_result = clean_result[:think_start] + clean_result[think_end:]
            clean_result = clean_result.strip()
        
        # 修正错误的换行符
        clean_result = clean_result.replace('/n', '\n')
        
        # Return only clean content
        return ChatResponse(
            message=clean_result,
            tool_info={"agent": "react_agent"}
        )
    except Exception as e:
        logger.error(f"Error processing chat request: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to process chat request: {str(e)}")

@app.post("/api/v1/mcp/stream")
async def stream_chat(request: MCPChatRequest):
    """使用React代理处理流式聊天请求"""
    global mcp_agent
    if not mcp_agent:
        raise HTTPException(status_code=500, detail="MCP agent not initialized")
    
    # 检查消息是否为空
    if not request.messages or len(request.messages) == 0:
        raise HTTPException(status_code=400, detail="No messages provided")
    
    # 获取用户消息
    user_message = request.messages[-1].content
    if not user_message or user_message.strip() == "":
        raise HTTPException(status_code=400, detail="Empty user message")
    
    async def generate():
        try:
            logger.info(f"Processing streaming chat request with MCP agent")
            logger.info(f"User message: {user_message}")
            
            # 转换为代理期望的格式
            input_messages = []
            for msg in request.messages:
                if msg.role == "user":
                    input_messages.append({"type": "human", "content": msg.content})
                elif msg.role == "assistant":
                    input_messages.append({"type": "ai", "content": msg.content})
            
            # 准备流式配置
            config = RunnableConfig(
                callbacks=None,
                tags=["mcp", "streaming"],
            )
            
            # 使用流式接口调用代理
            async for chunk in mcp_agent.astream({"messages": input_messages}, config=config):
                # 提取块内容
                result = ""
                if hasattr(chunk, 'content'):
                    result = chunk.content
                elif isinstance(chunk, dict):
                    # Handle different dict formats
                    if "messages" in chunk:
                        # Get the last message
                        messages = chunk["messages"]
                        if messages and len(messages) > 0:
                            last_msg = messages[-1]
                            if isinstance(last_msg, dict) and "content" in last_msg:
                                result = last_msg["content"]
                            elif hasattr(last_msg, "content"):
                                result = last_msg.content
                            else:
                                result = str(last_msg)
                        else:
                            result = ""
                    elif "content" in chunk:
                        result = chunk["content"]
                    elif "output" in chunk:
                        result = chunk["output"]
                    else:
                        result = str(chunk)
                else:
                    result = str(chunk)
                
                # 清理结果内容
                clean_result = result
                
                # 清理思考标签
                if '<think>' in clean_result:
                    think_parts = clean_result.split('<think>')
                    for i in range(1, len(think_parts)):
                        if '</think>' in think_parts[i]:
                            think_parts[i] = think_parts[i].split('</think>', 1)[1]
                    clean_result = ''.join(think_parts)
                
                # 修正错误的换行符
                clean_result = clean_result.replace('/n', '\n')
                
                # 发送干净的内容块
                if clean_result:
                    yield f"data: {json.dumps({'content': clean_result})}\n\n"
            
            # 发送结束事件
            yield "data: [DONE]\n\n"
        except Exception as e:
            logger.error(f"Error in streaming chat: {str(e)}", exc_info=True)
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
            yield "data: [DONE]\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream"
        }
    )

# If this file is run directly, start the server
if __name__ == "__main__":
    uvicorn.run("mcp_server:app", host="0.0.0.0", port=8001, reload=True) 