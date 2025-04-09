from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.db.session import get_db
from app.schemas.conversation import ConversationCreate, ConversationResponse, ConversationUpdate
from app.db.repositories.conversation_repository import ConversationRepository
from app.db.repositories.message_repository import MessageRepository
from app.core.deps import get_current_active_user
from app.models.user import User

router = APIRouter()

@router.post("", response_model=ConversationResponse)
async def create_conversation(
    conversation: ConversationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Create a new conversation
    """
    conversation_repo = ConversationRepository(db)
    db_conversation = conversation_repo.create_conversation(conversation, current_user.id)
    return db_conversation

@router.get("", response_model=List[ConversationResponse])
async def get_conversations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get all conversations for the current user
    """
    conversation_repo = ConversationRepository(db)
    conversations = conversation_repo.get_conversations_by_user_id(current_user.id)
    return conversations

@router.get("/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get detailed information for a specific conversation
    """
    conversation_repo = ConversationRepository(db)
    conversation = conversation_repo.get_conversation(conversation_id, current_user.id)
    
    if not conversation:
        raise HTTPException(status_code=404, detail=f"Conversation with id {conversation_id} not found")
    
    return conversation

@router.put("/{conversation_id}", response_model=ConversationResponse)
async def update_conversation(
    conversation_id: str,
    update_data: ConversationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Update conversation information
    """
    conversation_repo = ConversationRepository(db)
    updated_conversation = conversation_repo.update_conversation(conversation_id, update_data, current_user.id)
    
    if not updated_conversation:
        raise HTTPException(status_code=404, detail=f"Conversation with id {conversation_id} not found")
    
    return updated_conversation

@router.delete("/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Delete a conversation and all its messages
    """
    conversation_repo = ConversationRepository(db)
    message_repo = MessageRepository(db)
    
    # First delete all messages associated with the conversation
    message_repo.delete_conversation(conversation_id, current_user.id)
    
    # Then delete the conversation itself
    success = conversation_repo.delete_conversation(conversation_id, current_user.id)
    
    if not success:
        raise HTTPException(status_code=404, detail=f"Conversation with id {conversation_id} not found")
    
    return {"status": "success", "message": f"Conversation {conversation_id} deleted"} 