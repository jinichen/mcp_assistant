from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.message import Message
from app.schemas.message import MessageCreate, MessageInDB

class MessageRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def create_message(self, message: MessageCreate) -> Message:
        db_message = Message(
            conversation_id=message.conversation_id,
            role=message.role,
            content=message.content,
            provider=message.provider,
            user_id=message.user_id
        )
        self.db.add(db_message)
        self.db.commit()
        self.db.refresh(db_message)
        return db_message
    
    def get_messages_by_conversation_id(self, conversation_id: str, user_id: Optional[int] = None) -> List[Message]:
        query = self.db.query(Message).filter(
            Message.conversation_id == conversation_id
        )
        
        if user_id is not None:
            query = query.filter(Message.user_id == user_id)
            
        return query.order_by(Message.created_at).all()
    
    def get_message_by_id(self, message_id: int) -> Optional[Message]:
        return self.db.query(Message).filter(Message.id == message_id).first()
    
    def delete_conversation(self, conversation_id: str, user_id: Optional[int] = None) -> bool:
        query = self.db.query(Message).filter(
            Message.conversation_id == conversation_id
        )
        
        if user_id is not None:
            query = query.filter(Message.user_id == user_id)
            
        messages = query.all()
        
        if not messages:
            return False
        
        for message in messages:
            self.db.delete(message)
        
        self.db.commit()
        return True 