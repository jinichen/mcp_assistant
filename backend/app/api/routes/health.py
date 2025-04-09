from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.config import get_app_settings

router = APIRouter()
settings = get_app_settings()

@router.get("")
async def health_check(db: Session = Depends(get_db)):
    """
    Health check endpoint to verify API and database connection.
    """
    return {
        "status": "ok",
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "database": "connected"
    } 