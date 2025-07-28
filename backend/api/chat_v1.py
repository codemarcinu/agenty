"""
Simple v1 chat endpoint for frontend compatibility
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Any
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None

class ChatResponse(BaseModel):
    response: str
    session_id: str | None = None

@router.post("/chat", response_model=ChatResponse)
async def chat_v1(request: ChatRequest) -> ChatResponse:
    """Chat endpoint for v1 API - forwards to main chat functionality"""
    try:
        # Import here to avoid circular imports
        from api.chat import chat_with_model
        from fastapi import Request
        
        # Create a mock request object with the message
        from fastapi import Request
        from starlette.requests import Request as StarletteRequest
        
        # Simple approach - just return a basic response for now
        # TODO: Integrate with proper orchestrator later
        return ChatResponse(
            response=f"Echo: {request.message}",
            session_id=request.session_id or "default"
        )
        
    except Exception as e:
        logger.error(f"Chat v1 error: {e}")
        raise HTTPException(status_code=500, detail=str(e))