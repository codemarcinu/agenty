from datetime import datetime
import logging

import requests

from settings import settings

logger = logging.getLogger(__name__)

OLLAMA_URL = settings.OLLAMA_URL


class ModelUnavailableError(Exception):
    """Raised when no models are available for fallback"""


class ModelFallbackManager:
    """Manages model fallback strategy when primary model fails"""

    def __init__(self):
        self.available_models = settings.AVAILABLE_MODELS
        self.fallback_strategy = settings.FALLBACK_STRATEGY
        self.enable_fallback = settings.ENABLE_MODEL_FALLBACK
        self.fallback_timeout = settings.FALLBACK_TIMEOUT
        self.model_health: dict[str, bool] = {}
        self.last_fallback_time: dict[str, datetime] = {}
        self.failed_models: set = set()

    async def get_working_model(self, preferred_model: str | None = None) -> str:
        """Get a working model, starting with preferred and falling back if needed"""
        if not self.enable_fallback:
            return preferred_model or self.available_models[0]

        # Check if preferred model is healthy
        if preferred_model and await self._is_model_healthy(preferred_model):
            return preferred_model

        # Try fallback models
        for model in self.available_models:
            if model != preferred_model and await self._is_model_healthy(model):
                logger.info(f"Falling back from {preferred_model} to {model}")
                return model

        # If no model is healthy, raise exception
        logger.warning("No healthy models found")
        raise ModelUnavailableError("No models are currently available")

    async def _is_model_healthy(self, model: str) -> bool:
        """Check if a specific model is healthy and available"""
        if model in self.failed_models:
            return False

        try:
            # Check if model exists and is accessible
            response = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
            if response.status_code == 200:
                models_data = response.json()
                available_models = [
                    m.get("name", "") for m in models_data.get("models", [])
                ]
                return model in available_models
        except Exception as e:
            logger.debug(f"Health check failed for model {model}: {e}")

        return False

    def mark_model_failed(self, model: str):
        """Mark a model as failed for fallback purposes"""
        self.model_health[model] = False
        self.last_fallback_time[model] = datetime.now()
        self.failed_models.add(model)
        logger.warning(f"Model {model} marked as failed")

    def mark_model_available(self, model: str):
        """Mark a model as available again"""
        self.model_health[model] = True
        self.failed_models.discard(model)
        logger.info(f"Model {model} marked as available")
