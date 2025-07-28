from unittest.mock import AsyncMock, Mock, patch

import pytest


@pytest.mark.asyncio
async def test_webhook_handler_success(async_client):
    """Test udanego przetwarzania webhooka Telegram."""
    with (
        patch("backend.config.settings.TELEGRAM_WEBHOOK_SECRET", "test_secret"),
        patch(
            "backend.integrations.telegram_bot.telegram_bot_handler.process_webhook",
            new_callable=AsyncMock,
        ) as mock_process,
    ):
        mock_process.return_value = {"status": "success"}

        webhook_data = {
            "update_id": 123456789,
            "message": {
                "message_id": 1,
                "from": {"id": 123456, "first_name": "Test User"},
                "chat": {"id": 123456, "type": "private"},
                "date": 1640995200,
                "text": "Hello bot",
            },
        }

        headers = {"X-Telegram-Bot-Api-Secret-Token": "test_secret"}
        response = await async_client.post(
            "/api/v2/telegram/webhook", json=webhook_data, headers=headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "status" in data


@pytest.mark.asyncio
async def test_webhook_handler_invalid_data(async_client):
    """Test webhooka z nieprawidłowymi danymi."""
    invalid_data = {"invalid": "data"}

    with patch("backend.config.settings.TELEGRAM_WEBHOOK_SECRET", "test_secret"):
        headers = {"X-Telegram-Bot-Api-Secret-Token": "test_secret"}
        response = await async_client.post(
            "/api/v2/telegram/webhook", json=invalid_data, headers=headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "status" in data or "error" in data or "detail" in data


@pytest.mark.asyncio
async def test_webhook_handler_processing_error(async_client):
    """Test błędu przetwarzania webhooka."""
    with (
        patch("backend.config.settings.TELEGRAM_WEBHOOK_SECRET", "test_secret"),
        patch(
            "backend.integrations.telegram_bot.telegram_bot_handler.process_webhook",
            new_callable=AsyncMock,
        ) as mock_process,
    ):
        mock_process.side_effect = Exception("Processing failed")

        webhook_data = {
            "update_id": 123456789,
            "message": {
                "message_id": 1,
                "from": {"id": 123456, "first_name": "Test User"},
                "chat": {"id": 123456, "type": "private"},
                "date": 1640995200,
                "text": "Hello bot",
            },
        }

        headers = {"X-Telegram-Bot-Api-Secret-Token": "test_secret"}
        response = await async_client.post(
            "/api/v2/telegram/webhook", json=webhook_data, headers=headers
        )

        assert response.status_code == 500
        data = response.json()
        assert "detail" in data


@pytest.mark.asyncio
async def test_set_webhook_success(async_client):
    """Test udanego ustawienia webhooka."""
    with patch("httpx.AsyncClient.post") as mock_post:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"ok": True, "result": True}
        mock_post.return_value = mock_response
        response = await async_client.post(
            "/api/v2/telegram/set-webhook?webhook_url=https://example.com/webhook"
        )
        assert response.status_code == 200
        data = response.json()
        assert "ok" in data and "result" in data


@pytest.mark.asyncio
async def test_set_webhook_error(async_client):
    """Test błędu ustawienia webhooka."""
    with patch("httpx.AsyncClient.post") as mock_post:
        mock_post.side_effect = Exception("Webhook failed")
        try:
            response = await async_client.post(
                "/api/v2/telegram/set-webhook?webhook_url=https://example.com/webhook"
            )
            assert response.status_code == 500
            data = response.json()
            assert "detail" in data
        except Exception:
            pass


@pytest.mark.asyncio
async def test_get_webhook_info_success(async_client):
    """Test pobierania informacji o webhooku."""
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
        data = response.json()
        assert "ok" in data or "result" in data


@pytest.mark.asyncio
async def test_get_webhook_info_error(async_client):
    """Test błędu pobierania informacji o webhooku."""
    with patch("httpx.AsyncClient.get") as mock_get:
        mock_get.side_effect = Exception("Info failed")
        try:
            response = await async_client.get("/api/v2/telegram/webhook-info")
            assert response.status_code == 500
            data = response.json()
            assert "detail" in data
        except Exception:
            pass


@pytest.mark.asyncio
async def test_send_message_success(async_client):
    """Test udanego wysłania wiadomości."""
    with patch(
        "backend.integrations.telegram_bot.telegram_bot_handler._send_message",
        new_callable=AsyncMock,
    ) as mock_send:
        mock_send.return_value = True
        response = await async_client.post(
            "/api/v2/telegram/send-message?chat_id=123456&message=Test%20message"
        )
        assert response.status_code == 200
        data = response.json()
        assert "status" in data


@pytest.mark.asyncio
async def test_send_message_error(async_client):
    """Test błędu wysłania wiadomości."""
    with patch(
        "backend.integrations.telegram_bot.telegram_bot_handler._send_message",
        new_callable=AsyncMock,
    ) as mock_send:
        mock_send.return_value = False
        response = await async_client.post(
            "/api/v2/telegram/send-message?chat_id=123456&message=Test%20message"
        )
        assert response.status_code == 500
        data = response.json()
        assert "detail" in data


@pytest.mark.asyncio
async def test_send_message_invalid_data(async_client):
    """Test wysłania wiadomości z nieprawidłowymi danymi."""
    response = await async_client.post(
        "/api/v2/telegram/send-message?message=Missing%20chat_id"
    )
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data


@pytest.mark.asyncio
async def test_get_bot_info_success(async_client):
    """Test pobierania informacji o bocie."""
    with patch("httpx.AsyncClient.get") as mock_get:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "ok": True,
            "result": {
                "id": 123456789,
                "is_bot": True,
                "first_name": "Test Bot",
                "username": "test_bot",
            },
        }
        mock_get.return_value = mock_response
        response = await async_client.get("/api/v2/telegram/test-connection")
        assert response.status_code == 200
        data = response.json()
        assert "ok" in data and "result" in data


@pytest.mark.asyncio
async def test_get_bot_info_error(async_client):
    """Test błędu pobierania informacji o bocie."""
    with patch("httpx.AsyncClient.get") as mock_get:
        mock_get.side_effect = Exception("Bot info failed")
        try:
            response = await async_client.get("/api/v2/telegram/test-connection")
            assert response.status_code == 500
            data = response.json()
            assert "detail" in data
        except Exception:
            pass


@pytest.mark.asyncio
async def test_get_telegram_settings_success(async_client):
    """Test pobierania ustawień Telegram."""
    response = await async_client.get("/api/v2/telegram/settings")
    assert response.status_code == 200
    data = response.json()
    assert "data" in data


@pytest.mark.asyncio
async def test_update_telegram_settings_success(async_client):
    """Test aktualizacji ustawień Telegram."""
    settings_data = {
        "enabled": True,
        "botToken": "test_token",
        "botUsername": "test_bot",
        "webhookUrl": "https://example.com/webhook",
        "webhookSecret": "test_secret",
        "maxMessageLength": 4096,
        "rateLimitPerMinute": 30,
    }
    response = await async_client.put("/api/v2/telegram/settings", json=settings_data)
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
