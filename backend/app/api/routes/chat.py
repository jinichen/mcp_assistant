from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
import traceback

from app.db.session import get_db
from app.schemas.message import ChatRequest, ChatResponse, MessageBase, MessageCreate
from app.db.repositories.message_repository import MessageRepository
from app.db.repositories.conversation_repository import ConversationRepository
from app.services.llm_service import LLMService
from app.core.config import get_app_settings
from app.core.deps import get_current_active_user
from app.models.user import User
from app.schemas.conversation import ConversationUpdate

router = APIRouter()
settings = get_app_settings()

@router.post("/complete", response_model=ChatResponse)
async def chat_completion(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Generate a chat completion response using the provider and model associated with the conversation.
    """
    try:
        message_repo = MessageRepository(db)
        conversation_repo = ConversationRepository(db)
        
        # Print request information
        print(f"Processing chat request for conversation: {request.conversation_id}")
        print(f"Messages: {request.messages}")
        
        # Get conversation information, including provider and model
        conversation = conversation_repo.get_conversation(request.conversation_id, current_user.id)
        if not conversation:
            raise HTTPException(status_code=404, detail=f"Conversation with id {request.conversation_id} not found")
        
        # Use provider and model stored in the conversation, not values from the request
        provider = conversation.provider
        model = conversation.model
        
        print(f"Using provider: {provider}, model: {model}")
        
        # Save user message to the database
        for message in request.messages:
            msg_create = MessageCreate(
                conversation_id=request.conversation_id,
                role=message.role,
                content=message.content,
                provider=provider,  # Use conversation's provider
                user_id=current_user.id
            )
            message_repo.create_message(msg_create)
        
        # Generate assistant response using LLM service
        try:
            print(f"Calling LLMService.generate_response with provider={provider}, model={model}")
            response_content = await LLMService.generate_response(
                messages=[m.model_dump() for m in request.messages],
                provider=provider,  # Use conversation's provider
                model=model  # Use conversation's model
            )
            print(f"Got response: {response_content[:50]}...")
        except ValueError as e:
            print(f"ValueError in LLMService: {str(e)}")
            traceback.print_exc()
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            print(f"Exception in LLMService: {str(e)}")
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=f"Error generating response: {str(e)}")
        
        # Create assistant message
        assistant_message = MessageBase(
            role="assistant",
            content=response_content
        )
        
        # Save assistant message to database
        msg_create = MessageCreate(
            conversation_id=request.conversation_id,
            role=assistant_message.role,
            content=assistant_message.content,
            provider=provider,  # Use conversation's provider
            user_id=current_user.id
        )
        message_repo.create_message(msg_create)
        
        # Update conversation's last modified time using ConversationUpdate class
        update_data = ConversationUpdate(title=None, provider=None, model=None)
        conversation_repo.update_conversation(
            request.conversation_id,
            update_data,  # Use the correct class
            current_user.id
        )
        
        # Return response
        return ChatResponse(
            conversation_id=request.conversation_id,
            message=assistant_message,
            provider=provider  # Use conversation's provider
        )
    except Exception as e:
        print(f"Unhandled exception in chat_completion: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

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