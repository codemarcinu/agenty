"""
Telegram Bot API endpoints for FoodSave AI.

This module provides REST API endpoints for Telegram Bot integration,
including webhook handling, webhook configuration, and message sending.
"""

from datetime import datetime
import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
import httpx

from integrations.telegram_bot import telegram_bot_handler
from settings import settings

router = APIRouter(tags=["Telegram Bot"])
logger = logging.getLogger(__name__)


@router.post("/webhook")
async def telegram_webhook(request: Request) -> JSONResponse:
    """Webhook endpoint dla Telegram Bot API.

    Args:
        request: FastAPI request object

    Returns:
        JSONResponse z statusem przetwarzania

    Raises:
        HTTPException: W przypadku błędu walidacji lub przetwarzania
    """
    try:
        # Sprawdź secret token
        if (
            request.headers.get("X-Telegram-Bot-Api-Secret-Token")
            != settings.TELEGRAM_WEBHOOK_SECRET
        ):
            raise HTTPException(status_code=403, detail="Invalid webhook secret")

        # Pobierz dane webhook
        update_data = await request.json()

        # Przetwórz update
        result = await telegram_bot_handler.process_webhook(update_data)

        logger.info(
            "Telegram webhook processed",
            extra={
                "update_id": update_data.get("update_id"),
                "result_status": result.get("status"),
                "telegram_event": "webhook_processed",
            },
        )

        return JSONResponse(content={"status": "ok"})

    except Exception as e:
        logger.error(f"Telegram webhook error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/set-webhook")
async def set_webhook(webhook_url: str) -> JSONResponse:
    """Ustawia webhook URL dla bota.

    Args:
        webhook_url: URL webhook do ustawienia

    Returns:
        JSONResponse z wynikiem ustawienia webhook

    Raises:
        HTTPException: W przypadku błędu komunikacji z Telegram API
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/setWebhook",
                json={
                    "url": webhook_url,
                    "secret_token": settings.TELEGRAM_WEBHOOK_SECRET,
                    "allowed_updates": ["message", "callback_query"],
                },
            )

            if response.status_code == 200:
                result = response.json()
                if result.get("ok"):
                    logger.info(f"Webhook set successfully: {webhook_url}")
                    return JSONResponse(
                        content={"status": "success", "webhook_url": webhook_url}
                    )
                raise HTTPException(
                    status_code=400,
                    detail=f"Telegram API error: {result.get('description')}",
                )
            raise HTTPException(
                status_code=response.status_code, detail="Failed to set webhook"
            )

    except Exception as e:
        logger.error(f"Error setting webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/webhook-info")
async def get_webhook_info() -> JSONResponse:
    """Pobiera informacje o aktualnym webhook.

    Returns:
        JSONResponse z informacjami o webhook

    Raises:
        HTTPException: W przypadku błędu komunikacji z Telegram API
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/getWebhookInfo"
            )

            if response.status_code == 200:
                return JSONResponse(content=response.json())
            raise HTTPException(
                status_code=response.status_code, detail="Failed to get webhook info"
            )

    except Exception as e:
        logger.error(f"Error getting webhook info: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/send-message")
async def send_telegram_message(chat_id: int, message: str) -> JSONResponse:
    """Wysyła wiadomość przez Telegram Bot API.

    Args:
        chat_id: ID czatu Telegram
        message: Tekst wiadomości

    Returns:
        JSONResponse z wynikiem wysłania wiadomości

    Raises:
        HTTPException: W przypadku błędu wysłania wiadomości
    """
    try:
        success = await telegram_bot_handler._send_message(chat_id, message)

        if success:
            return JSONResponse(
                content={"status": "success", "message": "Message sent"}
            )
        raise HTTPException(status_code=500, detail="Failed to send message")

    except Exception as e:
        logger.error(f"Error sending message: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/test-connection")
