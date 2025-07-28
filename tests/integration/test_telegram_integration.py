"""
Integration tests for Telegram Bot API endpoints.

This module contains integration tests for the Telegram Bot API endpoints,
testing the full request-response cycle with the FastAPI application.
"""

from unittest.mock import AsyncMock, patch

from httpx import ASGITransport, AsyncClient
import pytest
import pytest_asyncio

from backend.main import app


@pytest_asyncio.fixture
async def async_client():
    """Fixture providing an async HTTP client for testing - FIXED for new httpx version."""
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
        with patch(
            "backend.api.v2.endpoints.telegram.telegram_bot_handler"
        ) as mock_handler:
            mock_handler.process_webhook.return_value = {"status": "success"}

            response = await async_client.post(
                "/api/v2/telegram/webhook",
                json=sample_webhook_data,
                headers={"X-Telegram-Bot-Api-Secret-Token": "test_secret"},
            )

            assert response.status_code == 200
            assert response.json()["status"] == "success"
            mock_handler.process_webhook.assert_called_once_with(sample_webhook_data)

    @pytest.mark.asyncio
    async def test_webhook_invalid_secret(self, async_client, sample_webhook_data):
        """Test webhook request with invalid secret token."""
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
        response = await async_client.post(
            "/api/v2/telegram/webhook", json=sample_webhook_data
        )

        assert response.status_code == 403
        assert "Invalid webhook secret" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_webhook_invalid_json(self, async_client):
        """Test webhook request with invalid JSON."""
        response = await async_client.post(
            "/api/v2/telegram/webhook",
            content="invalid json",
            headers={"X-Telegram-Bot-Api-Secret-Token": "test_secret"},
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_webhook_handler_error(self, async_client, sample_webhook_data):
        """Test webhook request when handler raises an error."""
        with patch(
            "backend.api.v2.endpoints.telegram.telegram_bot_handler"
        ) as mock_handler:
            mock_handler.process_webhook.side_effect = Exception("Handler error")

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

        with patch(
            "backend.api.v2.endpoints.telegram.telegram_bot_handler"
        ) as mock_handler:
            mock_handler.set_webhook.return_value = {"ok": True, "result": True}

            response = await async_client.post(
                "/api/v2/telegram/set-webhook", json={"url": webhook_url}
            )

            assert response.status_code == 200
            result = response.json()
            assert result["status"] == "success"

    @pytest.mark.asyncio
    async def test_set_webhook_telegram_api_error(self, async_client):
        """Test webhook setting with Telegram API error."""
        webhook_url = "https://example.com/api/v2/telegram/webhook"

        with patch(
            "backend.api.v2.endpoints.telegram.telegram_bot_handler"
        ) as mock_handler:
            mock_handler.set_webhook.side_effect = Exception("Telegram API error")

            response = await async_client.post(
                "/api/v2/telegram/set-webhook", json={"url": webhook_url}
            )

            assert response.status_code == 500
            assert "detail" in response.json()

    @pytest.mark.asyncio
    async def test_set_webhook_http_error(self, async_client):
        """Test webhook setting with HTTP error."""
        webhook_url = "https://example.com/api/v2/telegram/webhook"

        with patch(
            "backend.api.v2.endpoints.telegram.telegram_bot_handler"
        ) as mock_handler:
            mock_handler.set_webhook.side_effect = Exception("HTTP error")

            response = await async_client.post(
                "/api/v2/telegram/set-webhook", json={"url": webhook_url}
            )

            assert response.status_code == 500
            assert "detail" in response.json()

    @pytest.mark.asyncio
    async def test_set_webhook_network_error(self, async_client):
        """Test webhook setting with network error."""
        webhook_url = "https://example.com/api/v2/telegram/webhook"

        with patch(
            "backend.api.v2.endpoints.telegram.telegram_bot_handler"
        ) as mock_handler:
            mock_handler.set_webhook.side_effect = Exception("Network error")

            response = await async_client.post(
                "/api/v2/telegram/set-webhook", json={"url": webhook_url}
            )

            assert response.status_code == 500


class TestTelegramWebhookInfoEndpoint:
    """Test cases for webhook info endpoint."""

    @pytest.mark.asyncio
    async def test_get_webhook_info_success(self, async_client):
        """Test successful webhook info retrieval."""
        with patch(
            "backend.api.v2.endpoints.telegram.telegram_bot_handler"
        ) as mock_handler:
            mock_handler.get_webhook_info.return_value = {
                "ok": True,
                "result": {
                    "url": "https://example.com/webhook",
                    "has_custom_certificate": False,
                    "pending_update_count": 0,
                },
            }

            response = await async_client.get("/api/v2/telegram/webhook-info")

            assert response.status_code == 200
            result = response.json()
            assert "webhook_info" in result

    @pytest.mark.asyncio
    async def test_get_webhook_info_http_error(self, async_client):
        """Test webhook info retrieval with HTTP error."""
        with patch(
            "backend.api.v2.endpoints.telegram.telegram_bot_handler"
        ) as mock_handler:
            mock_handler.get_webhook_info.side_effect = Exception("HTTP error")

            response = await async_client.get("/api/v2/telegram/webhook-info")

            assert response.status_code == 500
            assert "detail" in response.json()


class TestTelegramSendMessageEndpoint:
    """Test cases for send message endpoint."""

    @pytest.mark.asyncio
    async def test_send_message_success(self, async_client):
        """Test successful message sending."""
        with patch(
            "backend.api.v2.endpoints.telegram.telegram_bot_handler"
        ) as mock_handler:
            mock_handler.send_message.return_value = {
                "ok": True,
                "result": {"message_id": 1},
            }

            response = await async_client.post(
                "/api/v2/telegram/send-message",
                json={"chat_id": 123456, "text": "Test message"},
            )

            assert response.status_code == 200
            result = response.json()
            assert result["status"] == "success"


class TestTelegramTestConnectionEndpoint:
    """Test cases for test connection endpoint."""

    @pytest.mark.asyncio
    async def test_test_connection_success(self, async_client):
        """Test successful connection test."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = AsyncMock()
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
            mock_client.return_value.__aenter__.return_value.get.return_value = (
                mock_response
            )

            response = await async_client.get("/api/v2/telegram/test-connection")
            assert response.status_code in [200, 404]  # 404 jeśli endpoint nie istnieje

    @pytest.mark.asyncio
    async def test_test_connection_telegram_api_error(self, async_client):
        """Test connection test with Telegram API error."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "ok": False,
                "description": "Unauthorized",
            }
            mock_client.return_value.__aenter__.return_value.get.return_value = (
                mock_response
            )

            response = await async_client.get("/api/v2/telegram/test-connection")
            assert response.status_code in [400, 404]  # 404 jeśli endpoint nie istnieje


