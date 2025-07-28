"""
Structured exceptions for receipt processing system
"""

from datetime import datetime
from typing import Any
import uuid


class ReceiptProcessingError(Exception):
    """Base exception for receipt processing"""

    def __init__(
        self,
        message: str,
        error_code: str,
        details: dict[str, Any] | None = None,
        correlation_id: str | None = None,
    ):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.correlation_id = correlation_id or str(uuid.uuid4())
        self.timestamp = datetime.now().isoformat()
        super().__init__(message)

    def to_dict(self) -> dict[str, Any]:
        """Convert exception to dictionary for API responses"""
        return {
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details,
            "correlation_id": self.correlation_id,
            "timestamp": self.timestamp,
        }


class OCRProcessingError(ReceiptProcessingError):
    """OCR specific errors"""

    def __init__(self, message: str, details: dict[str, Any] | None = None, **kwargs):
        super().__init__(
            message=message,
            error_code="OCR_PROCESSING_ERROR",
            details=details,
            **kwargs,
        )


class ReceiptAnalysisError(ReceiptProcessingError):
    """Receipt analysis specific errors"""

    def __init__(self, message: str, details: dict[str, Any] | None = None, **kwargs):
        super().__init__(
            message=message,
            error_code="RECEIPT_ANALYSIS_ERROR",
            details=details,
            **kwargs,
        )


class DatabaseSaveError(ReceiptProcessingError):
    """Database save errors"""

    def __init__(self, message: str, details: dict[str, Any] | None = None, **kwargs):
        super().__init__(
            message=message, error_code="DATABASE_SAVE_ERROR", details=details, **kwargs
        )


class FileValidationError(ReceiptProcessingError):
    """File validation errors"""

    def __init__(self, message: str, details: dict[str, Any] | None = None, **kwargs):
        super().__init__(
            message=message,
            error_code="FILE_VALIDATION_ERROR",
            details=details,
            **kwargs,
        )


class FileSecurityError(ReceiptProcessingError):
    """File security validation errors"""

    def __init__(self, message: str, details: dict[str, Any] | None = None, **kwargs):
        super().__init__(
            message=message, error_code="FILE_SECURITY_ERROR", details=details, **kwargs
        )


class ProcessingTimeoutError(ReceiptProcessingError):
    """Processing timeout errors"""

    def __init__(
        self,
        message: str,
        timeout_seconds: int,
        details: dict[str, Any] | None = None,
        **kwargs,
    ):
        details = details or {}
        details["timeout_seconds"] = timeout_seconds
        super().__init__(
            message=message,
            error_code="PROCESSING_TIMEOUT_ERROR",
            details=details,
            **kwargs,
        )


class RateLimitError(ReceiptProcessingError):
    """Rate limiting errors"""

    def __init__(self, message: str, details: dict[str, Any] | None = None, **kwargs):
        super().__init__(
            message=message, error_code="RATE_LIMIT_ERROR", details=details, **kwargs
        )
