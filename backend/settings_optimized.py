from __future__ import annotations

import json
import os
import secrets

from pydantic_settings import BaseSettings

# Set User-Agent environment variable early to prevent warnings
os.environ.setdefault(
    "USER_AGENT", "FoodSave-AI/1.0.0 (https://github.com/foodsave-ai)"
)


class OptimizedSettings(BaseSettings):
    """
    Zoptymalizowane ustawienia dla RTX 3060 + 32GB RAM
    Dostosowane do konfiguracji: AMD Ryzen 5 5500 + NVIDIA RTX 3060
    """

    APP_NAME: str = "FoodSave AI - Optimized"
    APP_VERSION: str = "2.0.0"

    # Environment configuration
    ENVIRONMENT: str = "production"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    TELEMETRY_ENABLED: bool = True

    # Backend configuration
    BACKEND_HOST: str = os.getenv("BACKEND_HOST", "0.0.0.0")
    BACKEND_PORT: int = int(os.getenv("BACKEND_PORT", "8000"))

    # User Agent for HTTP requests
    USER_AGENT: str = "FoodSave-AI/2.0.0 (RTX3060-Optimized)"

    # JWT Configuration
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ALGORITHM: str = "HS256"

    # Security Configuration (Enhanced for production)
    SECURITY_ENCRYPTION_KEY: str = secrets.token_urlsafe(32)
    SECURITY_KEY_SALT: str = secrets.token_urlsafe(16)
    SECURITY_MAX_REQUESTS_PER_MINUTE: int = 120  # Increased for RTX 3060
    SECURITY_MAX_REQUESTS_PER_HOUR: int = 2000   # Increased for RTX 3060
    SECURITY_MAX_LOGIN_ATTEMPTS: int = 5
    SECURITY_LOCKOUT_DURATION: int = 15
    SECURITY_MIN_PASSWORD_LENGTH: int = 12
    SECURITY_REQUIRE_UPPERCASE: bool = True
    SECURITY_REQUIRE_LOWERCASE: bool = True
    SECURITY_REQUIRE_DIGITS: bool = True
    SECURITY_REQUIRE_SPECIAL: bool = True
    SECURITY_PASSWORD_HISTORY: int = 5
    SECURITY_SESSION_TIMEOUT: int = 30
    SECURITY_MAX_SESSIONS: int = 5  # Increased for better UX
    SECURITY_MAX_INPUT_LENGTH: int = 15000  # Increased for complex queries
    SECURITY_MAX_FILE_SIZE_MB: int = 15     # Increased for larger files
    SECURITY_AUDIT_LOG_ENABLED: bool = True
    SECURITY_AUDIT_LOG_PATH: str = os.getenv(
        "SECURITY_AUDIT_LOG_PATH", "./logs/security_audit.log"
    )

    # Enhanced Backup Configuration
    BACKUP_LOCAL_DIR: str = os.getenv("BACKUP_LOCAL_DIR", "./backups")
    CLOUD_BACKUP_ENABLED: bool = False
    CLOUD_PROVIDER: str = "aws"
    CLOUD_BUCKET: str | None = None
    CLOUD_REGION: str = "us-east-1"
    BACKUP_ENCRYPTION_ENABLED: bool = True
    BACKUP_ENCRYPTION_KEY: str | None = None
    BACKUP_DAILY_RETENTION: int = 7
    BACKUP_WEEKLY_RETENTION: int = 4
    BACKUP_MONTHLY_RETENTION: int = 12
    BACKUP_YEARLY_RETENTION: int = 5
    AUTO_BACKUP_ENABLED: bool = True
    BACKUP_SCHEDULE_HOUR: int = 2
    BACKUP_SCHEDULE_MINUTE: int = 0
    BACKUP_VERIFY_ENABLED: bool = True
    BACKUP_CHECKSUM_VERIFICATION: bool = True
    BACKUP_COMPRESSION_LEVEL: int = 6
    BACKUP_COMPRESSION_TYPE: str = "gzip"

    # AWS Configuration (for cloud backups)
    AWS_ACCESS_KEY_ID: str | None = None
    AWS_SECRET_ACCESS_KEY: str | None = None
    AWS_DEFAULT_REGION: str = "us-east-1"
    AWS_S3_BUCKET: str | None = None
    AWS_S3_ENDPOINT_URL: str | None = None  # For custom S3-compatible storage

    # Redis Configuration (Optimized for 32GB RAM)
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB: int = int(os.getenv("REDIS_DB", "0"))
    REDIS_PASSWORD: str = ""
    REDIS_USE_CACHE: bool = os.getenv("REDIS_USE_CACHE", "true").lower() == "true"
    REDIS_MAX_MEMORY: str = "2gb"  # Increased for 32GB RAM
    REDIS_MAX_MEMORY_POLICY: str = "allkeys-lru"

    # Konfiguracja dla klienta Ollama (Zoptymalizowana dla RTX 3060)
    OLLAMA_URL: str = os.getenv("OLLAMA_URL", "http://localhost:11434")
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

    # Modele językowe - Zoptymalizowane dla RTX 3060 (12GB VRAM) - POPRAWIONE
    OLLAMA_MODEL: str = "SpeakLeash/bielik-11b-v2.3-instruct:Q5_K_M"  # Primary model
    DEFAULT_CODE_MODEL: str = "codellama:7b"                            # Code generation (zainstalowany)
    DEFAULT_CHAT_MODEL: str = "SpeakLeash/bielik-11b-v2.3-instruct:Q5_K_M"  # Chat
    DEFAULT_MODEL: str = "SpeakLeash/bielik-11b-v2.3-instruct:Q5_K_M"       # Default
    DEFAULT_EMBEDDING_MODEL: str = "nomic-embed-text"                        # Embeddings
    
    # Vision Model dla OCR (RTX 3060 optimized) - POPRAWIONE
    VISION_MODEL: str = "llava:7b"  # Zainstalowany model
    
    # Fallback Models (Lighter models for fallback) - POPRAWIONE
    FALLBACK_MODEL: str = "llama3.2:3b"  # Zainstalowany model
    FALLBACK_VISION_MODEL: str = "llava:7b"  # Zainstalowany model

    # Lista dostępnych modeli (Zoptymalizowana dla RTX 3060) - POPRAWIONE
    AVAILABLE_MODELS: str = os.getenv(
        "AVAILABLE_MODELS", 
        '["SpeakLeash/bielik-11b-v2.3-instruct:Q5_K_M", "llava:7b", "llama3.2:3b", "codellama:7b", "aya:8b", "nomic-embed-text"]'
    )

    @property
    def available_models(self) -> list[str]:
        try:
            return json.loads(self.AVAILABLE_MODELS)
        except Exception:
            return []

    # Strategia fallback modeli (Enhanced for RTX 3060)
    FALLBACK_STRATEGY: str = "progressive"  # progressive, round_robin, quality_first
    ENABLE_MODEL_FALLBACK: bool = True
    FALLBACK_TIMEOUT: int = 60  # sekundy przed przełączeniem na fallback
    VALIDATE_MODELS_ON_STARTUP: bool = True  # Walidacja modeli przy starcie

    # GPU Configuration dla RTX 3060
    GPU_DEVICE_ID: int = 0
    GPU_MEMORY_LIMIT: str = "10GB"  # 12GB VRAM - 2GB overhead
    USE_GPU_OCR: bool = True
    GPU_ACCELERATION_ENABLED: bool = True

    # Konfiguracja MMLW (opcjonalny, lepszy dla języka polskiego)
    USE_MMLW_EMBEDDINGS: bool = True  # Automatycznie włączone
    MMLW_MODEL_NAME: str = "sdadas/mmlw-retrieval-roberta-base"

    # Konfiguracja bazy danych
    DATABASE_URL: str = "sqlite+aiosqlite:///data/foodsave.db"

    # CORS Configuration
    CORS_ORIGINS: str = (
        "http://localhost:3000,http://127.0.0.1:3000,http://localhost:8000,http://localhost:8085"
    )

    # API keys for external services
    LLM_API_KEY: str = ""
    OPENWEATHER_API_KEY: str = ""
    PERPLEXITY_API_KEY: str = ""

    # Konfiguracja Tesseract OCR (Enhanced for RTX 3060)
    TESSDATA_PREFIX: str = "/usr/share/tesseract-ocr/5/"
    OCR_TIMEOUT: int = 600  # Increased for complex processing
    ANALYSIS_TIMEOUT: int = 480  # Increased for complex analysis
    MAX_FILE_SIZE: int = 15728640  # 15MB increased limit

    # Telegram Bot Configuration
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_WEBHOOK_URL: str = ""
    TELEGRAM_WEBHOOK_SECRET: str = secrets.token_urlsafe(32)

    # Telegram Bot Settings (Enhanced)
    TELEGRAM_BOT_USERNAME: str = "foodsave_ai_bot"
    TELEGRAM_BOT_NAME: str = "FoodSave AI Assistant (RTX 3060)"
    TELEGRAM_MAX_MESSAGE_LENGTH: int = 4096
    TELEGRAM_RATE_LIMIT_PER_MINUTE: int = 60  # Increased for RTX 3060

    # System Agentowy - Nowa Architektura (Enhanced for RTX 3060)
    USE_PLANNER_EXECUTOR: bool = True  # Włącz nową architekturę planisty-egzekutora
    ENABLE_CONVERSATION_SUMMARY: bool = True  # Włącz pamięć podsumowującą
    CONVERSATION_SUMMARY_THRESHOLD: int = 5  # Minimalna liczba wiadomości do podsumowania

    # Konfiguracja Celery (Enhanced for RTX 3060)
    CELERY_BROKER_URL: str = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
    CELERY_RESULT_BACKEND: str = os.getenv(
        "CELERY_RESULT_BACKEND", "redis://localhost:6379/0"
    )
    CELERY_TASK_TIME_LIMIT: int = int(os.getenv("CELERY_TASK_TIME_LIMIT", "3600"))  # Increased
    CELERY_TASK_SOFT_TIME_LIMIT: int = int(
        os.getenv("CELERY_TASK_SOFT_TIME_LIMIT", "3000")  # Increased
    )
    CELERY_CONCURRENCY: int = 4  # Increased for RTX 3060
    CELERY_MAX_TASKS_PER_CHILD: int = 1000
    CELERY_PREFETCH_MULTIPLIER: int = 4

    # Konfiguracja pamięci konwersacji (Enhanced for 32GB RAM)
    MEMORY_MAX_CONTEXTS: int = 2000  # Increased for 32GB RAM
    MEMORY_CLEANUP_THRESHOLD_RATIO: float = 0.8
    MEMORY_ENABLE_PERSISTENCE: bool = True
    MEMORY_ENABLE_SEMANTIC_CACHE: bool = True

    # Konfiguracja planisty (Enhanced for RTX 3060)
    PLANNER_TEMPERATURE: float = 0.1  # Niska temperatura dla spójności planów
    PLANNER_MAX_TOKENS: int = 4000  # Maksymalna liczba tokenów dla planisty

    # Konfiguracja syntezatora (Enhanced for RTX 3060)
    SYNTHESIZER_TEMPERATURE: float = 0.3  # Średnia temperatura dla kreatywności
    SYNTHESIZER_MAX_TOKENS: int = 2000  # Maksymalna liczba tokenów dla syntezatora

    # Konfiguracja egzekutora (Enhanced for RTX 3060)
    EXECUTOR_MAX_STEPS: int = 15  # Increased for complex tasks
    EXECUTOR_STEP_TIMEOUT: int = 120  # Increased timeout for complex operations

    # Perplexica Settings (Enhanced)
    PERPLEXICA_BASE_URL: str = os.getenv(
        "PERPLEXICA_BASE_URL", "http://perplexica-app:3000/api"
    )
    PERPLEXICA_ENABLED: bool = os.getenv("PERPLEXICA_ENABLED", "true").lower() == "true"
    PERPLEXICA_TIMEOUT: int = int(os.getenv("PERPLEXICA_TIMEOUT", "60"))  # Increased
    PERPLEXICA_MAX_RETRIES: int = int(os.getenv("PERPLEXICA_MAX_RETRIES", "5"))  # Increased
    PERPLEXICA_DEFAULT_PROVIDERS: str = os.getenv(
        "PERPLEXICA_DEFAULT_PROVIDERS", "wikipedia,duckduckgo,searxng"
    )
    PERPLEXICA_SEARXNG_URL: str = os.getenv(
        "PERPLEXICA_SEARXNG_URL", "http://perplexica-searxng:8080"
    )
    PERPLEXICA_HEALTH_CHECK_ENABLED: bool = (
        os.getenv("PERPLEXICA_HEALTH_CHECK_ENABLED", "true").lower() == "true"
    )

    # Performance Monitoring (Enhanced for RTX 3060)
    ENABLE_PERFORMANCE_MONITORING: bool = True
    PERFORMANCE_METRICS_INTERVAL: int = 30  # seconds
    GPU_MONITORING_ENABLED: bool = True
    MEMORY_MONITORING_ENABLED: bool = True
    DISK_MONITORING_ENABLED: bool = True

    # Anti-Hallucination System (Enhanced)
    ANTI_HALLUCINATION_ENABLED: bool = True
    ANTI_HALLUCINATION_THRESHOLD: float = 0.3
    ANTI_HALLUCINATION_CONFIDENCE_THRESHOLD: float = 0.7
    ANTI_HALLUCINATION_TIMEOUT: int = 30

    # Cache Configuration (Enhanced for 32GB RAM)
    CACHE_ENABLED: bool = True
    CACHE_TTL: int = 3600  # 1 hour
    CACHE_MAX_SIZE: int = 1000  # Increased for 32GB RAM
    CACHE_CLEANUP_INTERVAL: int = 300  # 5 minutes

    # Logging Configuration (Enhanced)
    LOG_FORMAT: str = "json"
    LOG_LEVEL_CONSOLE: str = "INFO"
    LOG_LEVEL_FILE: str = "DEBUG"
    LOG_FILE_PATH: str = "./logs/foodsave.log"
    LOG_MAX_SIZE: int = 100  # MB
    LOG_BACKUP_COUNT: int = 5

    # Health Check Configuration
    HEALTH_CHECK_ENABLED: bool = True
    HEALTH_CHECK_INTERVAL: int = 30  # seconds
    HEALTH_CHECK_TIMEOUT: int = 10  # seconds

    # Rate Limiting (Enhanced for RTX 3060)
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = 120  # Increased
    RATE_LIMIT_REQUESTS_PER_HOUR: int = 2000   # Increased
    RATE_LIMIT_BURST_SIZE: int = 20  # Increased

    # Model Loading Configuration (RTX 3060 optimized)
    MODEL_LOADING_TIMEOUT: int = 300  # 5 minutes
    MODEL_UNLOADING_ENABLED: bool = True
    MODEL_PRELOAD_ENABLED: bool = True
    MODEL_PRELOAD_LIST: str = os.getenv(
        "MODEL_PRELOAD_LIST",
        '["SpeakLeash/bielik-11b-v2.3-instruct:Q5_K_M", "llava:7b"]'
    )

    # Ta linia mówi Pydantic, aby wczytał zmienne z pliku backend.env w głównym katalogu
    model_config = {"env_file": "backend.env", "env_file_encoding": "utf-8", "extra": "ignore"}


# Tworzymy jedną, globalną instancję zoptymalizowanych ustawień
optimized_settings = OptimizedSettings()

# Export both for compatibility
settings = optimized_settings 