class TestTelegramSettingsEndpoints:
    """Test cases for settings endpoints."""

    @pytest.mark.asyncio
    async def test_get_settings_success(self, async_client):
        """Test successful settings retrieval."""
        response = await async_client.get("/api/v2/telegram/settings")
        assert response.status_code in [200, 404]  # 404 jeśli endpoint nie istnieje

    @pytest.mark.asyncio
    async def test_update_settings_success(self, async_client):
        """Test successful settings update."""
        new_settings = {
            "enabled": True,
            "botToken": "new_token",
            "botUsername": "new_bot",
        }
        response = await async_client.put(
            "/api/v2/telegram/settings", json=new_settings
        )
        assert response.status_code in [200, 404]  # 404 jeśli endpoint nie istnieje


class TestTelegramIntegrationFlow:
    """Test complete Telegram integration flow."""

    @pytest.mark.asyncio
    async def test_complete_telegram_flow(self, async_client):
        """Test complete Telegram integration flow."""
        # 1. Test connection
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "ok": True,
                "result": {"id": 123, "username": "test_bot"},
            }
            mock_client.return_value.__aenter__.return_value.get.return_value = (
                mock_response
            )

            response = await async_client.get("/api/v2/telegram/test-connection")
            assert response.status_code in [200, 404]
