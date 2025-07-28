"""
Handler dla plików z Telegram - FoodSave AI.

Ten moduł zawiera obsługę różnych typów plików przesyłanych przez Telegram:
- Zdjęcia (paragony do analizy OCR)
- Dokumenty (PDF do przetwarzania)
- Wiadomości głosowe (konwersja na tekst)
"""

import logging
import os
from pathlib import Path
import tempfile
from typing import Any

import httpx

from settings import settings

# Agent container will be created by orchestrator when needed

logger = logging.getLogger(__name__)


class TelegramFileHandler:
    """Handler dla plików z Telegram."""

    def __init__(self, telegram_bot_handler):
        """Inicjalizuje handler plików.

        Args:
            telegram_bot_handler: Instancja TelegramBotHandler
        """
        self.bot_handler = telegram_bot_handler
        self.api_base_url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}"

        # Obsługiwane typy plików
        self.supported_types = {
            "photo": self._handle_photo,
            "document": self._handle_document,
            "voice": self._handle_voice,
            "video": self._handle_video,
            "audio": self._handle_audio,
        }

        # Rozszerzenia plików dla OCR
        self.ocr_extensions = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".pdf"}

    async def handle_file(self, message: dict[str, Any]) -> str | None:
        """Obsługuje plik z Telegram.

        Args:
            message: Wiadomość z Telegram zawierająca plik

        Returns:
            Odpowiedź na plik lub None jeśli nie obsługiwany
        """
        try:
            # Sprawdź typ pliku
            file_type = self._get_file_type(message)

            if file_type in self.supported_types:
                logger.info(
                    f"Processing {file_type} file from user {message['from']['id']}"
                )
                return await self.supported_types[file_type](message)
            else:
                return (
                    "❌ Nieobsługiwany typ pliku. Wspierane: zdjęcia, dokumenty, głos."
                )

        except Exception as e:
            logger.error(f"Error handling file: {e}")
            return "❌ Wystąpił błąd podczas przetwarzania pliku"

    def _get_file_type(self, message: dict[str, Any]) -> str | None:
        """Określa typ pliku w wiadomości."""
        if "photo" in message:
            return "photo"
        elif "document" in message:
            return "document"
        elif "voice" in message:
            return "voice"
        elif "video" in message:
            return "video"
        elif "audio" in message:
            return "audio"
        return None

    async def _handle_photo(self, message: dict[str, Any]) -> str:
        """Obsługuje zdjęcia (głównie paragony)."""
        try:
            # Pobierz największe zdjęcie (ostatnie w tablicy)
            photos = message["photo"]
            photo = photos[-1]  # Największe zdjęcie

            # Pobierz file_id
            file_id = photo["file_id"]

            # Pobierz informacje o pliku
            file_info = await self._get_file_info(file_id)
            if not file_info:
                return "❌ Nie udało się pobrać informacji o pliku"

            # Pobierz plik
            file_path = await self._download_file(file_info["file_path"])
            if not file_path:
                return "❌ Nie udało się pobrać pliku"

            # Analizuj przez OCR
            result = await self._analyze_receipt(file_path)

            # Usuń plik tymczasowy
            os.unlink(file_path)

            return result

        except Exception as e:
            logger.error(f"Error handling photo: {e}")
            return "❌ Wystąpił błąd podczas analizy zdjęcia"

    async def _handle_document(self, message: dict[str, Any]) -> str:
        """Obsługuje dokumenty (PDF, etc.)."""
        try:
            document = message["document"]
            file_id = document["file_id"]
            file_name = document.get("file_name", "unknown")

            # Sprawdź rozszerzenie
            file_ext = Path(file_name).suffix.lower()
            if file_ext not in self.ocr_extensions:
                return f"❌ Nieobsługiwany format pliku: {file_ext}. Wspierane: {', '.join(self.ocr_extensions)}"

            # Pobierz informacje o pliku
            file_info = await self._get_file_info(file_id)
            if not file_info:
                return "❌ Nie udało się pobrać informacji o pliku"

            # Pobierz plik
            file_path = await self._download_file(file_info["file_path"])
            if not file_path:
                return "❌ Nie udało się pobrać pliku"

            # Analizuj przez OCR
            result = await self._analyze_receipt(file_path)

            # Usuń plik tymczasowy
            os.unlink(file_path)

            return result

        except Exception as e:
            logger.error(f"Error handling document: {e}")
            return "❌ Wystąpił błąd podczas analizy dokumentu"

    async def _handle_voice(self, message: dict[str, Any]) -> str:
        """Obsługuje wiadomości głosowe."""
        try:
            voice = message["voice"]
            file_id = voice["file_id"]
            duration = voice.get("duration", 0)

            # Sprawdź długość (max 5 minut)
            if duration > 300:
                return "❌ Wiadomość głosowa jest za długa (max 5 minut)"

            # Pobierz informacje o pliku
            file_info = await self._get_file_info(file_id)
            if not file_info:
                return "❌ Nie udało się pobrać informacji o pliku"

            # Pobierz plik
            file_path = await self._download_file(file_info["file_path"])
            if not file_path:
                return "❌ Nie udało się pobrać pliku"

            # Konwertuj głos na tekst
            text = await self._convert_voice_to_text(file_path)

            # Usuń plik tymczasowy
            os.unlink(file_path)

            if text:
                return f"🎤 **Rozpoznany tekst:**\n\n{text}\n\n💬 Możesz teraz odpowiedzieć na to pytanie!"
            else:
                return "❌ Nie udało się rozpoznać tekstu z wiadomości głosowej"

        except Exception as e:
            logger.error(f"Error handling voice: {e}")
            return "❌ Wystąpił błąd podczas przetwarzania wiadomości głosowej"

    async def _handle_video(self, message: dict[str, Any]) -> str:
        """Obsługuje wideo."""
        return "❌ Obsługa wideo nie jest jeszcze zaimplementowana"

    async def _handle_audio(self, message: dict[str, Any]) -> str:
        """Obsługuje pliki audio."""
        return "❌ Obsługa plików audio nie jest jeszcze zaimplementowana"

    async def _get_file_info(self, file_id: str) -> dict[str, Any] | None:
        """Pobiera informacje o pliku z Telegram API."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.api_base_url}/getFile", params={"file_id": file_id}
                )

                if response.status_code == 200:
                    data = response.json()
                    if data.get("ok"):
                        return data["result"]

                logger.error(f"Failed to get file info: {response.text}")
                return None

        except Exception as e:
            logger.error(f"Error getting file info: {e}")
            return None

    async def _download_file(self, file_path: str) -> str | None:
        """Pobiera plik z Telegram."""
        try:
            # Utwórz plik tymczasowy
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".tmp")
            temp_path = temp_file.name
            temp_file.close()

            # Pobierz plik
            file_url = f"https://api.telegram.org/file/bot{settings.TELEGRAM_BOT_TOKEN}/{file_path}"

            async with httpx.AsyncClient() as client:
                response = await client.get(file_url)

                if response.status_code == 200:
                    # Zapisz plik
                    with open(temp_path, "wb") as f:
                        f.write(response.content)

                    logger.info(f"File downloaded to {temp_path}")
                    return temp_path
                else:
                    logger.error(f"Failed to download file: {response.status_code}")
                    return None

        except Exception as e:
            logger.error(f"Error downloading file: {e}")
            return None

    async def _analyze_receipt(self, file_path: str) -> str:
        """Analizuje paragon przez OCR."""
        try:
            # Użyj orchestrator do analizy paragonu
            from agents.orchestrator_factory import create_orchestrator
            from infrastructure.database.database import get_db

            async for db in get_db():
                orchestrator = create_orchestrator(db)

                # Przetwórz paragon przez orchestrator
                response = await orchestrator.process_query(
                    query=f"Analizuj paragon z pliku: {file_path}",
                    session_id="telegram_receipt_analysis",
                )

                if response.success and response.data:
                    result = response.data
                else:
                    return "❌ Nie udało się przeanalizować paragonu. Upewnij się, że zdjęcie jest czytelne."

            if result and result.get("success"):
                return f"""📷 **Analiza paragonu:**

