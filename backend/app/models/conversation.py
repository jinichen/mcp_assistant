from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum
from sqlalchemy.sql import func
import enum

from app.db.session import Base

class ConversationType(str, enum.Enum):
    TEXT = "text"
    MULTIMODAL = "multimodal"

class Conversation(Base):
    __tablename__ = "conversations"
    
    id = Column(String, primary_key=True, index=True)
    title = Column(String, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    provider = Column(String, nullable=True)  # 'openai', 'google', 'anthropic', 'nvidia'
    model = Column(String, nullable=True)
    conversation_type = Column(Enum(ConversationType), default=ConversationType.TEXT, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<Conversation id={self.id}, title={self.title}, type={self.conversation_type}>" 