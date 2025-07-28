"""
Fixed integration tests for Telegram Bot API endpoints.

This module contains corrected integration tests for the Telegram Bot API endpoints,
testing the full request-response cycle with the FastAPI application.
"""

from unittest.mock import AsyncMock, Mock, patch

from httpx import ASGITransport, AsyncClient
import pytest
import pytest_asyncio

from backend.main import app


@pytest_asyncio.fixture
async def async_client():
    """Fixture providing an async HTTP client for testing."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac


@pytest.fixture
def sample_webhook_data():
    """Fixture providing sample webhook data for testing."""
    return {
        "update_id": 123456789,
        "message": {
            "message_id": 1,
            "from_user": {
                "id": 987654321,
                "first_name": "Test",
                "username": "testuser",
            },
            "chat": {"id": 987654321, "type": "private"},
            "text": "Cześć! Jak się masz?",
            "date": 1234567890,
        },
    }


class TestTelegramWebhookEndpoint:
    """Test cases for Telegram webhook endpoint."""

    @pytest.mark.asyncio
    async def test_webhook_valid_request(self, async_client, sample_webhook_data):
        """Test valid webhook request processing."""
        with patch("backend.settings.settings.TELEGRAM_WEBHOOK_SECRET", "test_secret"):
            with patch(
                "backend.integrations.telegram_bot.telegram_bot_handler.process_webhook",
                new_callable=AsyncMock,
            ) as mock_process:
                mock_process.return_value = {"status": "success"}

                response = await async_client.post(
                    "/api/v2/telegram/webhook",
                    json=sample_webhook_data,
                    headers={"X-Telegram-Bot-Api-Secret-Token": "test_secret"},
                )

                assert response.status_code == 200
                assert response.json()["status"] == "ok"
                mock_process.assert_called_once_with(sample_webhook_data)

    @pytest.mark.asyncio
    async def test_webhook_invalid_secret(self, async_client, sample_webhook_data):
        """Test webhook request with invalid secret token."""
        with patch(
            "backend.settings.settings.TELEGRAM_WEBHOOK_SECRET", "correct_secret"
        ):
            response = await async_client.post(
                "/api/v2/telegram/webhook",
                json=sample_webhook_data,
                headers={"X-Telegram-Bot-Api-Secret-Token": "wrong_secret"},
            )

            assert response.status_code == 403
            assert "Invalid webhook secret" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_webhook_missing_secret(self, async_client, sample_webhook_data):
        """Test webhook request without secret token."""
        with patch(
            "backend.settings.settings.TELEGRAM_WEBHOOK_SECRET", "correct_secret"
        ):
            response = await async_client.post(
                "/api/v2/telegram/webhook", json=sample_webhook_data
            )

            assert response.status_code == 403
            assert "Invalid webhook secret" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_webhook_invalid_json(self, async_client):
        """Test webhook request with invalid JSON."""
        with patch("backend.settings.settings.TELEGRAM_WEBHOOK_SECRET", "test_secret"):
            response = await async_client.post(
                "/api/v2/telegram/webhook",
                content="invalid json",
                headers={"X-Telegram-Bot-Api-Secret-Token": "test_secret"},
            )

            assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_webhook_handler_error(self, async_client, sample_webhook_data):
        """Test webhook request when handler raises an error."""
        with patch("backend.settings.settings.TELEGRAM_WEBHOOK_SECRET", "test_secret"):
            with patch(
                "backend.integrations.telegram_bot.telegram_bot_handler.process_webhook",
                new_callable=AsyncMock,
            ) as mock_process:
                mock_process.side_effect = Exception("Handler error")

                response = await async_client.post(
                    "/api/v2/telegram/webhook",
                    json=sample_webhook_data,
                    headers={"X-Telegram-Bot-Api-Secret-Token": "test_secret"},
                )

                assert response.status_code == 500
                assert "detail" in response.json()


class TestTelegramSetWebhookEndpoint:
    """Test cases for set webhook endpoint."""

    @pytest.mark.asyncio
    async def test_set_webhook_success(self, async_client):
        """Test successful webhook setting."""
        webhook_url = "https://example.com/api/v2/telegram/webhook"

        with patch("httpx.AsyncClient.post") as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"ok": True, "result": True}
            mock_post.return_value = mock_response

            response = await async_client.post(
                "/api/v2/telegram/set-webhook", params={"webhook_url": webhook_url}
            )

            assert response.status_code == 200
            result = response.json()
            assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_set_webhook_telegram_api_error(self, async_client):
        """Test webhook setting with Telegram API error."""
        webhook_url = "https://example.com/api/v2/telegram/webhook"

        with patch("httpx.AsyncClient.post") as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "ok": False,
                "description": "Invalid token",
            }
            mock_post.return_value = mock_response

            response = await async_client.post(
                "/api/v2/telegram/set-webhook", params={"webhook_url": webhook_url}
            )

            assert response.status_code == 400
            assert "Telegram API error" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_set_webhook_http_error(self, async_client):
        """Test webhook setting with HTTP error."""
        webhook_url = "https://example.com/api/v2/telegram/webhook"

        with patch("httpx.AsyncClient.post") as mock_post:
            mock_post.side_effect = Exception("HTTP error")

            response = await async_client.post(
                "/api/v2/telegram/set-webhook", params={"webhook_url": webhook_url}
            )

            assert response.status_code == 500
            assert "detail" in response.json()


class TestTelegramWebhookInfoEndpoint:
    """Test cases for webhook info endpoint."""

    @pytest.mark.asyncio
    async def test_get_webhook_info_success(self, async_client):
        """Test successful webhook info retrieval."""
        with patch("httpx.AsyncClient.get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "ok": True,
                "result": {
                    "url": "https://example.com/webhook",
                    "has_custom_certificate": False,
                    "pending_update_count": 0,
                },
            }
            mock_get.return_value = mock_response

            response = await async_client.get("/api/v2/telegram/webhook-info")

            assert response.status_code == 200
            result = response.json()
            assert "ok" in result
            assert "result" in result

    @pytest.mark.asyncio
    async def test_get_webhook_info_http_error(self, async_client):
        """Test webhook info retrieval with HTTP error."""
        with patch("httpx.AsyncClient.get") as mock_get:
            mock_get.side_effect = Exception("HTTP error")

            response = await async_client.get("/api/v2/telegram/webhook-info")

            assert response.status_code == 500
            assert "detail" in response.json()


class TestTelegramSendMessageEndpoint:
    """Test cases for send message endpoint."""

    @pytest.mark.asyncio
    async def test_send_message_success(self, async_client):
        """Test successful message sending."""
        with patch(
            "backend.integrations.telegram_bot.telegram_bot_handler._send_message",
            new_callable=AsyncMock,
        ) as mock_send:
            mock_send.return_value = True

            response = await async_client.post(
                "/api/v2/telegram/send-message",
                params={"chat_id": 123456, "message": "Test message"},
            )

            assert response.status_code == 200
            result = response.json()
            assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_send_message_failure(self, async_client):
        """Test failed message sending."""
        with patch(
            "backend.integrations.telegram_bot.telegram_bot_handler._send_message",
            new_callable=AsyncMock,
        ) as mock_send:
            mock_send.return_value = False

            response = await async_client.post(
                "/api/v2/telegram/send-message",
                params={"chat_id": 123456, "message": "Test message"},
            )

            assert response.status_code == 500
            assert "Failed to send message" in response.json()["detail"]


class TestTelegramTestConnectionEndpoint:
    """Test cases for test connection endpoint."""

    @pytest.mark.asyncio
    async def test_test_connection_success(self, async_client):
        """Test successful connection test."""
        with patch("httpx.AsyncClient.get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "ok": True,
                "result": {
                    "id": 123456789,
                    "is_bot": True,
                    "first_name": "FoodSave AI Bot",
                    "username": "foodsave_ai_bot",
                },
            }
            mock_get.return_value = mock_response

            response = await async_client.get("/api/v2/telegram/test-connection")

            assert response.status_code == 200
            result = response.json()
            assert result["status"] == "success"
            assert "bot_info" in result

    @pytest.mark.asyncio
    async def test_test_connection_telegram_api_error(self, async_client):
        """Test connection test with Telegram API error."""
        with patch("httpx.AsyncClient.get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "ok": False,
                "description": "Unauthorized",
            }
            mock_get.return_value = mock_response

            response = await async_client.get("/api/v2/telegram/test-connection")

            assert response.status_code == 400
            assert "Telegram API error" in response.json()["detail"]


class TestTelegramSettingsEndpoints:
    """Test cases for settings endpoints."""

    @pytest.mark.asyncio
    async def test_get_settings_success(self, async_client):
        """Test successful settings retrieval."""
        response = await async_client.get("/api/v2/telegram/settings")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "data" in data

    @pytest.mark.asyncio
    async def test_update_settings_success(self, async_client):
        """Test successful settings update."""
        settings_data = {
            "enabled": True,
            "botToken": "test_token",
            "botUsername": "test_bot",
            "webhookUrl": "https://example.com/webhook",
            "webhookSecret": "test_secret",
            "maxMessageLength": 4096,
            "rateLimitPerMinute": 30,
        }

        response = await async_client.put(
            "/api/v2/telegram/settings", json=settings_data
        )
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "data" in data


class TestTelegramIntegrationFlow:
    """Test complete Telegram integration flow."""

    @pytest.mark.asyncio
    async def test_complete_telegram_flow(self, async_client):
        """Test complete Telegram integration flow."""
        # 1. Test connection
        with patch("httpx.AsyncClient.get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "ok": True,
                "result": {"id": 123, "username": "test_bot"},
            }
            mock_get.return_value = mock_response

            response = await async_client.get("/api/v2/telegram/test-connection")
            assert response.status_code == 200

        # 2. Test settings
        response = await async_client.get("/api/v2/telegram/settings")
        assert response.status_code == 200

        # 3. Test webhook info
        with patch("httpx.AsyncClient.get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "ok": True,
                "result": {"url": "", "pending_update_count": 0},
            }
            mock_get.return_value = mock_response

            response = await async_client.get("/api/v2/telegram/webhook-info")
            assert response.status_code == 200