🏪 **Sklep:** {result.get('store_name', 'Nieznany')}
📅 **Data:** {result.get('date', 'Nieznana')}
💰 **Suma:** {result.get('total_amount', 'Nieznana')} zł

📋 **Produkty ({len(result.get('items', []))}):**
{self._format_receipt_items(result.get('items', []))}

💡 **Sugestie oszczędności:**
{result.get('suggestions', 'Brak sugestii')}"""
            else:
                return "❌ Nie udało się przeanalizować paragonu. Upewnij się, że zdjęcie jest czytelne."

        except Exception as e:
            logger.error(f"Error analyzing receipt: {e}")
            return "❌ Wystąpił błąd podczas analizy paragonu"

    async def _convert_voice_to_text(self, file_path: str) -> str | None:
        """Konwertuje głos na tekst."""
        try:
            # TODO: Implementacja konwersji głosu na tekst
            # Można użyć Whisper lub innego modelu
            return "Funkcja konwersji głosu na tekst w trakcie implementacji"

        except Exception as e:
            logger.error(f"Error converting voice to text: {e}")
            return None

    def _format_receipt_items(self, items: list[dict[str, Any]]) -> str:
        """Formatuje listę produktów z paragonu."""
        if not items:
            return "Brak produktów"

        formatted = []
        for item in items[:10]:  # Maksymalnie 10 produktów
            name = item.get("name", "Nieznany produkt")
            quantity = item.get("quantity", 1)
            price = item.get("total_price", 0)

            formatted.append(f"• {name} x{quantity} = {price:.2f} zł")

        if len(items) > 10:
            formatted.append(f"... i {len(items) - 10} więcej")

        return "\n".join(formatted)

    def get_supported_formats(self) -> dict[str, list[str]]:
        """Zwraca listę obsługiwanych formatów plików."""
        return {
            "zdjęcia": ["JPG", "JPEG", "PNG", "BMP", "TIFF"],
            "dokumenty": ["PDF"],
            "głos": ["OGG", "MP3", "WAV"],
            "wideo": ["MP4", "AVI", "MOV"],
            "audio": ["MP3", "WAV", "OGG"],
        }