async def test_telegram_connection() -> JSONResponse:
    """Testuje połączenie z Telegram Bot API.

    Returns:
        JSONResponse z informacjami o bot

    Raises:
        HTTPException: W przypadku błędu komunikacji z Telegram API
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/getMe"
            )

            if response.status_code == 200:
                result = response.json()
                if result.get("ok"):
                    bot_info = result.get("result", {})
                    logger.info(f"Telegram bot connection test successful: {bot_info}")
                    return JSONResponse(
                        content={"status": "success", "bot_info": bot_info}
                    )
                raise HTTPException(
                    status_code=400,
                    detail=f"Telegram API error: {result.get('description')}",
                )
            raise HTTPException(
                status_code=response.status_code, detail="Failed to test connection"
            )

    except Exception as e:
        logger.error(f"Error testing Telegram connection: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/settings")
async def get_telegram_settings() -> JSONResponse:
    """Pobiera ustawienia Telegram Bot.

    Returns:
        JSONResponse z ustawieniami bota
    """
    try:
        settings_data = {
            "enabled": bool(settings.TELEGRAM_BOT_TOKEN),
            "botToken": settings.TELEGRAM_BOT_TOKEN,
            "botUsername": settings.TELEGRAM_BOT_USERNAME,
            "webhookUrl": settings.TELEGRAM_WEBHOOK_URL,
            "webhookSecret": settings.TELEGRAM_WEBHOOK_SECRET,
            "maxMessageLength": settings.TELEGRAM_MAX_MESSAGE_LENGTH,
            "rateLimitPerMinute": settings.TELEGRAM_RATE_LIMIT_PER_MINUTE,
        }

        return JSONResponse(content={"status": "success", "data": settings_data})

    except Exception as e:
        logger.error(f"Error getting Telegram settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/settings")
async def update_telegram_settings(settings_data: dict[str, Any]) -> JSONResponse:
    """Aktualizuje ustawienia Telegram Bot.

    Args:
        settings_data: Nowe ustawienia bota

    Returns:
        JSONResponse z zaktualizowanymi ustawieniami

    Raises:
        HTTPException: W przypadku błędu aktualizacji ustawień
    """
    try:
        # W rzeczywistej implementacji tutaj byłaby logika zapisywania ustawień
        # do bazy danych lub pliku konfiguracyjnego
        logger.info(f"Telegram settings update requested: {settings_data}")

        # Zwróć zaktualizowane ustawienia
        updated_settings = {
            "enabled": settings_data.get("enabled", False),
            "botToken": settings_data.get("botToken", ""),
            "botUsername": settings_data.get("botUsername", ""),
            "webhookUrl": settings_data.get("webhookUrl", ""),
            "webhookSecret": settings_data.get("webhookSecret", ""),
            "maxMessageLength": settings_data.get("maxMessageLength", 4096),
            "rateLimitPerMinute": settings_data.get("rateLimitPerMinute", 30),
        }

        return JSONResponse(content={"status": "success", "data": updated_settings})

    except Exception as e:
        logger.error(f"Error updating Telegram settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/broadcast")
async def broadcast_message(
    message: str, user_ids: list[int] | None = None
) -> JSONResponse:
    """Wysyła wiadomość do wszystkich użytkowników lub określonej listy.

    Args:
        message: Wiadomość do wysłania
        user_ids: Lista ID użytkowników (opcjonalnie)

    Returns:
        JSONResponse z wynikiem broadcast

    Raises:
        HTTPException: W przypadku błędu wysłania broadcast
    """
    try:
        result = await telegram_bot_handler.broadcast_message(message, user_ids)

        if result.get("success"):
            return JSONResponse(
                content={
                    "status": "success",
                    "sent": result.get("sent", 0),
                    "errors": result.get("errors", 0),
                }
            )
        else:
            raise HTTPException(
                status_code=500, detail=result.get("error", "Unknown error")
            )

    except Exception as e:
        logger.error(f"Error broadcasting message: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/send-notification")
async def send_notification(
    alert_type: str, message: str, priority: str = "normal"
) -> JSONResponse:
    """Wysyła alert systemowy.

    Args:
        alert_type: Typ alertu (system, security, maintenance, etc.)
        message: Wiadomość alertu
        priority: Priorytet (low, normal, high, critical)

    Returns:
        JSONResponse z wynikiem wysłania alertu

    Raises:
        HTTPException: W przypadku błędu wysłania alertu
    """
    try:
        result = await telegram_bot_handler.send_system_alert(
            alert_type, message, priority
        )

        if result.get("success"):
            return JSONResponse(
                content={
                    "status": "success",
                    "sent": result.get("sent", 0),
                    "errors": result.get("errors", 0),
                }
            )
        else:
            raise HTTPException(
                status_code=500, detail=result.get("error", "Unknown error")
            )

    except Exception as e:
        logger.error(f"Error sending notification: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/send-daily-summary")
async def send_daily_summary() -> JSONResponse:
    """Wysyła dzienne podsumowanie aktywności.

    Returns:
        JSONResponse z wynikiem wysłania podsumowania

    Raises:
        HTTPException: W przypadku błędu wysłania podsumowania
    """
    try:
        result = await telegram_bot_handler.send_daily_summary()

        if result.get("success"):
            return JSONResponse(
                content={
                    "status": "success",
                    "sent": result.get("sent", 0),
                    "errors": result.get("errors", 0),
                }
            )
        else:
            raise HTTPException(
                status_code=500, detail=result.get("error", "Unknown error")
            )

    except Exception as e:
        logger.error(f"Error sending daily summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_telegram_stats() -> JSONResponse:
    """Pobiera statystyki Telegram Bot.

    Returns:
        JSONResponse ze statystykami bota

    Raises:
        HTTPException: W przypadku błędu pobierania statystyk
    """
    try:
        command_stats = telegram_bot_handler.get_command_stats()
        notification_stats = telegram_bot_handler.get_notification_stats()

        stats = {
            "commands": command_stats,
            "notifications": notification_stats,
            "timestamp": datetime.now().isoformat(),
        }

        return JSONResponse(content={"status": "success", "data": stats})

    except Exception as e:
        logger.error(f"Error getting Telegram stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/logs")
async def get_telegram_logs(limit: int = 100) -> JSONResponse:
    """Pobiera logi Telegram Bot.

    Args:
        limit: Maksymalna liczba logów do zwrócenia

    Returns:
        JSONResponse z logami bota

    Raises:
        HTTPException: W przypadku błędu pobierania logów
    """
    try:
        # W rzeczywistej implementacji tutaj byłaby logika pobierania logów
        # z pliku lub bazy danych
        logs = [
            {
                "timestamp": datetime.now().isoformat(),
                "level": "INFO",
                "message": "Telegram Bot is running",
                "user_id": None,
            }
        ]

        return JSONResponse(content={"status": "success", "data": logs[:limit]})

    except Exception as e:
        logger.error(f"Error getting Telegram logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/users")
async def get_telegram_users() -> JSONResponse:
    """Pobiera listę użytkowników bota.

    Returns:
        JSONResponse z listą użytkowników

    Raises:
        HTTPException: W przypadku błędu pobierania użytkowników
    """
    try:
        # W rzeczywistej implementacji tutaj byłaby logika pobierania użytkowników
        # z bazy danych
        users = [
            {
                "user_id": 123456789,
                "username": "test_user",
                "first_name": "Test",
                "last_seen": datetime.now().isoformat(),
                "message_count": 15,
            }
        ]

        return JSONResponse(content={"status": "success", "data": users})

    except Exception as e:
        logger.error(f"Error getting Telegram users: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/subscribe")
async def subscribe_user(user_id: int) -> JSONResponse:
    """Dodaje użytkownika do listy subskrybentów powiadomień.

    Args:
        user_id: ID użytkownika Telegram

    Returns:
        JSONResponse z wynikiem subskrypcji

    Raises:
        HTTPException: W przypadku błędu subskrypcji
    """
    try:
        telegram_bot_handler.notification_system.add_subscriber(user_id)

        return JSONResponse(
            content={
                "status": "success",
                "message": f"User {user_id} subscribed to notifications",
            }
        )

    except Exception as e:
        logger.error(f"Error subscribing user: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/unsubscribe")
async def unsubscribe_user(user_id: int) -> JSONResponse:
    """Usuwa użytkownika z listy subskrybentów powiadomień.

    Args:
        user_id: ID użytkownika Telegram

    Returns:
        JSONResponse z wynikiem rezygnacji z subskrypcji

    Raises:
        HTTPException: W przypadku błędu rezygnacji z subskrypcji
    """
    try:
        telegram_bot_handler.notification_system.remove_subscriber(user_id)

        return JSONResponse(
            content={
                "status": "success",
                "message": f"User {user_id} unsubscribed from notifications",
            }
        )

    except Exception as e:
        logger.error(f"Error unsubscribing user: {e}")
        raise HTTPException(status_code=500, detail=str(e))
