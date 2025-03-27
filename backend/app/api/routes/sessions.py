from fastapi import APIRouter, Depends, HTTPException, Query, Path
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime
import logging

from app.services.session_service import SessionService, get_session_service
from app.database import get_db
from sqlalchemy.orm import Session
from app.constants import DEFAULT_MODEL, DEFAULT_PROVIDER

router = APIRouter(prefix="/sessions", tags=["sessions"])

# Request models
class SessionCreateRequest(BaseModel):
    title: str = Field(..., description="Session title")
    model: str = Field(..., description="Model name to use")
    messages: List[Dict[str, Any]] = Field(..., description="List of session messages")
    user_id: Optional[str] = Field(None, description="User ID")

# Response models
class SessionResponse(BaseModel):
    id: str
    title: str
    model: str
    provider: str
    created_at: str
    updated_at: str
    messages: List[Dict[str, Any]] = []
    user_id: Optional[str] = None

class SessionListResponse(BaseModel):
    sessions: List[SessionResponse]
    total: int

class SessionDetailResponse(SessionResponse):
    messages: List[Dict[str, Any]]

class DeleteResponse(BaseModel):
    success: bool
    message: str

# Routes
@router.get("/", response_model=List[SessionResponse])
async def get_sessions(db: Session = Depends(get_db)):
    """Get all sessions list"""
    try:
        sessions = get_session_service().get_all_sessions(db)
        
        # Add empty messages array if not present
        for session in sessions:
            if "messages" not in session:
                session["messages"] = []
                
        return sessions
    except Exception as e:
        logging.error(f"Error in get_sessions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/", response_model=SessionResponse)
async def create_session(request: SessionCreateRequest = None, db: Session = Depends(get_db)):
    """Create new session"""
    try:
        data = request.dict() if request else {}
        
        if not data.get("model"):
            data["model"] = DEFAULT_MODEL
            
        session = get_session_service().create_session(db, data)
        session["messages"] = []
        
        return session
    except Exception as e:
        logging.error(f"Error in create_session: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(session_id: str, db: Session = Depends(get_db)):
    """Get specific session"""
    try:
        session = get_session_service().get_session(db, session_id)
        
        if not session:
            raise HTTPException(
                status_code=404,
                detail=f"Session with ID {session_id} not found"
            )
            
        # Get messages for this session
        messages = get_session_service().get_session_messages(db, session_id)
        session["messages"] = messages
        
        return session
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error in get_session: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{session_id}", response_model=SessionResponse)
async def update_session(session_id: str, request: dict, db: Session = Depends(get_db)):
    """Update session information"""
    try:
        session = get_session_service().update_session(db, session_id, request)
        
        if not session:
            raise HTTPException(
                status_code=404,
                detail=f"Session with ID {session_id} not found"
            )
            
        # Get messages for this session
        messages = get_session_service().get_session_messages(db, session_id)
        session["messages"] = messages
        
        return session
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error in update_session: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{session_id}", response_model=DeleteResponse)
async def delete_session(session_id: str, db: Session = Depends(get_db)):
    """Delete session"""
    try:
        result = get_session_service().delete_session(db, session_id)
        
        if not result:
            raise HTTPException(
                status_code=404,
                detail=f"Session with ID {session_id} not found"
            )
            
        return {"success": True, "message": f"Session {session_id} deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error in delete_session: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 