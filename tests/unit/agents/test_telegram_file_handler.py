"""
Unit tests for Telegram File Handler.

This module contains unit tests for the Telegram file handling system,
testing file processing, download, and analysis.
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from backend.integrations.telegram_file_handler import TelegramFileHandler


class TestTelegramFileHandler:
    """Test cases for TelegramFileHandler."""

    @pytest.fixture
    def mock_bot_handler(self):
        """Mock bot handler for testing."""
        mock = Mock()
        mock._send_message = AsyncMock()
        return mock

    @pytest.fixture
    def file_handler(self, mock_bot_handler):
        """File handler instance for testing."""
        return TelegramFileHandler(mock_bot_handler)

    @pytest.fixture
    def sample_photo_message(self):
        """Sample Telegram message with photo."""
        return {
            "message_id": 1,
            "from": {"id": 123456789, "first_name": "Test", "username": "testuser"},
            "chat": {"id": 123456789, "type": "private"},
            "photo": [
                {"file_id": "photo_small", "width": 90, "height": 90},
                {"file_id": "photo_medium", "width": 320, "height": 320},
                {"file_id": "photo_large", "width": 800, "height": 600},
            ],
            "date": 1234567890,
        }

    @pytest.fixture
    def sample_document_message(self):
        """Sample Telegram message with document."""
        return {
            "message_id": 1,
            "from": {"id": 123456789, "first_name": "Test", "username": "testuser"},
            "chat": {"id": 123456789, "type": "private"},
            "document": {
                "file_id": "doc_file_id",
                "file_name": "receipt.pdf",
                "mime_type": "application/pdf",
            },
            "date": 1234567890,
        }

    @pytest.fixture
    def sample_voice_message(self):
        """Sample Telegram message with voice."""
        return {
            "message_id": 1,
            "from": {"id": 123456789, "first_name": "Test", "username": "testuser"},
            "chat": {"id": 123456789, "type": "private"},
            "voice": {
                "file_id": "voice_file_id",
                "duration": 30,
                "mime_type": "audio/ogg",
            },
            "date": 1234567890,
        }

    def test_init(self, mock_bot_handler):
        """Test file handler initialization."""
        handler = TelegramFileHandler(mock_bot_handler)

        assert handler.bot_handler == mock_bot_handler
        assert "photo" in handler.supported_types
        assert "document" in handler.supported_types
        assert "voice" in handler.supported_types
        assert ".jpg" in handler.ocr_extensions
        assert ".pdf" in handler.ocr_extensions

    def test_get_file_type_photo(self, file_handler, sample_photo_message):
        """Test getting file type for photo."""
        file_type = file_handler._get_file_type(sample_photo_message)
        assert file_type == "photo"

    def test_get_file_type_document(self, file_handler, sample_document_message):
        """Test getting file type for document."""
        file_type = file_handler._get_file_type(sample_document_message)
        assert file_type == "document"

    def test_get_file_type_voice(self, file_handler, sample_voice_message):
        """Test getting file type for voice."""
        file_type = file_handler._get_file_type(sample_voice_message)
        assert file_type == "voice"

    def test_get_file_type_none(self, file_handler):
        """Test getting file type for message without file."""
        message = {"text": "Hello"}
        file_type = file_handler._get_file_type(message)
        assert file_type is None

    @pytest.mark.asyncio
    async def test_handle_file_photo(self, file_handler, sample_photo_message):
        """Test handling photo file."""
        with (
            patch.object(file_handler, "_get_file_info") as mock_get_info,
            patch.object(file_handler, "_download_file") as mock_download,
            patch.object(file_handler, "_analyze_receipt") as mock_analyze,
        ):

            mock_get_info.return_value = {"file_path": "test_path"}
            mock_download.return_value = "/tmp/test.jpg"
            mock_analyze.return_value = "Analiza paragonu"

            response = await file_handler.handle_file(sample_photo_message)

            assert response == "Analiza paragonu"
            mock_get_info.assert_called_once_with("photo_large")
            mock_download.assert_called_once_with("test_path")
            mock_analyze.assert_called_once_with("/tmp/test.jpg")

    @pytest.mark.asyncio
    async def test_handle_file_document(self, file_handler, sample_document_message):
        """Test handling document file."""
        with (
            patch.object(file_handler, "_get_file_info") as mock_get_info,
            patch.object(file_handler, "_download_file") as mock_download,
            patch.object(file_handler, "_analyze_receipt") as mock_analyze,
        ):

            mock_get_info.return_value = {"file_path": "test_path"}
            mock_download.return_value = "/tmp/test.pdf"
            mock_analyze.return_value = "Analiza dokumentu"

            response = await file_handler.handle_file(sample_document_message)

            assert response == "Analiza dokumentu"
            mock_get_info.assert_called_once_with("doc_file_id")
            mock_download.assert_called_once_with("test_path")
            mock_analyze.assert_called_once_with("/tmp/test.pdf")

    @pytest.mark.asyncio
    async def test_handle_file_voice(self, file_handler, sample_voice_message):
        """Test handling voice file."""
        with (
            patch.object(file_handler, "_get_file_info") as mock_get_info,
            patch.object(file_handler, "_download_file") as mock_download,
            patch.object(file_handler, "_convert_voice_to_text") as mock_convert,
        ):

            mock_get_info.return_value = {"file_path": "test_path"}
            mock_download.return_value = "/tmp/test.ogg"
            mock_convert.return_value = "Rozpoznany tekst"

            response = await file_handler.handle_file(sample_voice_message)

            assert "Rozpoznany tekst" in response
            mock_get_info.assert_called_once_with("voice_file_id")
            mock_download.assert_called_once_with("test_path")
            mock_convert.assert_called_once_with("/tmp/test.ogg")

    @pytest.mark.asyncio
    async def test_handle_file_unsupported(self, file_handler):
        """Test handling unsupported file type."""
        message = {"video": {"file_id": "video_id"}}
        response = await file_handler.handle_file(message)

        assert (
            response
            == "❌ Nieobsługiwany typ pliku. Wspierane: zdjęcia, dokumenty, głos."
        )

    @pytest.mark.asyncio
    async def test_handle_file_error(self, file_handler, sample_photo_message):
        """Test handling file with error."""
        with patch.object(
            file_handler, "_get_file_type", side_effect=Exception("Test error")
        ):
            response = await file_handler.handle_file(sample_photo_message)

            assert "Wystąpił błąd podczas przetwarzania pliku" in response

    @pytest.mark.asyncio
    async def test_handle_photo_success(self, file_handler, sample_photo_message):
        """Test successful photo handling."""
        with (
            patch.object(file_handler, "_get_file_info") as mock_get_info,
            patch.object(file_handler, "_download_file") as mock_download,
            patch.object(file_handler, "_analyze_receipt") as mock_analyze,
        ):

            mock_get_info.return_value = {"file_path": "test_path"}
            mock_download.return_value = "/tmp/test.jpg"
            mock_analyze.return_value = "Analiza paragonu"

            response = await file_handler._handle_photo(sample_photo_message)

            assert response == "Analiza paragonu"

    @pytest.mark.asyncio
    async def test_handle_photo_no_file_info(self, file_handler, sample_photo_message):
        """Test photo handling with no file info."""
        with patch.object(file_handler, "_get_file_info", return_value=None):
            response = await file_handler._handle_photo(sample_photo_message)

            assert "Nie udało się pobrać informacji o pliku" in response

    @pytest.mark.asyncio
    async def test_handle_photo_download_failed(
        self, file_handler, sample_photo_message
    ):
        """Test photo handling with download failure."""
        with (
            patch.object(file_handler, "_get_file_info") as mock_get_info,
            patch.object(file_handler, "_download_file", return_value=None),
        ):

            mock_get_info.return_value = {"file_path": "test_path"}
            response = await file_handler._handle_photo(sample_photo_message)

            assert "Nie udało się pobrać pliku" in response

    @pytest.mark.asyncio
    async def test_handle_document_success(self, file_handler, sample_document_message):
        """Test successful document handling."""
        with (
            patch.object(file_handler, "_get_file_info") as mock_get_info,
            patch.object(file_handler, "_download_file") as mock_download,
            patch.object(file_handler, "_analyze_receipt") as mock_analyze,
        ):

            mock_get_info.return_value = {"file_path": "test_path"}
            mock_download.return_value = "/tmp/test.pdf"
            mock_analyze.return_value = "Analiza dokumentu"

            response = await file_handler._handle_document(sample_document_message)

            assert response == "Analiza dokumentu"

    @pytest.mark.asyncio
    async def test_handle_document_unsupported_format(self, file_handler):
        """Test document handling with unsupported format."""
        message = {"document": {"file_id": "doc_file_id", "file_name": "test.txt"}}

        response = await file_handler._handle_document(message)

        assert "Nieobsługiwany format pliku" in response
        assert ".txt" in response

    @pytest.mark.asyncio
    async def test_handle_voice_success(self, file_handler, sample_voice_message):
        """Test successful voice handling."""
        with (
            patch.object(file_handler, "_get_file_info") as mock_get_info,
            patch.object(file_handler, "_download_file") as mock_download,
            patch.object(file_handler, "_convert_voice_to_text") as mock_convert,
        ):

            mock_get_info.return_value = {"file_path": "test_path"}
            mock_download.return_value = "/tmp/test.ogg"
            mock_convert.return_value = "Rozpoznany tekst"

            response = await file_handler._handle_voice(sample_voice_message)

            assert "Rozpoznany tekst" in response

    @pytest.mark.asyncio
    async def test_handle_voice_too_long(self, file_handler):
        """Test voice handling with too long duration."""
        message = {
            "voice": {"file_id": "voice_file_id", "duration": 400}  # Over 5 minutes
        }

        response = await file_handler._handle_voice(message)

        assert "Wiadomość głosowa jest za długa" in response

    @pytest.mark.asyncio
    async def test_handle_voice_no_text(self, file_handler, sample_voice_message):
        """Test voice handling with no recognized text."""
        with (
            patch.object(file_handler, "_get_file_info") as mock_get_info,
            patch.object(file_handler, "_download_file") as mock_download,
            patch.object(file_handler, "_convert_voice_to_text", return_value=None),
        ):

            mock_get_info.return_value = {"file_path": "test_path"}
            mock_download.return_value = "/tmp/test.ogg"

            response = await file_handler._handle_voice(sample_voice_message)

            assert "Nie udało się rozpoznać tekstu" in response

    @pytest.mark.asyncio
    async def test_get_file_info_success(self, file_handler):
        """Test successful file info retrieval."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "ok": True,
                "result": {"file_path": "test_path"},
            }

            mock_client_instance = Mock()
            mock_client_instance.__aenter__.return_value = mock_client_instance
            mock_client_instance.__aexit__.return_value = None
            mock_client_instance.get.return_value = mock_response
            mock_client.return_value = mock_client_instance

            result = await file_handler._get_file_info("test_file_id")

            assert result == {"file_path": "test_path"}

    @pytest.mark.asyncio
    async def test_get_file_info_failure(self, file_handler):
        """Test file info retrieval failure."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = Mock()
            mock_response.status_code = 400
            mock_response.text = "Bad Request"

            mock_client_instance = Mock()
            mock_client_instance.__aenter__.return_value = mock_client_instance
            mock_client_instance.__aexit__.return_value = None
            mock_client_instance.get.return_value = mock_response
            mock_client.return_value = mock_client_instance

            result = await file_handler._get_file_info("test_file_id")

            assert result is None

    @pytest.mark.asyncio
    async def test_download_file_success(self, file_handler):
        """Test successful file download."""
        with (
            patch("httpx.AsyncClient") as mock_client,
            patch("tempfile.NamedTemporaryFile") as mock_temp_file,
        ):

            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.content = b"test content"

            mock_temp_file_instance = Mock()
            mock_temp_file_instance.name = "/tmp/test_file"
            mock_temp_file_instance.close = Mock()
            mock_temp_file.return_value = mock_temp_file_instance

            mock_client_instance = Mock()
            mock_client_instance.__aenter__.return_value = mock_client_instance
            mock_client_instance.__aexit__.return_value = None
            mock_client_instance.get.return_value = mock_response
            mock_client.return_value = mock_client_instance

            result = await file_handler._download_file("test_path")

            assert result == "/tmp/test_file"

    @pytest.mark.asyncio
    async def test_download_file_failure(self, file_handler):
        """Test file download failure."""
        with (
            patch("httpx.AsyncClient") as mock_client,
            patch("tempfile.NamedTemporaryFile") as mock_temp_file,
        ):

            mock_response = Mock()
            mock_response.status_code = 404

            mock_temp_file_instance = Mock()
            mock_temp_file_instance.name = "/tmp/test_file"
            mock_temp_file_instance.close = Mock()
            mock_temp_file.return_value = mock_temp_file_instance

            mock_client_instance = Mock()
            mock_client_instance.__aenter__.return_value = mock_client_instance
            mock_client_instance.__aexit__.return_value = None
            mock_client_instance.get.return_value = mock_response
            mock_client.return_value = mock_client_instance

            result = await file_handler._download_file("test_path")

            assert result is None

    @pytest.mark.asyncio
    async def test_analyze_receipt_success(self, file_handler):
        """Test successful receipt analysis."""
        with patch(
            "backend.backend.agents.agent_container.agent_container"
        ) as mock_container:
            mock_agent = Mock()
            mock_agent.process = AsyncMock(
                return_value={
                    "success": True,
                    "store_name": "Biedronka",
                    "date": "2025-01-15",
                    "total_amount": 45.67,
                    "items": [{"name": "Mleko", "quantity": 2, "total_price": 9.98}],
                    "suggestions": "Kupuj w Lidl dla lepszych cen",
                }
            )
            mock_container.get_agent.return_value = mock_agent

            result = await file_handler._analyze_receipt("/tmp/test.jpg")

            assert "Analiza paragonu" in result
            assert "Biedronka" in result
            assert "45.67" in result
            assert "Mleko x2 = 9.98 zł" in result

    @pytest.mark.asyncio
    async def test_analyze_receipt_failure(self, file_handler):
        """Test receipt analysis failure."""
        with patch(
            "backend.backend.agents.agent_container.agent_container"
        ) as mock_container:
            mock_agent = Mock()
            mock_agent.process = AsyncMock(return_value={"success": False})
            mock_container.get_agent.return_value = mock_agent

            result = await file_handler._analyze_receipt("/tmp/test.jpg")

            assert "Nie udało się przeanalizować paragonu" in result

    def test_format_receipt_items(self, file_handler):
        """Test formatting receipt items."""
        items = [
            {"name": "Mleko", "quantity": 2, "total_price": 9.98},
            {"name": "Chleb", "quantity": 1, "total_price": 3.50},
            {"name": "Jajka", "quantity": 10, "total_price": 12.00},
        ]

        formatted = file_handler._format_receipt_items(items)

        assert "• Mleko x2 = 9.98 zł" in formatted
        assert "• Chleb x1 = 3.50 zł" in formatted
        assert "• Jajka x10 = 12.00 zł" in formatted

    def test_format_receipt_items_empty(self, file_handler):
        """Test formatting empty receipt items."""
        formatted = file_handler._format_receipt_items([])
        assert formatted == "Brak produktów"

    def test_format_receipt_items_many(self, file_handler):
        """Test formatting many receipt items (should truncate)."""
        items = [
            {"name": f"Item {i}", "quantity": 1, "total_price": 1.00} for i in range(15)
        ]

        formatted = file_handler._format_receipt_items(items)

        assert "• Item 0 x1 = 1.00 zł" in formatted
        assert "• Item 9 x1 = 1.00 zł" in formatted
        assert "... i 5 więcej" in formatted

    def test_get_supported_formats(self, file_handler):
        """Test getting supported file formats."""
        formats = file_handler.get_supported_formats()

        assert "zdjęcia" in formats
        assert "dokumenty" in formats
        assert "głos" in formats
        assert "JPG" in formats["zdjęcia"]
        assert "PDF" in formats["dokumenty"]
        assert "OGG" in formats["głos"]
