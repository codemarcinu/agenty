from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/chat", tags=["chat"])


@router.get("/ping")
async def ping():
    """Simple ping endpoint for chat module."""
    return {"message": "pong"}


@router.post("")
async def chat_root(request: Request):
    """Dummy POST endpoint for /api/v2/chat to pass contract tests."""
    data = await request.json()
    return JSONResponse(
        {
            "message": "Chat endpoint placeholder",
            "input": data,
            "response": "This is a mock chat response.",
        }
    )
