from collections.abc import Awaitable, Callable
from datetime import datetime
import logging
import traceback
from typing import Any

from agents.error_types import ErrorSeverity
from agents.interfaces import AgentResponse, IErrorHandler

logger = logging.getLogger(__name__)


class ErrorHandler(IErrorHandler):
    """Handler for error processing and recovery with alerting capabilities"""

    def __init__(self, name: str, alert_config: dict[str, Any] | None = None) -> None:
        self.name = name
        self.alert_config = alert_config or {
            "enabled": True,
            "min_severity": ErrorSeverity.HIGH,
            "throttle_period": 3600,
        }
        self.last_alerts: dict[str, datetime] = {}

    async def handle_error(
        self, error: Exception, context: dict[str, Any]
    ) -> AgentResponse:
        """Handle errors in agent processing"""
        error_message = str(error)
        error_type = type(error).__name__

        # Log the error
        logger.error(
            f"Error in {self.name}: {error_message}",
            extra={
                "error_type": error_type,
                "context": context,
                "agent_name": self.name,
            },
            exc_info=True,
        )

        # Determine severity based on error type
        severity = ErrorSeverity.MEDIUM
        if isinstance(error, ValueError | TypeError):
            severity = ErrorSeverity.LOW
        elif isinstance(error, ConnectionError | TimeoutError):
            severity = ErrorSeverity.HIGH
        elif isinstance(error, MemoryError | OSError):
            severity = ErrorSeverity.CRITICAL

        # Check if we should send an alert
        if self._should_alert(error_message, severity):
            await self._send_alert(
                f"Error in {self.name}",
                {
                    "error": error_message,
                    "error_type": error_type,
                    "context": context,
                    "timestamp": datetime.now().isoformat(),
                },
                severity,
            )

        # Return error response
        return AgentResponse(
            success=False,
            error=error_message,
            severity=severity.value,
            metadata={
                "error_type": error_type,
                "context": context,
                "agent_name": self.name,
                "handled_by": "ErrorHandler",
            },
        )

    async def execute_with_fallback(
        self,
        func: Callable[..., Awaitable[Any]],
        *args,
        fallback_handler: Callable[..., Any] | None = None,
        error_severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        **kwargs,
    ) -> None:
        """
        Execute a function with automatic fallback and error handling
        Returns the result of the operation or fallback.
        Logs additional debug information internally.
        """
        try:
            result = await func(*args, **kwargs)
            return result

        except Exception as e:
            error_info = {
                "error": str(e),
                "traceback": traceback.format_exc(),
                "timestamp": datetime.now().isoformat(),
            }
            logger.exception(f"Error in {self.name}.{func.__name__}")

            if self._should_alert(str(e), error_severity):
                await self._send_alert(
                    f"Error in {self.name}.{func.__name__}", error_info, error_severity
                )

            if fallback_handler:
                try:
                    logger.info(f"Attempting fallback for {func.__name__}")
                    result = await fallback_handler(*args, error=e, **kwargs)
                    return result
                except Exception as fallback_error:
                    logger.exception("Fallback also failed")
                    error_info["fallback_error"] = str(fallback_error)

            return None

    def _should_alert(self, error_message: str, severity: ErrorSeverity) -> bool:
        """Determine if an alert should be sent based on severity and throttling"""
        if not self.alert_config["enabled"]:
            return False

        severity_levels = {
            ErrorSeverity.LOW: 1,
            ErrorSeverity.MEDIUM: 2,
            ErrorSeverity.HIGH: 3,
            ErrorSeverity.CRITICAL: 4,
        }

        if (
            severity_levels[severity]
            < severity_levels[self.alert_config["min_severity"]]
        ):
            return False

        error_key = f"{self.name}:{error_message[:50]}"
        now = datetime.now()

        if error_key in self.last_alerts:
            time_since_last = (now - self.last_alerts[error_key]).total_seconds()
            if time_since_last < self.alert_config["throttle_period"]:
                return False

        return True

    def should_alert(self, error_message: str, severity: ErrorSeverity) -> bool:
        """Public interface for checking if an alert should be sent"""
        should_send = self._should_alert(error_message, severity)

        # Aktualizuj last_alerts jeśli alert powinien być wysłany
        if should_send:
            error_key = f"{self.name}:{error_message[:50]}"
            self.last_alerts[error_key] = datetime.now()

        return should_send

    async def _send_alert(
        self, subject: str, error_info: dict[str, Any], severity: ErrorSeverity
    ) -> None:
        """Send alert notification via configured channels"""
        if not self.alert_config["enabled"]:
            return

        error_key = f"{self.name}:{subject[:50]}"
        self.last_alerts[error_key] = datetime.now()

        logger.warning(f"AGENT ALERT: {subject} ({severity})")
        # In production would send email/Slack alerts here
