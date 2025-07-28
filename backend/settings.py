"""
Settings module - exports settings from backend
"""

import os
import sys
from pydantic_settings import BaseSettings

# Add src to path if not already there
project_root = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(project_root, "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)


class Settings(BaseSettings):
    """
    Basic settings configuration for FoodSave AI
    """
    
    # App configuration
    APP_NAME: str = "FoodSave AI"
    APP_VERSION: str = "2.0.0"
    
    # Environment configuration
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    
    # Backend configuration
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000
    
    # Database configuration
    DATABASE_URL: str = "sqlite+aiosqlite:///data/foodsave.db"
    
    # Redis configuration
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: str = ""
    
    # Ollama configuration
    OLLAMA_URL: str = "http://localhost:11434"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    
    # Model configuration
    OLLAMA_MODEL: str = "SpeakLeash/bielik-11b-v2.3-instruct:Q5_K_M"
    DEFAULT_MODEL: str = "SpeakLeash/bielik-11b-v2.3-instruct:Q5_K_M"
    FALLBACK_MODEL: str = "llama3.2:3b"
    VISION_MODEL: str = "llava:7b"
    AVAILABLE_MODELS: list = ["SpeakLeash/bielik-11b-v2.3-instruct:Q5_K_M", "llama3.2:3b", "llava:7b"]
    FALLBACK_STRATEGY: str = "sequential"
    ENABLE_MODEL_FALLBACK: bool = True
    FALLBACK_TIMEOUT: int = 30
    
    # CORS configuration
    CORS_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000,http://localhost:8000,http://localhost:8085"
    
    # Security configuration
    SECRET_KEY: str = "your-secret-key-here"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Telegram configuration
    TELEGRAM_BOT_TOKEN: str = "7689926174:AAHIidXCkrH4swWEz0EW0md8A196HvFggP4"
    
    # API Keys configuration
    LLM_API_KEY: str = ""
    OPENWEATHER_API_KEY: str = "dummy-api-key"
    PERPLEXITY_API_KEY: str = ""
    
    # Telemetry configuration
    TELEMETRY_ENABLED: bool = True
    
    # MMLW Embeddings configuration
    USE_MMLW_EMBEDDINGS: bool = True
    MMLW_MODEL_NAME: str = "sdadas/mmlw-retrieval-roberta-base"
    
    # GPU Configuration
    GPU_DEVICE_ID: int = 0
    GPU_MEMORY_LIMIT: str = "10GB"
    USE_GPU_OCR: bool = True
    GPU_ACCELERATION_ENABLED: bool = True
    GPU_MONITORING_ENABLED: bool = True
    
    # OCR Configuration
    OCR_TIMEOUT: int = 600
    ANALYSIS_TIMEOUT: int = 480
    TESSDATA_PREFIX: str = "/usr/share/tesseract-ocr/5/"
    
    # File upload configuration
    MAX_FILE_SIZE: int = 15728640  # 15MB
    
    # Model configuration for environment file
    model_config = {"env_file": "backend.env", "env_file_encoding": "utf-8", "extra": "ignore"}
    
    # User agent for web requests
    USER_AGENT: str = "FoodSave-AI/1.0"
    
    # SerpAPI configuration
    SERPAPI_API_KEY: str = ""
    SERPAPI_ENGINE: str = "google"
    SERPAPI_LOCATION: str = "Poland"
    SERPAPI_LANGUAGE: str = "pl"
    SERPAPI_ENABLED: bool = False


# Create settings instance
settings = Settings()
