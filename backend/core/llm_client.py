import asyncio
from collections.abc import AsyncGenerator, Generator
from datetime import datetime
import inspect
import time
from typing import Any

import ollama
import requests  # type: ignore
import structlog

from settings import settings

logger = structlog.get_logger()

# Configure ollama client to use the correct host from OLLAMA_URL
ollama_url = settings.OLLAMA_URL
logger.info(f"Raw OLLAMA_URL from config: {ollama_url}")

if not ollama_url or not ollama_url.startswith(("http://", "https://")):
    logger.error(f"Invalid OLLAMA_URL: {ollama_url}")
    raise ValueError(
        f"OLLAMA_URL must start with http:// or https://, got: {ollama_url}"
    )

# Create a configured ollama client instance with the correct base URL
ollama_client = ollama.Client(host=ollama_url)
logger.info(f"Configured ollama client with host: {ollama_url}")


# Test Ollama connection on startup
def test_ollama_connection() -> bool:
    """Test if Ollama server is accessible"""
    try:
        response = requests.get(f"{settings.OLLAMA_URL}/api/version", timeout=5)
        if response.status_code == 200:
            logger.info("Ollama server is accessible")
            return True
        logger.warning(f"Ollama server returned status {response.status_code}")
        return False
    except Exception as e:
        logger.warning(f"Ollama server not accessible: {e}")
        return False


# Test connection on module import
OLLAMA_AVAILABLE = test_ollama_connection()


class ModelFallbackManager:
    """Manages model fallback strategy when primary model fails"""

    def __init__(self):
        self.available_models = settings.AVAILABLE_MODELS
        self.fallback_strategy = settings.FALLBACK_STRATEGY
        self.enable_fallback = settings.ENABLE_MODEL_FALLBACK
        self.fallback_timeout = settings.FALLBACK_TIMEOUT
        self.model_health: dict[str, bool] = {}
        self.last_fallback_time: dict[str, datetime] = {}

    async def get_working_model(self, preferred_model: str) -> str:
        """Get a working model, starting with preferred and falling back if needed"""
        if not self.enable_fallback:
            return preferred_model

        # Check if preferred model is healthy
        if await self._is_model_healthy(preferred_model):
            return preferred_model

        # Try fallback models
        for model in self.available_models:
            if model != preferred_model and await self._is_model_healthy(model):
                logger.info(f"Falling back from {preferred_model} to {model}")
                return model

        # If no model is healthy, return preferred model anyway
        logger.warning(f"No healthy models found, using {preferred_model}")
        return preferred_model

    async def _is_model_healthy(self, model: str) -> bool:
        """Check if a specific model is healthy and available"""
        try:
            # Check if model exists and is accessible
            response = requests.get(f"{settings.OLLAMA_URL}/api/tags", timeout=5)
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
        logger.warning(f"Model {model} marked as failed")


class LLMCache:
    """Simple cache for LLM responses to avoid duplicate API calls"""

    def __init__(self, max_size: int = 100, ttl: int = 3600) -> None:
        """Initialize LLM cache with max size and TTL (in seconds)"""
        self.cache: dict[str, dict[str, Any]] = {}
        self.max_size = max_size
        self.ttl = ttl  # Time-to-live in seconds
        self.last_cleanup = datetime.now()

    def get(self, key: str) -> Any | None:
        """Get value from cache if it exists and is not expired"""
        if key in self.cache:
            entry = self.cache[key]
            if (datetime.now() - entry["timestamp"]).total_seconds() < self.ttl:
                return entry["value"]
            # Remove expired entry
            del self.cache[key]
        return None

    def set(self, key: str, value: Any) -> None:
        """Set value in cache with current timestamp"""
        # Cleanup if cache is full
        if len(self.cache) >= self.max_size:
            self._cleanup()

        self.cache[key] = {"value": value, "timestamp": datetime.now()}

    def _cleanup(self) -> None:
        """Remove expired entries and trim cache if needed"""
        now = datetime.now()
        # Remove expired entries
        expired_keys = [
            k
            for k, v in self.cache.items()
            if (now - v["timestamp"]).total_seconds() >= self.ttl
        ]
        for k in expired_keys:
            del self.cache[k]

        # If still too large, remove oldest entries
        if len(self.cache) >= self.max_size:
            sorted_keys = sorted(
                self.cache.keys(), key=lambda k: self.cache[k]["timestamp"]
            )
            for k in sorted_keys[
                : len(self.cache) - self.max_size + 10
            ]:  # Remove batch
                del self.cache[k]


