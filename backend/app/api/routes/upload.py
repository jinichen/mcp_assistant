from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from typing import List, Dict
import os
import uuid
import json
from datetime import datetime
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db
from app.models.user import User
from app.db.repositories.file_repository import FileRepository
from app.core.config import get_app_settings

# Get settings
settings = get_app_settings()

# Create uploads directory if it doesn't exist
UPLOAD_DIR = settings.UPLOAD_DIR
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Create subdirectories for different file types
DOCUMENT_DIR = os.path.join(UPLOAD_DIR, settings.DOCUMENTS_SUBDIR)
IMAGE_DIR = os.path.join(UPLOAD_DIR, settings.IMAGES_SUBDIR)
METADATA_DIR = os.path.join(UPLOAD_DIR, settings.METADATA_SUBDIR)
os.makedirs(DOCUMENT_DIR, exist_ok=True)
os.makedirs(IMAGE_DIR, exist_ok=True)
os.makedirs(METADATA_DIR, exist_ok=True)

router = APIRouter()

# Save filename mapping function
def save_filename_mapping(user_id: int, unique_filename: str, original_filename: str, file_type: str):
    """Save mapping of unique filename to original filename"""
    user_metadata_file = os.path.join(METADATA_DIR, f"{user_id}_files.json")
    
    # Read existing mappings
    mappings = {}
    if os.path.exists(user_metadata_file):
        try:
            with open(user_metadata_file, "r") as f:
                mappings = json.load(f)
        except json.JSONDecodeError:
            # File corrupted, recreate it
            mappings = {}
    
    # Add new mapping
    mappings[unique_filename] = {
        "original_filename": original_filename,
        "upload_time": datetime.now().isoformat(),
        "file_type": file_type
    }
    
    # Save mapping
    with open(user_metadata_file, "w") as f:
        json.dump(mappings, f, ensure_ascii=False, indent=2)

# Get filename mappings function
def get_filename_mappings(user_id: int) -> Dict:
    """Get mapping of unique filenames to original filenames"""
    user_metadata_file = os.path.join(METADATA_DIR, f"{user_id}_files.json")
    
    if not os.path.exists(user_metadata_file):
        return {}
    
    try:
        with open(user_metadata_file, "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {}

@router.post("/upload/document")
async def upload_document(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload document file (PDF, DOCX, TXT, etc)
    """
    # Validate file type
    allowed_extensions = [".pdf", ".docx", ".txt", ".md", ".csv", ".json", ".xls", ".xlsx", ".ppt", ".pptx"]
    file_ext = os.path.splitext(file.filename)[1].lower()
    
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type. Allowed types: {', '.join(allowed_extensions)}"
        )
    
    # Create unique filename
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    user_upload_dir = os.path.join(DOCUMENT_DIR, str(current_user.id))
    os.makedirs(user_upload_dir, exist_ok=True)
    
    file_path = os.path.join(user_upload_dir, unique_filename)
    
    # Save the file
    try:
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Save file information to database
        file_size = os.path.getsize(file_path)
        file_repo = FileRepository(db)
        file_obj = file_repo.create_file(
            user_id=current_user.id,
            original_filename=file.filename,
            stored_filename=unique_filename,
            file_path=file_path,
            file_type="document",
            content_type=file.content_type,
            file_size=file_size
        )
    except Exception as e:
        # If error occurs, delete the uploaded file
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload file: {str(e)}"
        )
    
    # Return success response with file details
    return {
        "filename": file.filename,
        "stored_filename": unique_filename,
        "content_type": file.content_type,
        "size": file_size,
        "upload_time": datetime.now().isoformat(),
        "file_path": file_path
    }

@router.post("/upload/image")
async def upload_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload image file (JPG, PNG, etc)
    """
    # Validate file type
    allowed_extensions = [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"]
    file_ext = os.path.splitext(file.filename)[1].lower()
    
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type. Allowed types: {', '.join(allowed_extensions)}"
        )
    
    # Create unique filename
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    user_upload_dir = os.path.join(IMAGE_DIR, str(current_user.id))
    os.makedirs(user_upload_dir, exist_ok=True)
    
    file_path = os.path.join(user_upload_dir, unique_filename)
    
    # Save the file
    try:
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
            
        # Save file information to database
        file_size = os.path.getsize(file_path)
        file_repo = FileRepository(db)
        file_obj = file_repo.create_file(
            user_id=current_user.id,
            original_filename=file.filename,
            stored_filename=unique_filename,
            file_path=file_path,
            file_type="image",
            content_type=file.content_type,
            file_size=file_size
        )
    except Exception as e:
        # If error occurs, delete the uploaded file
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload file: {str(e)}"
        )
    
    # Return success response with file details
    return {
        "filename": file.filename,
        "stored_filename": unique_filename,
        "content_type": file.content_type,
        "size": file_size,
        "upload_time": datetime.now().isoformat(),
        "file_path": file_path
    }

@router.get("/files")
async def list_user_files(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all files uploaded by the current user
    """
    file_repo = FileRepository(db)
    db_files = file_repo.get_files_by_user_id(current_user.id)
    
    user_files = []
    for file in db_files:
        user_files.append({
            "filename": file.stored_filename,
            "original_filename": file.original_filename,
            "type": file.file_type,
            "size": file.file_size,
            "last_modified": file.created_at.isoformat(),
            "content_type": file.content_type
        })
    
    return {"files": user_files}

@router.delete("/files/{file_id}")
async def delete_file(
    file_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a file
    """
    file_repo = FileRepository(db)
    file = file_repo.get_file_by_id(file_id)
    
    if not file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    if file.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this file"
        )
    
    # Delete physical file
    try:
        if os.path.exists(file.file_path):
            os.remove(file.file_path)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete file: {str(e)}"
        )
    
    # Delete database record
    file_repo.delete_file(file_id)
    
    return {"message": "File deleted successfully"} 