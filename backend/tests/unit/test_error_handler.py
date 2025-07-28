from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from agents.adapters.error_handler import ErrorHandler
from agents.interfaces import AgentResponse, ErrorSeverity


class ConcreteErrorHandler(ErrorHandler):
    """Concrete implementation of ErrorHandler for testing"""

    async def handle_error(
        self, error: Exception, context: dict | None = None
    ) -> AgentResponse:
        return AgentResponse(success=False, error=f"Handled error: {error!s}")


class TestErrorHandler:
    @pytest.fixture
    def handler(self) -> ConcreteErrorHandler:
        return ConcreteErrorHandler("test_agent")

    @pytest.mark.asyncio
    async def test_execute_with_fallback_success(self, handler) -> None:
        mock_func = AsyncMock(return_value=AgentResponse(success=True, text="Success"))
        mock_fallback = AsyncMock(
            return_value=AgentResponse(success=True, text="Fallback")
        )

        result = await handler.execute_with_fallback(
            mock_func, fallback_handler=mock_fallback
        )

        assert result.success
        assert result.text == "Success"
        mock_func.assert_called_once()
        mock_fallback.assert_not_called()

    @pytest.mark.asyncio
    async def test_execute_with_fallback_error(self, handler) -> None:
        mock_func = AsyncMock(side_effect=Exception("Test error"))
        mock_fallback = AsyncMock(
            return_value=AgentResponse(success=True, text="Fallback")
        )

        result = await handler.execute_with_fallback(
            mock_func, fallback_handler=mock_fallback
        )

        assert result.success
        assert result.text == "Fallback"
        mock_func.assert_called_once()
        mock_fallback.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_with_fallback_fallback_success(self, handler) -> None:
        mock_func = AsyncMock(side_effect=Exception("Test error"))
        mock_fallback = AsyncMock(side_effect=Exception("Fallback error"))

        result = await handler.execute_with_fallback(
            mock_func, fallback_handler=mock_fallback
        )

        assert result is None  # Gdy fallback też się nie powiedzie, zwraca None

    def test_should_alert_below_threshold(self, handler) -> None:
        handler.error_count = 2
        handler.alert_threshold = 5

        assert not handler.should_alert("test error", ErrorSeverity.LOW)

    def test_should_alert_above_threshold(self, handler) -> None:
        handler.error_count = 10
        handler.alert_threshold = 5

        assert handler.should_alert("test error", ErrorSeverity.HIGH)

    def test_should_alert_throttling(self, handler) -> None:
        # Ustaw konfigurację alertów
        handler.alert_config = {
            "enabled": True,
            "min_severity": ErrorSeverity.MEDIUM,
            "throttle_period": 300,  # 5 minut
        }

        # Resetuj stan alertów
        handler.last_alerts = {}

        # Test 1: Pierwszy alert powinien przejść
        assert handler.should_alert("test error", ErrorSeverity.HIGH)

        # Test 2: Drugi alert w tym samym czasie powinien być zablokowany
        assert not handler.should_alert("test error", ErrorSeverity.HIGH)

        # Test 3: Po upływie czasu throttle powinien pozwolić na alert
        with patch("backend.agents.adapters.error_handler.datetime") as mock_datetime:
            # Symuluj czas po upływie throttle period
            mock_datetime.now.return_value = datetime.now() + timedelta(minutes=6)
            assert handler.should_alert("test error", ErrorSeverity.HIGH)

    @pytest.mark.asyncio
    async def test_send_alert(self, handler) -> None:
        handler.alert_service = MagicMock()
        handler.alert_service.send_alert.return_value = True

        result = await handler._send_alert("Test alert", {}, ErrorSeverity.HIGH)

        assert result is None  # _send_alert zwraca None

    @pytest.mark.asyncio
    async def test_handle_error(self, handler) -> None:
        """Test the handle_error method"""
        # Use the actual ErrorHandler instead of ConcreteErrorHandler
        actual_handler = ErrorHandler("test_agent")
        test_error = ValueError("Test error message")
        context = {"test_key": "test_value"}

        result = await actual_handler.handle_error(test_error, context)

        assert result.success is False
        assert result.error == "Test error message"
        assert result.severity == "low"  # ValueError should be LOW severity
        assert result.metadata["error_type"] == "ValueError"
        assert result.metadata["context"] == context
        assert result.metadata["agent_name"] == "test_agent"
        assert result.metadata["handled_by"] == "ErrorHandler"

    @pytest.mark.asyncio
    async def test_handle_error_critical_severity(self, handler) -> None:
        """Test handle_error with critical severity error"""
        # Use the actual ErrorHandler instead of ConcreteErrorHandler
        actual_handler = ErrorHandler("test_agent")
        test_error = MemoryError("Out of memory")
        context = {"memory_usage": "95%"}

        result = await actual_handler.handle_error(test_error, context)

        assert result.success is False
        assert result.error == "Out of memory"
        assert result.severity == "critical"  # MemoryError should be CRITICAL severity
        assert result.metadata["error_type"] == "MemoryError"
