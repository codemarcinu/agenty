import json
import os
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
import httpx
import structlog

from settings import settings

router = APIRouter()

LLM_SETTINGS_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "..",
    "data",
    "config",
    "llm_settings.json",
)

logger = structlog.get_logger(__name__)


@router.get("/", response_model=dict[str, Any])
async def get_settings() -> dict[str, Any]:
    """Get general application settings for frontend."""
    try:
        # Return default settings structure expected by frontend
        settings_data = {
            "user": {
                "name": "",
                "email": "",
                "language": "pl",
                "currency": "PLN",
                "timezone": "Europe/Warsaw",
            },
            "notifications": {
                "email": True,
                "push": False,
                "sms": False,
                "expiringAlerts": True,
                "spendingAlerts": True,
            },
            "system": {
                "debug": settings.DEBUG,
                "environment": settings.ENVIRONMENT,
                "version": settings.APP_VERSION,
            }
        }
        return settings_data
    except Exception as e:
        logger.error(f"Error getting settings: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Błąd podczas pobierania ustawień: {e}"
        )


@router.put("/", response_model=dict[str, Any])
async def update_settings(settings_data: dict[str, Any]) -> dict[str, Any]:
    """Update general application settings."""
    try:
        # For now, just return the updated settings
        # In a full implementation, this would save to database or config file
        logger.info(f"Settings update requested: {settings_data}")
        return settings_data
    except Exception as e:
        logger.error(f"Error updating settings: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Błąd podczas aktualizacji ustawień: {e}"
        )


@router.get("/llm-models", response_model=list[dict[str, str]])
async def get_available_models() -> list[dict[str, str]]:
    """Get list of available LLM models from Ollama."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{settings.OLLAMA_URL}/api/tags")
            if response.status_code == 200:
                data = response.json()
                models = []
                for model in data.get("models", []):
                    models.append(
                        {
                            "name": model["name"],
                            "size": str(model.get("size", "Unknown")),
                            "modified_at": model.get("modified_at", ""),
                        }
                    )
                return models
            logger.error(
                "Failed to fetch models from Ollama",
                status_code=response.status_code,
                detail=response.text,
            )
            raise HTTPException(
                status_code=500, detail="Nie udało się pobrać listy modeli z Ollama"
            )
    except Exception as e:
        logger.error(f"Error fetching models: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Błąd podczas pobierania modeli: {e}"
        )


@router.get("/llm-model/selected")
async def get_selected_model() -> str:
    """Get currently selected LLM model."""
    try:
        if Path(LLM_SETTINGS_PATH).exists():
            with open(LLM_SETTINGS_PATH, encoding="utf-8") as f:
                data = json.load(f)
                return data.get("selected_model", "")
        return ""
    except Exception as e:
        logger.error(f"Error reading selected model: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Błąd odczytu wybranego modelu: {e}"
        )


@router.post("/llm-model/selected")
async def set_selected_model(model_name: str) -> dict[str, str]:
    """Set the selected LLM model with validation."""
    try:
        # Validate that the model exists in Ollama
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{settings.OLLAMA_URL}/api/tags")
            if response.status_code != 200:
                logger.error(
                    "Failed to connect to Ollama for model validation",
                    status_code=response.status_code,
                    detail=response.text,
                )
                raise HTTPException(
                    status_code=500, detail="Nie udało się połączyć z Ollama"
                )

            data = response.json()
            available_models = [model["name"] for model in data.get("models", [])]

            if model_name not in available_models:
                logger.warning(
                    f"Model '{model_name}' not found in Ollama. Available: {available_models}"
                )
                raise HTTPException(
                    status_code=400,
                    detail=f"Model '{model_name}' nie jest dostępny w Ollama. Dostępne modele: {', '.join(available_models)}",
                )

        # Ensure config directory exists
        config_dir = os.path.dirname(LLM_SETTINGS_PATH)
        os.makedirs(config_dir, exist_ok=True)

        # Save the selected model
        settings_data = {"selected_model": model_name}
        with open(LLM_SETTINGS_PATH, "w", encoding="utf-8") as f:
            json.dump(settings_data, f, indent=2, ensure_ascii=False)

        logger.info(f"Model '{model_name}' set as default")
        return {
            "message": f"Model '{model_name}' został ustawiony jako domyślny",
            "selected_model": model_name,
        }

    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Error setting selected model: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Błąd ustawiania wybranego modelu: {e}"
        )
