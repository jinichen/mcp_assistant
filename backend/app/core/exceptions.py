from fastapi import HTTPException, status

def handle_api_error(detail: str, status_code: int = status.HTTP_400_BAD_REQUEST):
    """Helper function to raise consistent HTTP exceptions"""
    raise HTTPException(
        status_code=status_code,
        detail=detail,
    ) 