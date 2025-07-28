"""
Unit tests for Telegram Command Handler.

This module contains unit tests for the Telegram command system,
testing command parsing, handling, and responses.
"""

from unittest.mock import AsyncMock, Mock

import pytest

from backend.integrations.telegram_commands import CommandType, TelegramCommandHandler


class TestTelegramCommandHandler:
    """Test cases for TelegramCommandHandler."""

    @pytest.fixture
    def mock_bot_handler(self):
        """Mock bot handler for testing."""
        mock = Mock()
        mock._process_with_ai = AsyncMock(return_value="AI response")
        return mock

    @pytest.fixture
    def command_handler(self, mock_bot_handler):
        """Command handler instance for testing."""
        return TelegramCommandHandler(mock_bot_handler)

    @pytest.fixture
    def sample_message(self):
        """Sample Telegram message for testing."""
        return {
            "message_id": 1,
            "from": {"id": 123456789, "first_name": "Test", "username": "testuser"},
            "chat": {"id": 123456789, "type": "private"},
            "text": "/start",
            "date": 1234567890,
        }

    def test_init(self, mock_bot_handler):
        """Test command handler initialization."""
        handler = TelegramCommandHandler(mock_bot_handler)

        assert handler.bot_handler == mock_bot_handler
        assert "/start" in handler.commands
        assert "/help" in handler.commands
        assert "/receipt" in handler.commands
        assert "/recipe" in handler.commands

    @pytest.mark.asyncio
    async def test_handle_command_start(self, command_handler, sample_message):
        """Test handling /start command."""
        response = await command_handler.handle_command(sample_message)

        assert response is not None
        assert "Witaj w FoodSave AI Assistant" in response
        assert "/help" in response
        assert "/receipt" in response

    @pytest.mark.asyncio
    async def test_handle_command_help(self, command_handler, sample_message):
        """Test handling /help command."""
        sample_message["text"] = "/help"
        response = await command_handler.handle_command(sample_message)

        assert response is not None
        assert "Dostępne komendy" in response
        assert "/start" in response
        assert "/receipt" in response

    @pytest.mark.asyncio
    async def test_handle_command_receipt(self, command_handler, sample_message):
        """Test handling /receipt command."""
        sample_message["text"] = "/receipt"
        response = await command_handler.handle_command(sample_message)

        assert response is not None
        assert "Analiza paragonów" in response
        assert "Zrób zdjęcie paragonu" in response

    @pytest.mark.asyncio
    async def test_handle_command_recipe_with_args(
        self, command_handler, sample_message, mock_bot_handler
    ):
        """Test handling /recipe command with arguments."""
        sample_message["text"] = "/recipe jajka mleko"
        mock_bot_handler._process_with_ai.return_value = "Przepis na jajecznicę"

        response = await command_handler.handle_command(sample_message)

        assert response is not None
        assert "Przepis dla: jajka mleko" in response
        assert "Przepis na jajecznicę" in response

    @pytest.mark.asyncio
    async def test_handle_command_recipe_without_args(
        self, command_handler, sample_message
    ):
        """Test handling /recipe command without arguments."""
        sample_message["text"] = "/recipe"
        response = await command_handler.handle_command(sample_message)

        assert response is not None
        assert "Wyszukiwanie przepisów" in response
        assert "Użyj: /recipe [składniki]" in response

    @pytest.mark.asyncio
    async def test_handle_command_search_with_args(
        self, command_handler, sample_message, mock_bot_handler
    ):
        """Test handling /search command with arguments."""
        sample_message["text"] = "/search przepis na pierogi"
        mock_bot_handler._process_with_ai.return_value = "Wyniki wyszukiwania"

        response = await command_handler.handle_command(sample_message)

        assert response is not None
        assert "Wyniki wyszukiwania dla: przepis na pierogi" in response

    @pytest.mark.asyncio
    async def test_handle_command_search_without_args(
        self, command_handler, sample_message
    ):
        """Test handling /search command without arguments."""
        sample_message["text"] = "/search"
        response = await command_handler.handle_command(sample_message)

        assert response is not None
        assert "Wyszukiwanie informacji" in response
        assert "Użyj: /search [zapytanie]" in response

    @pytest.mark.asyncio
    async def test_handle_command_stats(self, command_handler, sample_message):
        """Test handling /stats command."""
        sample_message["text"] = "/stats"
        response = await command_handler.handle_command(sample_message)

        assert response is not None
        assert "Twoje statystyki" in response
        assert "Wiadomości wysłane" in response

    @pytest.mark.asyncio
    async def test_handle_command_status(self, command_handler, sample_message):
        """Test handling /status command."""
        sample_message["text"] = "/status"
        response = await command_handler.handle_command(sample_message)

        assert response is not None
        assert "Status systemu" in response
        assert "AI Assistant" in response
        assert "Aktywny" in response

    @pytest.mark.asyncio
    async def test_handle_command_pantry(self, command_handler, sample_message):
        """Test handling /pantry command."""
        sample_message["text"] = "/pantry"
        response = await command_handler.handle_command(sample_message)

        assert response is not None
        assert "Stan spiżarni" in response
        assert "Funkcja w trakcie implementacji" in response

    @pytest.mark.asyncio
    async def test_handle_command_weather(self, command_handler, sample_message):
        """Test handling /weather command."""
        sample_message["text"] = "/weather"
        response = await command_handler.handle_command(sample_message)

        assert response is not None
        assert "Sprawdzanie pogody" in response
        assert "Funkcja w trakcie implementacji" in response

    @pytest.mark.asyncio
    async def test_handle_command_settings(self, command_handler, sample_message):
        """Test handling /settings command."""
        sample_message["text"] = "/settings"
        response = await command_handler.handle_command(sample_message)

        assert response is not None
        assert "Ustawienia" in response
        assert "Funkcja w trakcie implementacji" in response

    @pytest.mark.asyncio
    async def test_handle_command_expenses(self, command_handler, sample_message):
        """Test handling /expenses command."""
        sample_message["text"] = "/expenses"
        response = await command_handler.handle_command(sample_message)

        assert response is not None
        assert "Ostatnie wydatki" in response
        assert "Funkcja w trakcie implementacji" in response

    @pytest.mark.asyncio
    async def test_handle_command_add_with_args(self, command_handler, sample_message):
        """Test handling /add command with arguments."""
        sample_message["text"] = "/add mleko 2L"
        response = await command_handler.handle_command(sample_message)

        assert response is not None
        assert "Dodano do spiżarni: mleko 2L" in response

    @pytest.mark.asyncio
    async def test_handle_command_add_without_args(
        self, command_handler, sample_message
    ):
        """Test handling /add command without arguments."""
        sample_message["text"] = "/add"
        response = await command_handler.handle_command(sample_message)

        assert response is not None
        assert "Dodawanie produktów" in response
        assert "Użyj: /add [produkt] [ilość]" in response

    @pytest.mark.asyncio
    async def test_handle_unknown_command(self, command_handler, sample_message):
        """Test handling unknown command."""
        sample_message["text"] = "/unknown"
        response = await command_handler.handle_command(sample_message)

        assert response is not None
        assert "Nieznana komenda" in response
        assert "/help" in response

    @pytest.mark.asyncio
    async def test_handle_non_command_message(self, command_handler, sample_message):
        """Test handling non-command message."""
        sample_message["text"] = "Hello world"
        response = await command_handler.handle_command(sample_message)

        assert response is None

    @pytest.mark.asyncio
    async def test_handle_command_with_error(
        self, command_handler, sample_message, mock_bot_handler
    ):
        """Test handling command with error."""
        sample_message["text"] = "/recipe test"
        mock_bot_handler._process_with_ai.side_effect = Exception("Test error")

        response = await command_handler.handle_command(sample_message)

        assert response is not None
        assert "Wystąpił błąd podczas przetwarzania komendy" in response

    def test_update_usage_stats(self, command_handler):
        """Test updating usage statistics."""
        user_id = 123456789
        command = "/start"

        command_handler._update_usage_stats(command, user_id)

        assert command in command_handler.command_usage
        assert command_handler.command_usage[command] == 1
        assert user_id in command_handler.user_activity
        assert command_handler.user_activity[user_id] == 1

    def test_get_user_stats(self, command_handler):
        """Test getting user statistics."""
        user_id = 123456789
        command_handler.user_activity[user_id] = 5
        command_handler.command_usage["/start"] = 2
        command_handler.command_usage["/help"] = 1

        stats = command_handler.get_user_stats(user_id)

        assert stats["messages_sent"] == 5
        assert "/start" in stats["commands_used"]
        assert stats["commands_used"]["/start"] == 2
        assert "last_activity" in stats

    def test_format_command_stats(self, command_handler):
        """Test formatting command statistics."""
        command_handler.command_usage = {
            "/start": 5,
            "/help": 3,
            "/receipt": 2,
            "/recipe": 1,
        }

        formatted = command_handler._format_command_stats(command_handler.command_usage)

        assert "• /start: 5x" in formatted
        assert "• /help: 3x" in formatted
        assert "• /receipt: 2x" in formatted

    def test_format_command_stats_empty(self, command_handler):
        """Test formatting empty command statistics."""
        formatted = command_handler._format_command_stats({})

        assert formatted == "Brak danych"

    def test_get_daily_stats(self, command_handler):
        """Test getting daily statistics."""
        command_handler.command_usage = {"/start": 5, "/help": 3}
        command_handler.user_activity = {123: 1, 456: 1}

        stats = command_handler.get_daily_stats()

        assert "date" in stats
        assert stats["total_commands"] == 8
        assert stats["active_users"] == 2
        assert stats["most_used_command"] == "/start"


class TestCommandType:
    """Test cases for CommandType enum."""

    def test_command_types(self):
        """Test all command types are defined."""
        assert CommandType.START == "start"
        assert CommandType.HELP == "help"
        assert CommandType.RECEIPT == "receipt"
        assert CommandType.PANTRY == "pantry"
        assert CommandType.RECIPE == "recipe"
        assert CommandType.WEATHER == "weather"
        assert CommandType.SEARCH == "search"
        assert CommandType.SETTINGS == "settings"
        assert CommandType.STATS == "stats"
        assert CommandType.STATUS == "status"
        assert CommandType.EXPENSES == "expenses"
        assert CommandType.ADD == "add"
