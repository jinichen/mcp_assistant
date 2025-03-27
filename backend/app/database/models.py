from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, JSON, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from datetime import datetime

from app.database.database import Base

class ChatSession(Base):
    """Chat session model"""
    __tablename__ = "chat_sessions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    model = Column(String, nullable=False)  # Model name used
    provider = Column(String, nullable=False)
    title = Column(String, nullable=True)
    user_id = Column(String, nullable=True)  # Reserved for future user authentication
    
    # Establish relationship with messages
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<ChatSession(id={self.id}, created_at={self.created_at}, model={self.model})>"


class ChatMessage(Base):
    """Chat message model"""
    __tablename__ = "chat_messages"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String, ForeignKey("chat_sessions.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    role = Column(String, nullable=False)
    content = Column(Text, nullable=True)
    order = Column(Integer, nullable=False)  # Message order in the session
    name = Column(String, nullable=True)
    
    # Tool call related fields
    tool_call_id = Column(String, nullable=True)  # If this is a tool call, store the tool call ID
    tool_name = Column(String, nullable=True)
    tool_args = Column(Text, nullable=True)
    tool_response = Column(Text, nullable=True)
    is_tool_call = Column(Boolean, default=False)
    
    # Establish relationship with session
    session = relationship("ChatSession", back_populates="messages")

    def __repr__(self):
        return f"<ChatMessage(id={self.id}, role={self.role}, order={self.order})>" 