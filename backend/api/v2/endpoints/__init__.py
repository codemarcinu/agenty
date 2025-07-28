from datetime import datetime
import os
from typing import Any, Optional

from fastapi import APIRouter, Body, File, HTTPException, Query, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from .performance import router as performance_router

router = APIRouter()

# Include performance router
router.include_router(performance_router)


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="Message content")
    context: dict | None = None


# @router.post("/chat")
# async def chat_stub(request: ChatRequest):
#    """Stub: Zwraca przykładową odpowiedź chat zgodną ze schematem kontraktowym"""
#    if not request.message.strip():
#        raise HTTPException(status_code=422, detail="Message cannot be empty")
#
#    return {
#        "response": "Stub chat response",
#        "success": True,
#        "metadata": {},
#        "timestamp": datetime.utcnow().isoformat(),
#    }


@router.get("/users")
async def users_stub():
    """Stub: Zwraca przykładową listę użytkowników"""
    return [
        {"id": 1, "username": "user1", "email": "user1@example.com"},
        {"id": 2, "username": "user2", "email": "user2@example.com"},
    ]


@router.get("/test")
async def test_endpoint():
    """Test endpoint for v2 API"""
    return {"message": "v2 API is working", "timestamp": datetime.utcnow().isoformat()}


@router.get("/raise_error")
async def raise_error(type: str = Query(..., description="Type of error to raise")):
    """Test endpoint for error handling - raises different types of errors based on query parameter"""
    if type == "value":
        raise ValueError("Test ValueError")
    elif type == "key":
        raise KeyError("Missing required field")
    elif type == "custom":
        raise HTTPException(status_code=500, detail="Test custom exception")
    elif type == "http":
        raise HTTPException(status_code=418, detail="I'm a teapot")
    else:
        raise Exception("Unexpected error")


@router.get("/users/me")
async def users_me_stub():
    """Stub: Zwraca przykładowego zalogowanego użytkownika"""
    # W trybie testowym zwracamy mock user
    if os.getenv("TESTING_MODE") == "true":
        return {
            "id": 1,
            "email": "test@example.com",
            "username": "testuser",
            "full_name": "Test User",
            "is_active": True,
            "is_verified": True,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "last_login": None,
            "roles": ["user"],
        }

    # Symulacja braku autoryzacji w trybie produkcyjnym
    raise HTTPException(status_code=401, detail="Authentication required")


@router.post("/receipts/upload")
async def receipts_upload_stub(file: UploadFile = File(...)):
    """Stub: Zwraca przykładową odpowiedź uploadu paragonu"""
    # W trybie testowym zwracamy mock response
    if os.getenv("TESTING_MODE") == "true":
        return {
            "id": "test-receipt-id",
            "filename": file.filename,
            "upload_date": datetime.utcnow().isoformat(),
            "status": "uploaded",
        }

    # Symulacja braku autoryzacji w trybie produkcyjnym
    raise HTTPException(status_code=401, detail="Authentication required")
