from unittest.mock import AsyncMock, patch

import pytest

from core.model_fallback_manager import (
    ModelFallbackManager,
    ModelUnavailableError,
)


@pytest.mark.asyncio
async def test_model_fallback_and_recovery():
    mgr = ModelFallbackManager()

    # Mock health checks for specific models
    with patch.object(mgr, "_is_model_healthy", new_callable=AsyncMock) as mock_health:
        # Mock health check to return True for specific models
        def mock_health_check(model):
            if (
                model in ("SpeakLeash/bielik-4.5b-v3.0-instruct:Q8_0", "SpeakLeash/bielik-11b-v2.3-instruct:Q5_K_M", "gemma3:12b")
            ):
                return model not in mgr.failed_models
            return False

        mock_health.side_effect = mock_health_check

        # Początkowo wszystkie modele dostępne
        model = await mgr.get_working_model()
        assert model == "SpeakLeash/bielik-4.5b-v3.0-instruct:Q8_0"

        # Symuluj awarię głównego modelu
        mgr.failed_models.add("SpeakLeash/bielik-4.5b-v3.0-instruct:Q8_0")
        model = await mgr.get_working_model()
        assert model == "SpeakLeash/bielik-11b-v2.3-instruct:Q5_K_M"

        # Symuluj awarię wszystkich modeli
        mgr.failed_models.update(
            ["SpeakLeash/bielik-11b-v2.3-instruct:Q5_K_M", "gemma3:12b"]
        )
        with pytest.raises(ModelUnavailableError):
            await mgr.get_working_model()

        # Recovery: przywróć model
        mgr.failed_models.remove("SpeakLeash/bielik-11b-v2.3-instruct:Q5_K_M")
        model = await mgr.get_working_model()
        assert model == "SpeakLeash/bielik-11b-v2.3-instruct:Q5_K_M"


@pytest.mark.asyncio
async def test_model_health_check():
    """Test model health check with mocked requests"""
    mgr = ModelFallbackManager()

    with patch("requests.get") as mock_get:
        # Mock successful response with available models
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            "models": [
                {"name": "SpeakLeash/bielik-4.5b-v3.0-instruct:Q8_0"},
                {"name": "SpeakLeash/bielik-11b-v2.3-instruct:Q5_K_M"},
                {"name": "gemma3:12b"},
            ]
        }

        # Test health check for available model
        is_healthy = await mgr._is_model_healthy(
            "SpeakLeash/bielik-4.5b-v3.0-instruct:Q8_0"
        )
        assert is_healthy is True

        # Test health check for unavailable model
        is_healthy = await mgr._is_model_healthy("nonexistent:model")
        assert is_healthy is False


@pytest.mark.asyncio
async def test_model_fallback_disabled():
    """Test fallback when disabled"""
    mgr = ModelFallbackManager()
    mgr.enable_fallback = False

    # Should return preferred model without health check
    model = await mgr.get_working_model("SpeakLeash/bielik-4.5b-v3.0-instruct:Q8_0")
    assert model == "SpeakLeash/bielik-4.5b-v3.0-instruct:Q8_0"
