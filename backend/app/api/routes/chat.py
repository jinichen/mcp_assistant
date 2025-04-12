from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional, Dict
import json

from app.db.session import get_db
from app.schemas.message import ChatRequest, ChatResponse, MessageBase, MessageCreate
from app.db.repositories.message_repository import MessageRepository
from app.db.repositories.conversation_repository import ConversationRepository
from app.services.llm_service import LLMService
from app.core.config import get_app_settings
from app.core.deps import get_current_active_user, get_current_user
from app.models.user import User
from app.schemas.conversation import ConversationUpdate
from langchain.schema import HumanMessage, AIMessage, SystemMessage
import logging

router = APIRouter()
settings = get_app_settings()
logger = logging.getLogger(__name__)

def get_conversation_repo(db: Session = Depends(get_db)) -> ConversationRepository:
    return ConversationRepository(db)

def get_message_repo(db: Session = Depends(get_db)) -> MessageRepository:
    return MessageRepository(db)

@router.post("/complete", response_model=ChatResponse)
async def complete_chat(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        # 创建存储库
        conversation_repo = ConversationRepository(db)
        message_repo = MessageRepository(db)
        
        # 获取请求内容
        provider = settings.DEFAULT_LLM_PROVIDER
        model = None
        messages = request.messages
        
        if not messages or len(messages) == 0:
            raise HTTPException(status_code=400, detail="No messages provided")
        
        # 从LLM提供商获取回复
        response = await LLMService.generate_response(
            messages=messages,
            provider=provider,
            model=model
        )
        
        # 保存对话记录
        if request.conversation_id:
            # 添加用户消息
            user_message = MessageCreate(
                conversation_id=request.conversation_id,
                role="user",
                content=messages[-1].content,
                provider=provider,
                user_id=current_user.id
            )
            message_repo.create_message(user_message)
            
            # 添加助手消息
            assistant_message = MessageCreate(
                conversation_id=request.conversation_id,
                role="assistant",
                content=response,
                provider=provider,
                user_id=current_user.id
            )
            message_repo.create_message(assistant_message)
            
            # 更新对话的最后修改时间
            update_data = ConversationUpdate(title=None, provider=None, model=None)
            conversation_repo.update_conversation(
                request.conversation_id,
                update_data,
                current_user.id
            )
        
        # 返回响应
        return ChatResponse(
            conversation_id=request.conversation_id,
            message=MessageBase(role="assistant", content=response),
            provider=provider
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/conversations/{conversation_id}", response_model=List[MessageBase])
async def get_conversation(
    conversation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Retrieve all messages for a specific conversation.
    """
    # Verify conversation exists
    conversation_repo = ConversationRepository(db)
    conversation = conversation_repo.get_conversation(conversation_id, current_user.id)
    if not conversation:
        raise HTTPException(status_code=404, detail=f"Conversation with id {conversation_id} not found")
    
    message_repo = MessageRepository(db)
    messages = message_repo.get_messages_by_conversation_id(conversation_id, current_user.id)
    return messages

@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Delete all messages for a specific conversation.
    This is only for backward compatibility, please use DELETE /conversations/{conversation_id} instead.
    """
    # Verify conversation exists
    conversation_repo = ConversationRepository(db)
    conversation = conversation_repo.get_conversation(conversation_id, current_user.id)
    if not conversation:
        raise HTTPException(status_code=404, detail=f"Conversation with id {conversation_id} not found")
    
    message_repo = MessageRepository(db)
    success = message_repo.delete_conversation(conversation_id, current_user.id)
    
    if not success:
        raise HTTPException(status_code=404, detail=f"Messages for conversation {conversation_id} not found")
    
    # Delete the conversation itself
    conversation_repo.delete_conversation(conversation_id, current_user.id)
    
    return {"status": "success", "message": f"Conversation {conversation_id} deleted"}

@router.post("/stream", response_class=StreamingResponse)
async def stream_chat(request: ChatRequest, current_user: User = Depends(get_current_user)):
    """Stream chat completion from LLM"""
    if not request.messages:
        raise HTTPException(status_code=400, detail="No messages provided")
    
    # 获取最新用户消息
    user_message = request.messages[-1].content if request.messages else ""
    logger.info(f"Processing user message: {user_message[:100]}...")
    
    # 默认使用标准LLM处理
    try:
        # 获取LLM提供商配置
        provider = settings.DEFAULT_LLM_PROVIDER
        model = None
        
        logger.info(f"Using standard LLM directly: {provider}, model: {model or 'default'}")
        
        # 转换消息为LangChain格式
        messages = []
        for msg in request.messages:
            if msg.role == "user":
                messages.append(HumanMessage(content=msg.content))
            elif msg.role == "assistant":
                messages.append(AIMessage(content=msg.content))
            else:
                messages.append(SystemMessage(content=msg.content))
        
        # 创建LLM服务
        llm_service = LLMService()
        
        # 直接返回LLM的流式响应
        return StreamingResponse(
            llm_service.generate_response_stream(messages, provider, model),
            media_type="text/event-stream"
        )
    except Exception as e:
        logger.error(f"Error in standard LLM processing: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))