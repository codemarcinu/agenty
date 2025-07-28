from fastapi import APIRouter

from api.v2.endpoints import (
    backup,
    chat,
    enhanced_backup,
    feedback,
    gmail_inbox_zero,
    inventory,
    ocr_rag,
    rag,
    receipts,
    router as stub_router,
    security,
    telegram,
    user_profile,
    weather,
)
from api.v2.endpoints.concise_responses import (
    router as concise_responses_router,
)

api_router = APIRouter()

api_router.include_router(backup.router, prefix="/backup", tags=["backup"])
api_router.include_router(rag.router, tags=["rag"])
api_router.include_router(
    receipts.router, tags=["receipts"]
)  # Odkomentowane, by aktywować endpointy receipts
api_router.include_router(
    inventory.router, tags=["inventory"]
)  # Dodane endpointy inventory
api_router.include_router(weather.router, tags=["weather"])
api_router.include_router(
    concise_responses_router, prefix="/concise-responses", tags=["concise-responses"]
)
api_router.include_router(telegram.router, prefix="/telegram", tags=["Telegram Bot"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
api_router.include_router(stub_router, tags=["stubs"])
api_router.include_router(security.router, tags=["Security Management"])
api_router.include_router(enhanced_backup.router, tags=["Enhanced Backup Management"])
api_router.include_router(user_profile.router, tags=["User Profile"])
api_router.include_router(
    gmail_inbox_zero.router, prefix="/gmail-inbox-zero", tags=["Gmail Inbox Zero"]
)
api_router.include_router(ocr_rag.router, tags=["OCR-RAG Integration"])
api_router.include_router(feedback.router, tags=["Feedback"])