class EnhancedLLMClient:
    """Enhanced LLM client with caching and improved error handling"""

    def __init__(self) -> None:
        """Initialize enhanced LLM client"""
        self.cache = LLMCache(max_size=1000, ttl=3600)  # 1 hour cache
        self.embedding_cache = LLMCache(max_size=5000, ttl=86400)  # 24 hour cache
        self.models_info: dict[str, Any] = {}
        self.last_error: str | None = None
        self.error_count = 0
        self.last_request_time = datetime.now()
        self.connection_retries = 3
        self.retry_delay = 1.0
        self.model_fallback_manager = ModelFallbackManager()

    async def _check_ollama_availability(self) -> bool:
        """Check if Ollama is available with retries"""
        for attempt in range(self.connection_retries):
            try:
                response = requests.get(f"{settings.OLLAMA_URL}/api/version", timeout=5)
                if response.status_code == 200:
                    return True
            except Exception as e:
                logger.debug(
                    f"Ollama availability check attempt {attempt + 1} failed: {e}"
                )
                if attempt < self.connection_retries - 1:
                    await asyncio.sleep(self.retry_delay)
        return False

    async def chat(
        self,
        model: str,
        messages: list[dict[str, str]],
        stream: bool = False,
        options: dict[str, Any] | None = None,
    ) -> dict[str, Any] | AsyncGenerator[dict[str, Any], None]:
        """
        Send chat messages to the LLM with automatic fallback

        Args:
            model: Model name
            messages: List of message dicts with role and content
            stream: Whether to stream the response
            options: Additional options to pass to the model

        Returns:
            Response dict or async generator for streaming
        """
        start_time = time.time()
        options = options or {}

        # Get working model with fallback
        working_model = await self.model_fallback_manager.get_working_model(model)
        if working_model != model:
            logger.info(f"Using fallback model: {working_model} instead of {model}")
            model = working_model

        # Log prompt
        logger.info(
            "ollama_prompt",
            model=model,
            messages=messages,
            options=options,
            stream=stream,
            timestamp=datetime.now().isoformat(),
        )

        # Check if Ollama is available
        if not await self._check_ollama_availability():
            logger.error(f"Ollama server not available for model {model}")
            fallback_response = {
                "message": {
                    "role": "assistant",
                    "content": "I'm sorry, but the language model service is currently unavailable. Please try again later.",
                },
                "response": "I'm sorry, but the language model service is currently unavailable. Please try again later.",
                "error": "Ollama server not available",
            }
            if stream:

                async def fallback_stream() -> AsyncGenerator[dict[str, Any], None]:
                    yield fallback_response

                return fallback_stream()
            return fallback_response

        # For non-streaming, check cache
        if not stream:
            cache_key = f"{model}_{messages!s}_{options!s}"
            cached = self.cache.get(cache_key)
            if cached:
                logger.debug(f"Cache hit for {model}")
                return cached

        try:
            self.last_request_time = datetime.now()

            # Format messages for Ollama
            formatted_messages = []
            for msg in messages:
                if msg["role"] == "system":
                    # Add system message as a special parameter
                    options["system"] = msg["content"]
                else:
                    formatted_messages.append(msg)

            # Clean options to remove unsupported parameters
            cleaned_options = {}
            for key, value in options.items():
                if key in ["num_predict", "top_p", "top_k", "repeat_penalty", "system"]:
                    cleaned_options[key] = value
                # Remove temperature if not supported by this Ollama version
                elif key == "temperature":
                    try:
                        # Test if temperature is supported
                        cleaned_options[key] = value
                    except Exception:
                        logger.warning(
                            "Temperature parameter not supported by Ollama, removing"
                        )
                        continue

            if stream:
                # Return streaming generator
                sync_generator = self._stream_response(
                    model,
                    formatted_messages,
                    cleaned_options,
                    original_messages=messages,
                )
                return self._convert_to_async_generator(sync_generator)
            # For non-streaming, get complete response
            response = await asyncio.to_thread(
                ollama_client.chat,
                model=model,
                messages=[
                    {"role": m["role"], "content": m["content"]}
                    for m in formatted_messages
                ],
                options=cleaned_options,
            )

            # Format response to standard structure
            result = {
                "message": {
                    "role": "assistant",
                    "content": response["message"]["content"],
                },
                "response": response["message"]["content"],
            }

            # Log response
            logger.info(
                "ollama_response",
                model=model,
                messages=messages,
                options=cleaned_options,
                response=result,
                duration=time.time() - start_time,
                timestamp=datetime.now().isoformat(),
            )

            # Cache the result
            if not stream:
                self.cache.set(cache_key, result)

            return result

        except Exception as e:
            self.last_error = str(e)
            self.error_count += 1
            logger.error(f"Error in chat request to {model}: {e!s}")

            # Return fallback response
            fallback_response = {
                "message": {
                    "role": "assistant",
                    "content": "I'm sorry, but I encountered an error processing your request. Please try again.",
                },
                "response": "I'm sorry, but I encountered an error processing your request. Please try again.",
                "error": str(e),
            }
            if stream:

                async def fallback_stream() -> AsyncGenerator[dict[str, Any], None]:
                    yield fallback_response

                return fallback_stream()
            return fallback_response

    async def _convert_to_async_generator(self, sync_gen):
        """Helper method to properly convert sync generator to async."""
        try:
            for item in sync_gen:
                yield item
                await asyncio.sleep(0)  # Allow other coroutines to run
        except Exception as e:
            logger.error(f"Error in async generator conversion: {e}")
            raise

    def _stream_response(
        self,
        model: str,
        messages: list[dict[str, str]],
        options: dict[str, Any],
        original_messages: list[dict[str, str]] | None = None,
    ) -> Generator[dict[str, Any], None, None]:
        """
        Synchronous streaming using Ollama client.
        Returns a proper generator for streaming responses.
        """
        try:
            logger.debug(f"Starting _stream_response for model: {model}")
            logger.debug(f"Messages count: {len(messages)}")
            logger.debug(f"Options: {options}")

            # Używaj stream=True dla streamingu z Ollama
            stream = ollama_client.chat(
                model=model, messages=messages, stream=True, options=options
            )

            logger.debug(f"Ollama stream type: {type(stream)}")
            logger.debug(f"Ollama stream is generator: {inspect.isgenerator(stream)}")

            # Ollama zwraca iterator, nie async generator
            chunk_count = 0
            for chunk in stream:
                chunk_count += 1
                logger.debug(f"Ollama chunk {chunk_count}: {type(chunk)}")
                # Convert ChatResponse to dict if needed
                if hasattr(chunk, "message") and hasattr(chunk.message, "content"):
                    yield {
                        "message": {
                            "role": "assistant",
                            "content": chunk.message.content,
                        }
                    }
                else:
                    yield chunk

            logger.debug(f"Total Ollama chunks: {chunk_count}")

        except Exception as e:
            logger.error(f"Error in Ollama streaming: {e}")
            logger.error(f"Error type: {type(e)}")
            import traceback

            logger.error(f"Traceback: {traceback.format_exc()}")
            raise

    async def embed(
        self, model: str, text: str, options: dict[str, Any] | None = None
    ) -> list[float]:
        """Get embeddings from the model"""
        start_time = time.time()
        options = options or {}

        # Check cache first
        cache_key = f"embed_{model}_{text}_{options!s}"
        cached = self.embedding_cache.get(cache_key)
        if cached:
            logger.debug(f"Embedding cache hit for {model}")
            return cached

        # Check if Ollama is available
        if not await self._check_ollama_availability():
            logger.error(f"Ollama server not available for embedding model {model}")
            # Return zero vector as fallback
            return [0.0] * 384  # Default embedding size

        try:
            self.last_request_time = datetime.now()

            # Get embeddings
            embeddings = await asyncio.to_thread(
                ollama_client.embeddings,
                model=model,
                prompt=text,
                options=options,
            )

            # Cache the result
            self.embedding_cache.set(cache_key, embeddings["embedding"])

            logger.debug(
                f"Embedding request to {model} completed in {time.time() - start_time:.2f}s"
            )
            return embeddings["embedding"]

        except Exception as e:
            self.last_error = str(e)
            self.error_count += 1
            logger.error(f"Error in embedding request to {model}: {e!s}")

            # Return zero vector as fallback
            return [0.0] * 384

    async def get_models(self) -> list[dict[str, Any]]:
        """Get list of available models"""
        try:
            if not await self._check_ollama_availability():
                logger.warning(
                    "Ollama server not available, returning empty model list"
                )
                return []

            models = await asyncio.to_thread(ollama_client.list)
            return models.get("models", [])
        except Exception as e:
            logger.error(f"Error getting models: {e!s}")
            return []

    def generate_stream(
        self,
        model: str,
        messages: list[dict[str, str]],
        options: dict[str, Any] | None = None,
    ) -> Generator[dict[str, Any], None, None]:
        """Generate streaming response from model"""
        yield from self._stream_response(model, messages, options or {})

    def generate_stream_from_prompt(
        self,
        model: str,
        prompt: str,
        system_prompt: str = "",
        options: dict[str, Any] | None = None,
    ) -> Generator[dict[str, Any], None, None]:
        """Generate streaming response from prompt and system prompt"""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        yield from self._stream_response(model, messages, options or {})

    async def generate_stream_from_prompt_async(
        self,
        model: str,
        prompt: str,
        system_prompt: str = "",
        options: dict[str, Any] | None = None,
    ) -> AsyncGenerator[dict[str, Any], None]:
        """
        Async version of generate_stream_from_prompt for FastAPI compatibility.
        Converts synchronous generator to asynchronous generator.
        """
        # Walidacja prompt
        if not prompt or prompt.strip() == "":
            logger.error(
                "Empty or null prompt provided to generate_stream_from_prompt_async"
            )
            yield {"error": "Prompt cannot be empty or null"}
            return

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        sync_generator = self._stream_response(model, messages, options or {})
        await asyncio.sleep(0)  # Ensure this is always an async generator
        for chunk in sync_generator:
            yield chunk
            await asyncio.sleep(0)
        # No return here – ensures this is a true async generator

    def get_health_status(self) -> dict[str, Any]:
        """Get health status of the LLM client"""
        return {
            "ollama_available": OLLAMA_AVAILABLE,
            "last_error": self.last_error,
            "error_count": self.error_count,
            "last_request_time": self.last_request_time.isoformat(),
            "cache_size": len(self.cache.cache),
            "embedding_cache_size": len(self.embedding_cache.cache),
        }


# Global instance
llm_client = EnhancedLLMClient()
LLMClient = EnhancedLLMClient  # Alias for backwards compatibility
