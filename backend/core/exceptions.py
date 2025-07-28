"""
Centralny moduł wyjątków dla MyAssistant/FoodSave AI.

Zgodnie z regułami TRY003 i TRY002, definiujemy specyficzne wyjątki
zamiast używania generycznych Exception.
"""

from typing import Any


class FoodSaveAIError(Exception):
    """Bazowy wyjątek dla wszystkich błędów aplikacji."""

    def __init__(self, message: str, details: Any | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details


# Alias dla kompatybilności wstecznej
FoodSaveError = FoodSaveAIError


# === AUTHENTICATION & AUTHORIZATION ===
class AuthenticationError(FoodSaveAIError):
    """Błąd uwierzytelniania użytkownika."""


class AuthorizationError(FoodSaveAIError):
    """Błąd autoryzacji - brak uprawnień."""


class InvalidTokenError(AuthenticationError):
    """Nieprawidłowy lub wygasły token."""


# === DATA VALIDATION ===
class ValidationError(FoodSaveAIError):
    """Błąd walidacji danych wejściowych."""


class InvalidDataError(ValidationError):
    """Nieprawidłowe dane wejściowe."""


class MissingRequiredFieldError(ValidationError):
    """Brak wymaganego pola."""


# === DATABASE ===
class DatabaseError(FoodSaveAIError):
    """Błąd bazy danych."""


class ConnectionError(DatabaseError):
    """Błąd połączenia z bazą danych."""


class QueryError(DatabaseError):
    """Błąd zapytania do bazy danych."""


class RecordNotFoundError(DatabaseError):
    """Rekord nie został znaleziony."""


# === FILE OPERATIONS ===
class FileOperationError(FoodSaveAIError):
    """Błąd operacji na plikach."""


class FileNotFoundError(FileOperationError):
    """Plik nie został znaleziony."""


class FilePermissionError(FileOperationError):
    """Brak uprawnień do pliku."""


class FileSizeError(FileOperationError):
    """Plik jest za duży."""


# === OCR & RECEIPT PROCESSING ===
class ProcessingError(FoodSaveAIError):
    """Ogólny błąd przetwarzania."""


class OCRError(FoodSaveAIError):
    """Błąd OCR (Optical Character Recognition)."""


class ReceiptProcessingError(FoodSaveAIError):
    """Błąd przetwarzania paragonu."""


class ReceiptValidationError(ReceiptProcessingError):
    """Błąd walidacji paragonu."""


class ReceiptFormatError(ReceiptProcessingError):
    """Nieprawidłowy format paragonu."""


# === AI & LLM ===
class AIError(FoodSaveAIError):
    """Błąd AI/LLM."""


class LLMConnectionError(AIError):
    """Błąd połączenia z LLM."""


class LLMTimeoutError(AIError):
    """Timeout połączenia z LLM."""


class LLMResponseError(AIError):
    """Błąd odpowiedzi z LLM."""


class AgentError(AIError):
    """Błąd agenta AI."""


# === EXTERNAL SERVICES ===
class ExternalServiceError(FoodSaveAIError):
    """Błąd zewnętrznego serwisu."""


class ExternalAPIError(ExternalServiceError):
    """Błąd zewnętrznego API."""


class APIConnectionError(ExternalServiceError):
    """Błąd połączenia z API."""


class APIResponseError(ExternalServiceError):
    """Błąd odpowiedzi z API."""


class RateLimitError(ExternalServiceError):
    """Przekroczono limit zapytań."""


# === CONFIGURATION ===
class ConfigurationError(FoodSaveAIError):
    """Błąd konfiguracji."""


class MissingConfigError(ConfigurationError):
    """Brak wymaganej konfiguracji."""


class InvalidConfigError(ConfigurationError):
    """Nieprawidłowa konfiguracja."""


# === CACHE & STORAGE ===
class CacheError(FoodSaveAIError):
    """Błąd cache."""


class StorageError(FoodSaveAIError):
    """Błąd magazynu danych."""


class VectorStoreError(StorageError):
    """Błąd magazynu wektorów."""


# === TASKS & WORKERS ===
class TaskError(FoodSaveAIError):
    """Błąd zadania."""


class WorkerError(TaskError):
    """Błąd workera."""


class TaskTimeoutError(TaskError):
    """Timeout zadania."""


# === MONITORING & LOGGING ===
class MonitoringError(FoodSaveAIError):
    """Błąd monitoringu."""


class HealthCheckError(MonitoringError):
    """Błąd sprawdzania stanu systemu."""


class LoggingError(FoodSaveAIError):
    """Błąd logowania."""


# === UTILITY EXCEPTIONS ===
class TimeoutError(FoodSaveAIError):
    """Ogólny błąd timeout."""


class RetryableError(FoodSaveAIError):
    """Błąd, który można ponowić."""


class NonRetryableError(FoodSaveAIError):
    """Błąd, którego nie można ponowić."""


# === CONSTANTS FOR MAGIC VALUES ===
# Zgodnie z regułą PLR2004
HTTP_OK = 200
HTTP_CREATED = 201
HTTP_BAD_REQUEST = 400
HTTP_UNAUTHORIZED = 401
HTTP_FORBIDDEN = 403
HTTP_NOT_FOUND = 404
HTTP_INTERNAL_SERVER_ERROR = 500
HTTP_SERVICE_UNAVAILABLE = 503

# Timeout constants
DEFAULT_TIMEOUT = 30
LLM_TIMEOUT = 60
OCR_TIMEOUT = 120
FILE_UPLOAD_TIMEOUT = 300

# File size limits
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5MB

# Cache TTL
DEFAULT_CACHE_TTL = 3600  # 1 hour
SHORT_CACHE_TTL = 300  # 5 minutes
LONG_CACHE_TTL = 86400  # 24 hours


# === UTILITY FUNCTIONS ===
def handle_exception_with_context(
    exception: Exception, context: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Handle exception with additional context information.

    Args:
        exception: The exception to handle
        context: Additional context information

    Returns:
        Dictionary with error information
    """
    error_info = {
        "error_type": type(exception).__name__,
        "error_message": str(exception),
        "context": context or {},
    }

    details = getattr(exception, "details", None)
    if details is not None:
        error_info["details"] = details

    return error_info


def create_error_response(
    error: Exception,
    status_code: int = HTTP_INTERNAL_SERVER_ERROR,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Create a standardized error response.

    Args:
        error: The exception that occurred
        status_code: HTTP status code
        context: Additional context information

    Returns:
        Standardized error response dictionary
    """
    error_info = handle_exception_with_context(error, context)

    return {
        "status_code": status_code,
        "error": error_info,
        "success": False,
        "timestamp": __import__("datetime").datetime.now().isoformat(),
    }
