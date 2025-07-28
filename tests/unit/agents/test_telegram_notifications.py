"""
Unit tests for Telegram Notification System.

This module contains unit tests for the Telegram notification system,
testing broadcast, alerts, and daily summaries.
"""

from unittest.mock import AsyncMock, Mock

import pytest

from backend.integrations.telegram_notifications import TelegramNotificationSystem


class TestTelegramNotificationSystem:
    """Test cases for TelegramNotificationSystem."""

    @pytest.fixture
    def mock_bot_handler(self):
        """Mock bot handler for testing."""
        mock = Mock()
        mock._send_message = AsyncMock(return_value=True)
        return mock

    @pytest.fixture
    def notification_system(self, mock_bot_handler):
        """Notification system instance for testing."""
        return TelegramNotificationSystem(mock_bot_handler)

    def test_init(self, mock_bot_handler):
        """Test notification system initialization."""
        system = TelegramNotificationSystem(mock_bot_handler)

        assert system.bot_handler == mock_bot_handler
        assert len(system.subscribed_users) == 0
        assert len(system.notification_history) == 0
        assert system.notification_settings["daily_summary"] is True
        assert system.notification_settings["system_alerts"] is True

    @pytest.mark.asyncio
    async def test_broadcast_message_success(self, notification_system):
        """Test successful broadcast message."""
        notification_system.subscribed_users.add(123)
        notification_system.subscribed_users.add(456)

        result = await notification_system.broadcast_message("Test message")

        assert result["success"] is True
        assert result["sent"] == 2
        assert result["errors"] == 0
        assert len(result["error_details"]) == 0

    @pytest.mark.asyncio
    async def test_broadcast_message_no_users(self, notification_system):
        """Test broadcast message with no users."""
        result = await notification_system.broadcast_message("Test message")

        assert result["success"] is False
        assert "Brak użytkowników do powiadomienia" in result["error"]

    @pytest.mark.asyncio
    async def test_broadcast_message_with_errors(
        self, notification_system, mock_bot_handler
    ):
        """Test broadcast message with some errors."""
        notification_system.subscribed_users.add(123)
        notification_system.subscribed_users.add(456)

        # Make one send fail
        mock_bot_handler._send_message.side_effect = [True, Exception("Test error")]

        result = await notification_system.broadcast_message("Test message")

        assert result["success"] is True
        assert result["sent"] == 1
        assert result["errors"] == 1
        assert len(result["error_details"]) == 1

    @pytest.mark.asyncio
    async def test_broadcast_message_specific_users(self, notification_system):
        """Test broadcast message to specific users."""
        user_ids = [123, 456, 789]

        result = await notification_system.broadcast_message("Test message", user_ids)

        assert result["success"] is True
        assert result["sent"] == 3
        assert result["errors"] == 0

    @pytest.mark.asyncio
    async def test_send_system_alert_normal(self, notification_system):
        """Test sending normal priority system alert."""
        notification_system.subscribed_users.add(123)
        notification_system.subscribed_users.add(456)
        notification_system.subscribed_users.add(789)

        result = await notification_system.send_system_alert(
            "test", "Test alert", "normal"
        )

        assert result["success"] is True
        # Should send to 50% of users (1-2 users)
        assert result["sent"] >= 1
        assert result["sent"] <= 2

    @pytest.mark.asyncio
    async def test_send_system_alert_high(self, notification_system):
        """Test sending high priority system alert."""
        notification_system.subscribed_users.add(123)
        notification_system.subscribed_users.add(456)
        notification_system.subscribed_users.add(789)
        notification_system.subscribed_users.add(101)
        notification_system.subscribed_users.add(102)

        result = await notification_system.send_system_alert(
            "test", "Test alert", "high"
        )

        assert result["success"] is True
        # Should send to 80% of users (4 users)
        assert result["sent"] == 4

    @pytest.mark.asyncio
    async def test_send_system_alert_critical(self, notification_system):
        """Test sending critical priority system alert."""
        notification_system.subscribed_users.add(123)
        notification_system.subscribed_users.add(456)

        result = await notification_system.send_system_alert(
            "test", "Test alert", "critical"
        )

        assert result["success"] is True
        # Should send to all users
        assert result["sent"] == 2

    @pytest.mark.asyncio
    async def test_send_daily_summary(self, notification_system):
        """Test sending daily summary."""
        notification_system.subscribed_users.add(123)
        notification_system.subscribed_users.add(456)

        result = await notification_system.send_daily_summary()

        assert result["success"] is True
        assert result["sent"] == 2
        assert result["errors"] == 0

    @pytest.mark.asyncio
    async def test_send_receipt_analysis_notification(self, notification_system):
        """Test sending receipt analysis notification."""
        receipt_data = {
            "store_name": "Biedronka",
            "total_amount": 45.67,
            "date": "2025-01-15",
            "items": [{"name": "Mleko", "quantity": 2, "total_price": 9.98}],
            "suggestions": "Kupuj w Lidl dla lepszych cen",
        }

        result = await notification_system.send_receipt_analysis_notification(
            123, receipt_data
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_send_expense_alert(self, notification_system):
        """Test sending expense alert."""
        expense_data = {
            "store_name": "Lidl",
            "amount": 89.99,
            "date": "2025-01-15",
            "suggestions": "Rozważ zakupy w Biedronce",
        }

        result = await notification_system.send_expense_alert(123, expense_data)

        assert result is True

    @pytest.mark.asyncio
    async def test_send_weather_alert(self, notification_system):
        """Test sending weather alert."""
        weather_data = {
            "location": "Warszawa",
            "temperature": 25,
            "precipitation": "Brak",
            "warnings": "Uwaga na upał",
        }

        result = await notification_system.send_weather_alert(123, weather_data)

        assert result is True

    def test_format_alert_message(self, notification_system):
        """Test formatting alert message."""
        message = notification_system._format_alert_message(
            "test", "Test alert", "normal"
        )

        assert "⚠️" in message
        assert "Alert Systemowy - TEST" in message
        assert "Test alert" in message
        assert "Priorytet: NORMAL" in message

    def test_format_alert_message_critical(self, notification_system):
        """Test formatting critical alert message."""
        message = notification_system._format_alert_message(
            "test", "Test alert", "critical"
        )

        assert "🚨🚨" in message
        assert "Priorytet: CRITICAL" in message

    def test_format_daily_summary(self, notification_system):
        """Test formatting daily summary."""
        stats = {
            "messages_processed": 150,
            "receipts_analyzed": 25,
            "recipes_searched": 30,
            "daily_expenses": 245.67,
            "savings": 45.23,
            "active_users": 45,
            "new_users": 3,
            "suggestions": "Test suggestions",
        }

        summary = notification_system._format_daily_summary(stats)

        assert "Dzienne Podsumowanie" in summary
        assert "150" in summary
        assert "25" in summary
        assert "245.67" in summary
        assert "Test suggestions" in summary

    def test_format_receipt_notification(self, notification_system):
        """Test formatting receipt notification."""
        receipt_data = {
            "store_name": "Biedronka",
            "total_amount": 45.67,
            "date": "2025-01-15",
            "items": [{"name": "Mleko", "quantity": 2, "total_price": 9.98}],
            "suggestions": "Kupuj w Lidl dla lepszych cen",
        }

        notification = notification_system._format_receipt_notification(receipt_data)

        assert "Analiza paragonu zakończona" in notification
        assert "Biedronka" in notification
        assert "45.67" in notification
        assert "1 pozycji" in notification

    def test_format_expense_alert(self, notification_system):
        """Test formatting expense alert."""
        expense_data = {
            "store_name": "Lidl",
            "amount": 89.99,
            "date": "2025-01-15",
            "suggestions": "Rozważ zakupy w Biedronce",
        }

        alert = notification_system._format_expense_alert(expense_data)

        assert "Alert Wydatków" in alert
        assert "Wykryto wysokie wydatki" in alert
        assert "Lidl" in alert
        assert "89.99" in alert

    def test_format_weather_alert(self, notification_system):
        """Test formatting weather alert."""
        weather_data = {
            "location": "Warszawa",
            "temperature": 25,
            "precipitation": "Brak",
            "warnings": "Uwaga na upał",
        }

        alert = notification_system._format_weather_alert(weather_data)

        assert "Alert Pogodowy" in alert
        assert "Warszawa" in alert
        assert "25" in alert
        assert "Uwaga na upał" in alert

    def test_get_users_for_alert_critical(self, notification_system):
        """Test getting users for critical alert."""
        notification_system.subscribed_users.add(123)
        notification_system.subscribed_users.add(456)
        notification_system.subscribed_users.add(789)

        users = notification_system._get_users_for_alert("critical")

        assert len(users) == 3
        assert 123 in users
        assert 456 in users
        assert 789 in users

    def test_get_users_for_alert_high(self, notification_system):
        """Test getting users for high priority alert."""
        notification_system.subscribed_users.add(123)
        notification_system.subscribed_users.add(456)
        notification_system.subscribed_users.add(789)
        notification_system.subscribed_users.add(101)
        notification_system.subscribed_users.add(102)

        users = notification_system._get_users_for_alert("high")

        assert len(users) == 4  # 80% of 5 users

    def test_get_users_for_alert_normal(self, notification_system):
        """Test getting users for normal priority alert."""
        notification_system.subscribed_users.add(123)
        notification_system.subscribed_users.add(456)
        notification_system.subscribed_users.add(789)
        notification_system.subscribed_users.add(101)
        notification_system.subscribed_users.add(102)

        users = notification_system._get_users_for_alert("normal")

        assert len(users) == 2  # 50% of 5 users

    @pytest.mark.asyncio
    async def test_get_daily_stats(self, notification_system):
        """Test getting daily stats."""
        stats = await notification_system._get_daily_stats()

        assert "messages_processed" in stats
        assert "receipts_analyzed" in stats
        assert "recipes_searched" in stats
        assert "daily_expenses" in stats
        assert "savings" in stats
        assert "active_users" in stats
        assert "new_users" in stats
        assert "suggestions" in stats

    def test_log_notification(self, notification_system):
        """Test logging notification."""
        notification_system._log_notification("broadcast", "Test message", 5, 1)

        assert len(notification_system.notification_history) == 1
        log_entry = notification_system.notification_history[0]

        assert log_entry["type"] == "broadcast"
        assert log_entry["message"] == "Test message"
        assert log_entry["success_count"] == 5
        assert log_entry["error_count"] == 1

    def test_log_alert(self, notification_system):
        """Test logging alert."""
        result = {"success": True, "sent": 3, "errors": 0}
        notification_system._log_alert("test", "Test alert", "normal", result)

        assert len(notification_system.notification_history) == 1
        log_entry = notification_system.notification_history[0]

        assert log_entry["type"] == "alert"
        assert log_entry["alert_type"] == "test"
        assert log_entry["priority"] == "normal"
        assert log_entry["message"] == "Test alert"
        assert log_entry["result"] == result

    def test_add_subscriber(self, notification_system):
        """Test adding subscriber."""
        notification_system.add_subscriber(123)

        assert 123 in notification_system.subscribed_users
        assert notification_system.get_subscribers_count() == 1

    def test_remove_subscriber(self, notification_system):
        """Test removing subscriber."""
        notification_system.subscribed_users.add(123)
        notification_system.subscribed_users.add(456)

        notification_system.remove_subscriber(123)

        assert 123 not in notification_system.subscribed_users
        assert 456 in notification_system.subscribed_users
        assert notification_system.get_subscribers_count() == 1

    def test_get_subscribers_count(self, notification_system):
        """Test getting subscribers count."""
        assert notification_system.get_subscribers_count() == 0

        notification_system.subscribed_users.add(123)
        notification_system.subscribed_users.add(456)

        assert notification_system.get_subscribers_count() == 2

    def test_get_notification_history(self, notification_system):
        """Test getting notification history."""
        # Add some test notifications
        notification_system._log_notification("test", "Test 1", 1, 0)
        notification_system._log_notification("test", "Test 2", 2, 0)
        notification_system._log_notification("test", "Test 3", 3, 0)

        history = notification_system.get_notification_history(limit=2)

        assert len(history) == 2
        assert history[0]["message"] == "Test 2"
        assert history[1]["message"] == "Test 3"

    def test_update_settings(self, notification_system):
        """Test updating notification settings."""
        new_settings = {"daily_summary": False, "system_alerts": False}

        notification_system.update_settings(new_settings)

        assert notification_system.notification_settings["daily_summary"] is False
        assert notification_system.notification_settings["system_alerts"] is False
        assert (
            notification_system.notification_settings["receipt_analysis"] is True
        )  # Unchanged

    def test_notification_history_limit(self, notification_system):
        """Test notification history limit (max 100 entries)."""
        # Add more than 100 notifications
        for i in range(110):
            notification_system._log_notification("test", f"Test {i}", 1, 0)

        assert len(notification_system.notification_history) == 100
        assert notification_system.notification_history[0]["message"] == "Test 10"
        assert notification_system.notification_history[-1]["message"] == "Test 109"
