"""
Telegram Bot Integration for FoodSave AI.

This module provides integration with Telegram Bot API, allowing users
to interact with the AI assistant directly through Telegram.
"""

import asyncio
from datetime import datetime
import logging
from typing import Any

import httpx
from pydantic import BaseModel, Field

from infrastructure.database.database import get_db
from integrations.telegram_commands import TelegramCommandHandler
from integrations.telegram_file_handler import TelegramFileHandler
from integrations.telegram_notifications import TelegramNotificationSystem
from settings import settings

logger = logging.getLogger(__name__)


class TelegramUpdate(BaseModel):
    """Model dla webhook updates z Telegram."""

    update_id: int
    message: dict[str, Any] | None = None
    callback_query: dict[str, Any] | None = None


class TelegramMessage(BaseModel):
    """Model dla wiadomości Telegram."""

    message_id: int
    from_user: dict[str, Any] = Field(alias="from")
    chat: dict[str, Any]
    text: str | None = None
    date: int


class TelegramBotHandler:
    """Handler dla integracji z Telegram Bot API."""

    def __init__(self) -> None:
        """Inicjalizuje handler Telegram Bot."""
        self.bot_token = settings.TELEGRAM_BOT_TOKEN
        self.api_base_url = f"https://api.telegram.org/bot{self.bot_token}"
        self.rate_limiter: dict[int, datetime] = {}  # Simple rate limiting

        # Inicjalizuj komponenty
        self.command_handler = TelegramCommandHandler(self)
        self.file_handler = TelegramFileHandler(self)
        self.notification_system = TelegramNotificationSystem(self)

    async def process_webhook(self, update_data: dict[str, Any]) -> dict[str, Any]:
        """Przetwarza webhook update z Telegram.

        Args:
            update_data: Dane webhook z Telegram API

        Returns:
            Dict z wynikiem przetwarzania

        Raises:
            Exception: W przypadku błędu przetwarzania
        """
        try:
            update = TelegramUpdate(**update_data)

            if update.message:
                return await self._handle_message(update.message)
            if update.callback_query:
                return await self._handle_callback_query(update.callback_query)
            logger.warning(f"Unknown update type: {update_data}")
            return {"status": "ignored", "reason": "unknown_update_type"}

        except Exception as e:
            logger.error(f"Error processing webhook: {e}")
            return {"status": "error", "error": str(e)}

    async def _handle_message(self, message_data: dict[str, Any]) -> dict[str, Any]:
        """Obsługuje wiadomości tekstowe i pliki.

        Args:
            message_data: Dane wiadomości z Telegram

        Returns:
            Dict z wynikiem obsługi wiadomości
        """
        try:
            message = TelegramMessage(**message_data)
            user_id = message.from_user["id"]
            chat_id = message.chat["id"]
            text = message.text

            # Rate limiting
            if not self._check_rate_limit(user_id):
                await self._send_message(
                    chat_id, "⚠️ Zbyt wiele wiadomości. Spróbuj za chwilę."
                )
                return {"status": "rate_limited"}

            # Sprawdź czy to plik
            if self._has_file(message_data):
                response = await self.file_handler.handle_file(message_data)
                if response:
                    await self._send_message(chat_id, response)
                    return {"status": "file_processed", "user_id": user_id}
                else:
                    return {"status": "ignored", "reason": "unsupported_file"}

            # Sprawdź czy to komenda
            if text and text.startswith("/"):
                response = await self.command_handler.handle_command(message_data)
                if response:
                    await self._send_message(chat_id, response)
                    return {"status": "command_processed", "user_id": user_id}

            # Przetwarzanie zwykłej wiadomości przez AI
            if text:
                ai_response = await self._process_with_ai(text, user_id)
                await self._send_message(chat_id, ai_response)
                await self._save_conversation(user_id, text, ai_response)

                return {
                    "status": "success",
                    "user_id": user_id,
                    "response_length": len(ai_response),
                }
            else:
                return {"status": "ignored", "reason": "no_text"}

        except Exception as e:
            logger.error(f"Error handling message: {e}")
            return {"status": "error", "error": str(e)}

    def _has_file(self, message_data: dict[str, Any]) -> bool:
        """Sprawdza czy wiadomość zawiera plik."""
        file_types = ["photo", "document", "voice", "video", "audio"]
        return any(file_type in message_data for file_type in file_types)

    async def _process_with_ai(self, user_message: str, user_id: int) -> str:
        """Przetwarza wiadomość przez AI.

        Args:
            user_message: Wiadomość użytkownika
            user_id: ID użytkownika Telegram

        Returns:
            Odpowiedź AI jako string
        """
        try:
            # Użyj istniejącego orchestrator
            from agents.orchestrator_factory import create_orchestrator
            from infrastructure.database.database import get_db

            async for db in get_db():
                orchestrator = create_orchestrator(db)

                # Przetwórz zapytanie
                response = await orchestrator.process_query(
                    query=user_message,
                    session_id=f"telegram_{user_id}",
                )

                if response.success:
                    return (
                        response.text
                        or "Przepraszam, nie udało się przetworzyć zapytania."
                    )
                else:
                    return f"❌ Błąd: {response.error or 'Nieznany błąd'}"

            # This should never be reached, but kept as safety fallback
            return "❌ Przepraszam, nie udało się połączyć z bazą danych."

        except Exception as e:
            logger.error(f"AI processing error: {e}")
            return "❌ Przepraszam, wystąpił błąd podczas przetwarzania zapytania."

    async def _send_message(self, chat_id: int, text: str) -> bool:
        """Wysyła wiadomość przez Telegram Bot API.

        Args:
            chat_id: ID czatu Telegram
            text: Tekst wiadomości

        Returns:
            True jeśli wiadomość została wysłana pomyślnie
        """
        try:
            # Podziel długie wiadomości
            if len(text) > settings.TELEGRAM_MAX_MESSAGE_LENGTH:
                chunks = self._split_message(text)
                for chunk in chunks:
                    await self._send_single_message(chat_id, chunk)
                    await asyncio.sleep(0.1)  # Rate limiting
            else:
                await self._send_single_message(chat_id, text)

            return True

        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return False

    async def _send_single_message(self, chat_id: int, text: str) -> None:
        """Wysyła pojedynczą wiadomość.

        Args:
            chat_id: ID czatu Telegram
            text: Tekst wiadomości
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.api_base_url}/sendMessage",
                json={"chat_id": chat_id, "text": text, "parse_mode": "HTML"},
                timeout=10.0,
            )

            if response.status_code != 200:
                logger.error(
                    f"Telegram API error: {response.status_code} - {response.text}"
                )

    def _split_message(self, text: str, max_length: int = 4000) -> list[str]:
        """Dzieli długą wiadomość na części.

        Args:
            text: Tekst do podziału
            max_length: Maksymalna długość części

        Returns:
            Lista części wiadomości
        """
        if len(text) <= max_length:
            return [text]

        chunks = []
        current_chunk = ""

        for line in text.split("\n"):
            if len(current_chunk) + len(line) + 1 <= max_length:
                current_chunk += line + "\n"
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = line + "\n"

        if current_chunk:
            chunks.append(current_chunk.strip())

        return chunks

    def _check_rate_limit(self, user_id: int) -> bool:
        """Sprawdza rate limiting dla użytkownika.

        Args:
            user_id: ID użytkownika

        Returns:
            True jeśli użytkownik może wysłać wiadomość
        """
        now = datetime.now()
        if user_id in self.rate_limiter:
            last_message = self.rate_limiter[user_id]
            if (now - last_message).seconds < 10:  # 1 wiadomość na 10 sekund
                return False

        self.rate_limiter[user_id] = now
        return True

    async def _save_conversation(
        self, user_id: int, user_message: str, ai_response: str
    ) -> None:
        """Zapisuje konwersację do bazy danych.

        Args:
            user_id: ID użytkownika Telegram
            user_message: Wiadomość użytkownika
            ai_response: Odpowiedź AI
        """
        try:
            async for db in get_db():
                # Use session_id instead of user_id for new model
                session_id = f"telegram_{user_id}"

                # For now, just log the conversation - proper storage would need Message model
                logger.info(
                    f"Conversation for {session_id}: {user_message[:50]}... -> {ai_response[:50]}..."
                )

                # TODO: Implement proper conversation storage with Message model
                # conversation = Conversation(session_id=session_id)
                # message = Message(conversation=conversation, content=user_message, role="user")
                # response = Message(conversation=conversation, content=ai_response, role="assistant")

        except Exception as e:
            logger.error(f"Error saving conversation: {e}")

    async def _handle_callback_query(
        self, callback_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Obsługuje callback queries z inline keyboards.

        Args:
            callback_data: Dane callback query

        Returns:
            Dict z wynikiem obsługi
        """
        try:
            callback_id = callback_data["id"]
            user_id = callback_data["from"]["id"]
            chat_id = callback_data["message"]["chat"]["id"]
            data = callback_data.get("data", "")

            # Obsługa różnych typów callback
            if data.startswith("receipt_"):
                # Obsługa akcji związanych z paragonami
                await self._handle_receipt_callback(chat_id, data)
            elif data.startswith("recipe_"):
                # Obsługa akcji związanych z przepisami
                await self._handle_recipe_callback(chat_id, data)
            else:
                await self._send_message(chat_id, "❌ Nieznana akcja")

            # Odpowiedz na callback
            await self._answer_callback_query(callback_id)

            return {"status": "callback_processed", "user_id": user_id}

        except Exception as e:
            logger.error(f"Error handling callback query: {e}")
            return {"status": "error", "error": str(e)}

    async def _handle_receipt_callback(self, chat_id: int, data: str) -> None:
        """Obsługuje callback związany z paragonami."""
        action = data.split("_", 1)[1]

        if action == "analyze":
            await self._send_message(chat_id, "📷 Analizuję paragon...")
        elif action == "save":
            await self._send_message(chat_id, "💾 Zapisuję paragon...")
        else:
            await self._send_message(chat_id, "❌ Nieznana akcja paragonu")

    async def _handle_recipe_callback(self, chat_id: int, data: str) -> None:
        """Obsługuje callback związany z przepisami."""
        action = data.split("_", 1)[1]

        if action == "save":
            await self._send_message(chat_id, "💾 Zapisuję przepis...")
        elif action == "share":
            await self._send_message(chat_id, "📤 Udostępniam przepis...")
        else:
            await self._send_message(chat_id, "❌ Nieznana akcja przepisu")

    async def _answer_callback_query(self, callback_id: str) -> None:
        """Odpowiada na callback query."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_base_url}/answerCallbackQuery",
                    json={"callback_query_id": callback_id},
                    timeout=5.0,
                )

                if response.status_code != 200:
                    logger.error(f"Error answering callback query: {response.text}")

        except Exception as e:
            logger.error(f"Error answering callback query: {e}")

    # Metody dla systemu powiadomień
    async def broadcast_message(
        self, message: str, user_ids: list[int] | None = None
    ) -> dict[str, Any]:
        """Wysyła wiadomość do wielu użytkowników."""
        return await self.notification_system.broadcast_message(message, user_ids)

    async def send_system_alert(
        self, alert_type: str, message: str, priority: str = "normal"
    ) -> dict[str, Any]:
        """Wysyła alert systemowy."""
        return await self.notification_system.send_system_alert(
            alert_type, message, priority
        )

    async def send_daily_summary(self) -> dict[str, Any]:
        """Wysyła dzienne podsumowanie."""
        return await self.notification_system.send_daily_summary()

    # Metody dla statystyk
    def get_command_stats(self) -> dict[str, Any]:
        """Zwraca statystyki komend."""
        return self.command_handler.get_daily_stats()

    def get_notification_stats(self) -> dict[str, Any]:
        """Zwraca statystyki powiadomień."""
        return {
            "subscribers_count": self.notification_system.get_subscribers_count(),
            "notification_history": self.notification_system.get_notification_history(),
        }


# Global instance
telegram_bot_handler = TelegramBotHandler()
