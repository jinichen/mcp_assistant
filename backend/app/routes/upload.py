"""
Upload API routes
"""
import os
import uuid
import shutil
import base64
from io import BytesIO
from typing import List
import logging
from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from fastapi.responses import JSONResponse
from PIL import Image

# Set up logger
logger = logging.getLogger(__name__)

# Create uploads directory if it doesn't exist
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Set up routes
router = APIRouter(prefix="/upload", tags=["upload"])

@router.post("/images")
async def upload_images(files: List[UploadFile] = File(...)):
    """Upload images to be used in chat
    
    Returns image URLs that can be used in multimodal chat messages
    """
    result = []
    
    try:
        for file in files:
            # Generate unique filename
            file_extension = os.path.splitext(file.filename)[1] if file.filename else ".jpg"
            unique_filename = f"{uuid.uuid4()}{file_extension}"
            file_path = os.path.join(UPLOAD_DIR, unique_filename)
            
            # Read and validate image
            contents = await file.read()
            try:
                img = Image.open(BytesIO(contents))
                img.verify()  # Verify it's a valid image
                
                # Optional: resize large images to save bandwidth
                img = Image.open(BytesIO(contents))
                if max(img.size) > 1024:  # If larger than 1024px in any dimension
                    img.thumbnail((1024, 1024), Image.LANCZOS)
                    buffer = BytesIO()
                    img.save(buffer, format=img.format or "JPEG")
                    contents = buffer.getvalue()
            except Exception as e:
                logger.error(f"Invalid image file: {str(e)}")
                raise HTTPException(status_code=400, detail=f"Invalid image file: {file.filename}")
            
            # Save the file
            with open(file_path, "wb") as f:
                f.write(contents)
            
            # For simplicity, encode as base64 for direct use in messages
            base64_image = base64.b64encode(contents).decode("utf-8")
            mime_type = file.content_type or "image/jpeg"
            data_url = f"data:{mime_type};base64,{base64_image}"
            
            # Add results with both local path and base64 data URL
            result.append({
                "filename": file.filename,
                "content_type": mime_type,
                "size": len(contents),
                "image_url": data_url,
                "file_path": f"/uploads/{unique_filename}"
            })
        
        return {"images": result}
    
    except Exception as e:
        logger.error(f"Error uploading images: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error uploading images: {str(e)}") 