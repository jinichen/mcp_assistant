from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.conversation import Conversation, ConversationType
from app.schemas.conversation import ConversationCreate, ConversationUpdate, generate_conversation_id
from app.core.config import get_app_settings

settings = get_app_settings()

class ConversationRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def create_conversation(self, conversation: ConversationCreate, user_id: int) -> Conversation:
        conversation_id = generate_conversation_id()
        provider = conversation.provider or settings.DEFAULT_LLM_PROVIDER
        
        # Choose appropriate default model based on conversation type and provider
        model = conversation.model
        if not model:
            if conversation.conversation_type == ConversationType.MULTIMODAL:
                # Choose a model that supports multimodal
                if provider == "openai":
                    model = "gpt-4-vision-preview"
                elif provider == "google":
                    model = "gemini-pro-vision"
                elif provider == "anthropic":
                    model = "claude-3-opus-20240229"
                else:
                    # Default to OpenAI multimodal model
                    provider = "openai"
                    model = "gpt-4-vision-preview"
            else:
                # Text-only models use default values from config
                if provider == "openai":
                    model = settings.DEFAULT_OPENAI_MODEL
                elif provider == "google":
                    model = settings.DEFAULT_GOOGLE_MODEL
                elif provider == "anthropic":
                    model = settings.DEFAULT_ANTHROPIC_MODEL
                elif provider == "nvidia":
                    model = settings.DEFAULT_NVIDIA_MODEL
        
        db_conversation = Conversation(
            id=conversation_id,
            title=conversation.title or "New Conversation",
            user_id=user_id,
            provider=provider,
            model=model,
            conversation_type=conversation.conversation_type
        )
        
        self.db.add(db_conversation)
        self.db.commit()
        self.db.refresh(db_conversation)
        return db_conversation
    
    def get_conversation(self, conversation_id: str, user_id: Optional[int] = None) -> Optional[Conversation]:
        query = self.db.query(Conversation).filter(Conversation.id == conversation_id)
        
        if user_id is not None:
            query = query.filter(Conversation.user_id == user_id)
            
        return query.first()
    
    def get_conversations_by_user_id(self, user_id: int) -> List[Conversation]:
        return self.db.query(Conversation).filter(
            Conversation.user_id == user_id
        ).order_by(Conversation.updated_at.desc()).all()
    
    def update_conversation(self, conversation_id: str, update_data: ConversationUpdate, user_id: int) -> Optional[Conversation]:
        conversation = self.get_conversation(conversation_id, user_id)
        
        if not conversation:
            return None
        
        # Update fields
        if update_data.title is not None:
            conversation.title = update_data.title
        
        if update_data.provider is not None:
            conversation.provider = update_data.provider
        
        if update_data.model is not None:
            conversation.model = update_data.model
        
        self.db.commit()
        self.db.refresh(conversation)
        return conversation
    
    def delete_conversation(self, conversation_id: str, user_id: int) -> bool:
        conversation = self.get_conversation(conversation_id, user_id)
        
        if not conversation:
            return False
        
        self.db.delete(conversation)
        self.db.commit()
        return True 