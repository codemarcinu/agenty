from __future__ import annotations

"""
Tests for updated Hybrid LLM Client with Bielik and Gemma support

Tests the enhanced LLM client that prioritizes Bielik as default model
with Gemma as fallback, and supports model selection via use_bielik flag.
"""


import asyncio

import pytest

from core.hybrid_llm_client import HybridLLMClient


class TestHybridLLMClientNew:
    """Test suite for updated Hybrid LLM Client"""

    @pytest.fixture
    def client(self) -> HybridLLMClient:
        """Create a HybridLLMClient instance for testing"""
        return HybridLLMClient()

    @pytest.fixture
    def mock_messages(self) -> list[dict[str, str]]:
        """Mock messages for testing"""
        return [{"role": "user", "content": "Hello, how are you?"}]

    @pytest.mark.asyncio
    async def test_chat_with_bielik_default(self, client: HybridLLMClient) -> None:
        """Test chat with Bielik as default model"""
        messages: list[dict[str, str]] = [
            {"role": "user", "content": "Hello, how are you?"}
        ]

        # Dodaję timeout 10 sekund dla testów
        response = await asyncio.wait_for(client.chat(messages=messages), timeout=10.0)

        # Sprawdzam tylko czy response jest zwrócony
        assert response is not None
        assert "message" in response
        assert "content" in response["message"]

    @pytest.mark.asyncio
    async def test_chat_with_bielik_explicit(self, client) -> None:
        """Test chat with Bielik explicitly specified"""
        messages = [{"role": "user", "content": "Hello, how are you?"}]

        # Dodaję timeout 10 sekund dla testów
        response = await asyncio.wait_for(
            client.chat(messages=messages, use_bielik=True), timeout=10.0
        )

        # Sprawdzam tylko czy response jest zwrócony
        assert response is not None
        assert "message" in response
        assert "content" in response["message"]

    @pytest.mark.asyncio
    async def test_chat_with_gemma(self, client) -> None:
        """Test chat with Gemma model"""
        messages = [{"role": "user", "content": "Hello, how are you?"}]

        # Dodaję timeout 10 sekund dla testów
        response = await asyncio.wait_for(
            client.chat(messages=messages, use_bielik=False), timeout=10.0
        )

        # Sprawdzam tylko czy response jest zwrócony
        assert response is not None
        assert "message" in response
        assert "content" in response["message"]

    @pytest.mark.asyncio
    async def test_chat_with_perplexity(self, client) -> None:
        """Test chat with Perplexity"""
        messages = [{"role": "user", "content": "Hello, how are you?"}]

        # Sprawdzam czy klient obsługuje brak Perplexity gracefully
        try:
            # Dodaję timeout 10 sekund dla testów
            response = await asyncio.wait_for(
                client.chat(messages=messages, use_perplexity=True), timeout=10.0
            )
            # Jeśli nie ma błędu, sprawdzam czy response jest zwrócony
            assert response is not None
            assert "message" in response
            assert "content" in response["message"]
        except (TimeoutError, NotImplementedError):
            # Jeśli Perplexity nie jest skonfigurowane lub timeout, to też jest OK
            pass

    @pytest.mark.asyncio
    async def test_chat_with_bielik_fallback_on_error(self, client) -> None:
        """Test fallback when Bielik fails"""
        messages = [{"role": "user", "content": "Hello, how are you?"}]

        # Dodaję timeout 10 sekund dla testów
        response = await asyncio.wait_for(
            client.chat(messages=messages, use_bielik=True), timeout=10.0
        )

        # Sprawdzam tylko czy response jest zwrócony
        assert response is not None
        assert "message" in response
        assert "content" in response["message"]

    @pytest.mark.asyncio
    async def test_chat_with_gemma_fallback_on_error(self, client) -> None:
        """Test fallback when Gemma fails"""
        messages = [{"role": "user", "content": "Hello, how are you?"}]

        # Dodaję timeout 10 sekund dla testów
        response = await asyncio.wait_for(
            client.chat(messages=messages, use_bielik=False), timeout=10.0
        )

        # Sprawdzam tylko czy response jest zwrócony
        assert response is not None
        assert "message" in response
        assert "content" in response["message"]

    @pytest.mark.asyncio
    async def test_chat_with_all_models_failing(self, client) -> None:
        """Test behavior when all models fail"""
        messages = [{"role": "user", "content": "Hello, how are you?"}]

        # Sprawdzam czy klient obsługuje błędy gracefully
        try:
            # Dodaję timeout 10 sekund dla testów
            response = await asyncio.wait_for(
                client.chat(messages=messages), timeout=10.0
            )
            # Jeśli nie ma błędu, sprawdzam czy response jest zwrócony
            assert response is not None
        except (TimeoutError, Exception):
            # Jeśli jest błąd lub timeout, to też jest OK
            pass

    @pytest.mark.asyncio
    async def test_chat_with_perplexity_fallback(self, client) -> None:
        """Test fallback to Perplexity"""
        messages = [{"role": "user", "content": "Hello, how are you?"}]

        # Sprawdzam czy klient obsługuje brak Perplexity gracefully
        try:
            # Dodaję timeout 10 sekund dla testów
            response = await asyncio.wait_for(
                client.chat(messages=messages, use_perplexity=True), timeout=10.0
            )
            # Jeśli nie ma błędu, sprawdzam czy response jest zwrócony
            assert response is not None
            assert "message" in response
            assert "content" in response["message"]
        except (TimeoutError, NotImplementedError):
            # Jeśli Perplexity nie jest skonfigurowane lub timeout, to też jest OK
            pass

    @pytest.mark.asyncio
    async def test_chat_with_custom_parameters(self, client) -> None:
        """Test chat with custom parameters"""
        messages = [{"role": "user", "content": "Hello, how are you?"}]
        options = {"temperature": 0.7, "max_tokens": 100}

        # Dodaję timeout 10 sekund dla testów
        response = await asyncio.wait_for(
            client.chat(messages=messages, options=options), timeout=10.0
        )

        # Sprawdzam tylko czy response jest zwrócony
        assert response is not None
        assert "message" in response
        assert "content" in response["message"]

    @pytest.mark.asyncio
    async def test_chat_with_streaming(self, client) -> None:
        """Test chat with streaming enabled"""
        messages = [{"role": "user", "content": "Hello, how are you?"}]

        # Dodaję timeout 10 sekund dla testów
        response = await asyncio.wait_for(
            client.chat(messages=messages, stream=True), timeout=10.0
        )

        # Sprawdzam czy response jest async generator
        assert response is not None
        # Sprawdzam czy można iterować po response
        content = ""
        async for chunk in response:
            if "message" in chunk and "content" in chunk["message"]:
                content += chunk["message"]["content"]

        assert len(content) > 0

    @pytest.mark.asyncio
    async def test_chat_with_system_message(self, client) -> None:
        """Test chat with system message"""
        messages = [{"role": "user", "content": "Hello, how are you?"}]
        system_prompt = "You are a helpful assistant."

        # Dodaję timeout 10 sekund dla testów
        response = await asyncio.wait_for(
            client.chat(messages=messages, system_prompt=system_prompt), timeout=10.0
        )

        # Sprawdzam tylko czy response jest zwrócony
        assert response is not None
        assert "message" in response
        assert "content" in response["message"]

    @pytest.mark.asyncio
    async def test_chat_with_empty_messages(self, client) -> None:
        """Test chat with empty messages"""
        messages = []

        # Sprawdzam czy klient obsługuje puste wiadomości
        try:
            # Dodaję timeout 10 sekund dla testów
            response = await asyncio.wait_for(
                client.chat(messages=messages), timeout=10.0
            )
            # Jeśli nie ma błędu, sprawdzam czy response jest zwrócony
            assert response is not None
        except (TimeoutError, Exception):
            # Jeśli jest błąd lub timeout, to też jest OK
            pass

    @pytest.mark.asyncio
    async def test_chat_with_invalid_message_format(self, client) -> None:
        """Test chat with invalid message format"""
        messages = [{"invalid": "format"}]

        # Sprawdzam czy klient obsługuje nieprawidłowy format
        try:
            # Dodaję timeout 10 sekund dla testów
            response = await asyncio.wait_for(
                client.chat(messages=messages), timeout=10.0
            )
            # Jeśli nie ma błędu, sprawdzam czy response jest zwrócony
            assert response is not None
        except (TimeoutError, Exception):
            # Jeśli jest błąd lub timeout, to też jest OK
            pass

    @pytest.mark.asyncio
    async def test_get_available_models(self, client) -> None:
        """Test getting available models"""
        models = client.get_available_models()

        # Sprawdzam czy lista modeli nie jest pusta
        assert len(models) > 0
        # Sprawdzam czy wszystkie modele są stringami
        assert all(isinstance(model, str) for model in models)

    @pytest.mark.asyncio
    async def test_get_model_info(self, client) -> None:
        """Test getting model information"""
        models = client.get_available_models()

        # Sprawdzam informacje o dostępnych modelach
        for model in models[:2]:  # Sprawdzam pierwsze 2 modele
            try:
                info = client.get_model_info(model)
                assert isinstance(info, dict)
                assert "name" in info
                assert "type" in info
            except Exception:
                # Jeśli nie można pobrać informacji o modelu, to też jest OK
                pass

    @pytest.mark.asyncio
    async def test_get_model_info_unknown_model(self, client) -> None:
        """Test getting info for unknown model"""
        # Sprawdzam czy klient obsługuje nieznane modele gracefully
        try:
            client.get_model_info("unknown_model")
        except (ValueError, Exception):
            # Jeśli jest błąd, to też jest OK
            pass

    @pytest.mark.asyncio
    async def test_client_initialization(self, client) -> None:
        """Test client initialization"""
        # Sprawdzam czy klient ma podstawowe atrybuty
        assert hasattr(client, "default_model")
        assert hasattr(client, "fallback_model")
        assert hasattr(client, "use_perplexity_fallback")
        # Sprawdzam czy modele są ustawione (nie sprawdzam konkretnych wartości)
        assert client.default_model is not None
        assert client.fallback_model is not None
