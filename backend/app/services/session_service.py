from typing import List, Dict, Any, Optional
import logging
import uuid
from datetime import datetime
from fastapi import Depends
from sqlalchemy.orm import Session
from app.database.models import ChatSession, ChatMessage

# In-memory session data storage (actual projects should use a database)
sessions_db = {}

class SessionService:
    """Session service, manages CRUD operations for chat sessions"""
    
    def get_all_sessions(self, db: Session) -> List[Dict[str, Any]]:
        """Get all sessions list"""
        sessions = db.query(ChatSession).order_by(ChatSession.updated_at.desc()).all()
        return [self._session_to_dict(session) for session in sessions]
    
    def create_session(self, db: Session, session_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create a new session"""
        session_data = session_data or {}
        
        # Create session object
        session = ChatSession(
            id=session_data.get("id", str(uuid.uuid4())),
            title=session_data.get("title", "New session"),
            model=session_data.get("model", "gpt-3.5-turbo"),
            provider=session_data.get("provider", "openai"),
            user_id=session_data.get("user_id")
        )
        
        # Save to database
        db.add(session)
        db.commit()
        db.refresh(session)
        
        return self._session_to_dict(session)
    
    def get_session(self, db: Session, session_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific session"""
        session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
        return self._session_to_dict(session) if session else None
    
    def update_session(self, db: Session, session_id: str, session_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update session information"""
        session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
        if not session:
            return None
        
        # Update session fields
        for key, value in session_data.items():
            if key != "id" and key != "created_at":  # Do not allow changing ID and creation time
                setattr(session, key, value)
        
        # Update last modification time
        session.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(session)
        
        return self._session_to_dict(session)
    
    def delete_session(self, db: Session, session_id: str) -> bool:
        """Delete a session"""
        session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
        if not session:
            return False
        
        db.delete(session)
        db.commit()
        
        return True
    
    def get_session_messages(self, db: Session, session_id: str) -> List[Dict[str, Any]]:
        """Get all messages in a session"""
        session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
        if not session:
            return []
        
        messages = db.query(ChatMessage).filter(
            ChatMessage.session_id == session_id
        ).order_by(ChatMessage.order).all()
        
        return [self._message_to_dict(msg) for msg in messages]
    
    def add_message(self, db: Session, session_id: str, message_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Add a message to a session"""
        session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
        if not session:
            return None
        
        # Get the current highest message order
        last_message = db.query(ChatMessage).filter(
            ChatMessage.session_id == session_id
        ).order_by(ChatMessage.order.desc()).first()
        
        order = (last_message.order + 1) if last_message else 0
        
        # Create message
        message = ChatMessage(
            session_id=session_id,
            role=message_data["role"],
            content=message_data.get("content"),
            order=order,
            name=message_data.get("name"),
            tool_call_id=message_data.get("tool_call_id"),
            tool_name=message_data.get("tool_name"),
            tool_args=message_data.get("tool_args"),
            tool_response=message_data.get("tool_response"),
            is_tool_call=message_data.get("is_tool_call", False)
        )
        
        # Update session
        session.updated_at = datetime.utcnow()
        
        # Save to database
        db.add(message)
        db.commit()
        db.refresh(message)
        
        return self._message_to_dict(message)
    
    def _session_to_dict(self, session: ChatSession) -> Dict[str, Any]:
        """Convert session object to dictionary"""
        if not session:
            return None
        
        return {
            "id": session.id,
            "title": session.title,
            "model": session.model,
            "provider": session.provider,
            "created_at": session.created_at.isoformat() if session.created_at else None,
            "updated_at": session.updated_at.isoformat() if session.updated_at else None,
            "user_id": session.user_id,
        }
    
    def _message_to_dict(self, message: ChatMessage) -> Dict[str, Any]:
        """Convert message object to dictionary"""
        if not message:
            return None
        
        result = {
            "id": message.id,
            "session_id": message.session_id,
            "role": message.role,
            "content": message.content,
            "order": message.order,
            "created_at": message.created_at.isoformat() if message.created_at else None,
        }
        
        # Include optional fields if they exist
        if message.name:
            result["name"] = message.name
            
        if message.is_tool_call:
            result["tool_call_id"] = message.tool_call_id
            result["tool_name"] = message.tool_name
            result["tool_args"] = message.tool_args
            result["tool_response"] = message.tool_response
            result["is_tool_call"] = True
            
        return result

# Dependency injection to get session service instance
def get_session_service() -> SessionService:
    return SessionService() 