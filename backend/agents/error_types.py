from collections.abc import AsyncGenerator
from typing import Any

from pydantic import BaseModel

from agents.interfaces import ErrorSeverity


class AgentResponseEnhanced(BaseModel):
    """Enhanced agent response with additional context and error handling"""

    success: bool
    data: dict[str, Any] | None = None
    text: str | None = None
    text_stream: AsyncGenerator[str, None] | None = None
    message: str | None = None
    error: str | None = None
    error_details: dict[str, Any] | None = None
    error_severity: ErrorSeverity | None = None
    processed_with_fallback: bool = False
    processing_time: float = 0.0
    metadata: dict[str, Any] = {}

    model_config = {"arbitrary_types_allowed": True}


class AlertConfig(BaseModel):
    """Configuration for alert notifications"""

    enabled: bool = True
    email_alerts: bool = False
    email_recipients: list[str] = []
    slack_alerts: bool = False
    slack_webhook: str | None = None
    min_severity: ErrorSeverity = ErrorSeverity.HIGH
    throttle_period: int = 3600  # seconds between similar alerts


class AgentError(Exception):
    """Base class for agent errors"""

    def __init__(
        self, message: str, severity: ErrorSeverity = ErrorSeverity.MEDIUM
    ) -> None:
        self.message = message
        self.severity = severity
        super().__init__(message)


class OrchestratorError(AgentError):
    """Error specific to orchestrator operations"""

    def __init__(
        self, message: str, severity: ErrorSeverity = ErrorSeverity.HIGH
    ) -> None:
        super().__init__(message, severity)


class AgentProcessingError(AgentError):
    """Error during agent processing"""

    def __init__(
        self,
        message: str,
        agent_type: str,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
    ) -> None:
        self.agent_type = agent_type
        super().__init__(message, severity)


class AgentInitializationError(AgentError):
    """Error during agent initialization"""

    def __init__(
        self,
        message: str,
        agent_type: str,
        severity: ErrorSeverity = ErrorSeverity.HIGH,
    ) -> None:
        self.agent_type = agent_type
        super().__init__(message, severity)
