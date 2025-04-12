from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.db.session import Base

class File(Base):
    """File upload record model"""
    __tablename__ = "files"

    id = Column(Integer, primary_key=True, index=True)
    original_filename = Column(String, index=True, nullable=False)
    stored_filename = Column(String, unique=True, nullable=False)
    file_path = Column(String, nullable=False)
    file_type = Column(String, nullable=False)  # "document" or "image"
    content_type = Column(String, nullable=True)
    file_size = Column(Integer, nullable=False)
    
    # User relationship
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user = relationship("User", back_populates="files")
    
    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False) 