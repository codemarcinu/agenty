import asyncio
from collections.abc import AsyncGenerator
from datetime import datetime, timedelta
from enum import Enum
import json
import logging
import os
from pathlib import Path
import re
import time
from typing import Any

from pydantic import BaseModel

from core.language_detector import language_detector
from core.llm_client import LLMCache, llm_client
from core.model_selector import ModelTask, model_selector
from core.response_length_config import ResponseLengthConfig

logger = logging.getLogger(__name__)


class ModelComplexity(str, Enum):
    """Complexity levels for model selection"""

    SIMPLE = "simple"  # For simple queries, greetings
    STANDARD = "standard"  # For most conversational queries
    COMPLEX = "complex"  # For reasoning, coding, creative tasks
    CRITICAL = "critical"  # For safety-critical operations


class ModelConfig(BaseModel):
    """Configuration for a specific LLM model"""

    model_config = {}

    name: str
    complexity_levels: list[ModelComplexity]
    max_tokens: int
    cost_per_token: float = 0.0  # Cost per 1000 tokens
    priority: int = 1  # Lower number means higher priority
    concurrency_limit: int = 10  # Max concurrent requests
    is_enabled: bool = True
    supports_streaming: bool = True
    supports_embedding: bool = False
    description: str | None = None
    default_options: dict[str, Any] | None = None
    polish_optimized: bool = False
    concise_mode: bool = False


class ModelUsageStats(BaseModel):
    """Usage statistics for a model"""

    total_requests: int = 0
    total_tokens: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    average_latency: float = 0.0
    last_error: str | None = None
    last_used: datetime = datetime.now()


class ModelSelectionMetrics(BaseModel):
    """Metrics used for model selection decisions"""

    query_length: int
    complexity_score: float
    keyword_score: float
    priority_features: list[str]
    selected_model: str
    complexity_level: ModelComplexity
    selection_reason: str
    language: str | None = None


class HybridLLMClient:
    """
    Enhanced LLM client with hybrid model selection, resource management,
    and automatic fallback.
    """

    fallback_model = "aya:8b"
    gemma_model = "llava:7b"  # Model multimodalny dla zadań z obrazami
    use_perplexity_fallback = True
    perplexity_client = None  # do mockowania w testach

    def __init__(self) -> None:
        """Initialize hybrid LLM client"""
        self.base_client = llm_client
        self.model_configs: dict[str, ModelConfig] = self._init_model_configs()
        self.model_stats: dict[str, ModelUsageStats] = {
            name: ModelUsageStats() for name in self.model_configs
        }

        # Create semaphores for each model
        self.semaphores: dict[str, asyncio.Semaphore] = {
            name: asyncio.Semaphore(config.concurrency_limit)
            for name, config in self.model_configs.items()
        }

        # Create caches for each model
        self.caches: dict[str, LLMCache] = {
            name: LLMCache(max_size=1000, ttl=3600)  # 1 hour TTL
            for name in self.model_configs
        }

        # For metrics collection
        self.selection_metrics: list[ModelSelectionMetrics] = []
        self.last_cleanup = datetime.now()

        # Inicjalizacja model_selector
        self.model_selector = model_selector
        logger.info("HybridLLMClient initialized with ModelSelector")

    @property
    def default_model(self) -> str:
        """Get the default model from config file or fallback to hardcoded value"""
        try:
            # Path to the LLM settings file
            llm_settings_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                "..",
                "data",
                "config",
                "llm_settings.json",
            )

            if Path(llm_settings_path).exists():
                with open(llm_settings_path, encoding="utf-8") as f:
                    data = json.load(f)
                    selected_model = data.get("selected_model", "")
                    if selected_model and selected_model in self.model_configs:
                        logger.info(
                            f"Using selected model from config: {selected_model}"
                        )
                        return selected_model

            # Fallback to hardcoded default
            fallback_default = "aya:8b"
            logger.info(
                f"No valid selected model in config, using fallback: {fallback_default}"
            )
            return fallback_default

        except Exception as e:
            logger.warning(f"Error reading selected model from config: {e}")
            fallback_default = "aya:8b"
            logger.info(f"Using fallback default model: {fallback_default}")
            return fallback_default

    def _init_model_configs(self) -> dict[str, ModelConfig]:
        """Initialize model configs with their capabilities"""
        return {
            "aya:8b": ModelConfig(
                name="aya:8b",
                complexity_levels=[
                    ModelComplexity.SIMPLE,
                    ModelComplexity.STANDARD,
                    ModelComplexity.COMPLEX,
                    ModelComplexity.CRITICAL,
                ],
                max_tokens=32768,
                cost_per_token=0.15,
                priority=1,  # Najwyższy priorytet - główny model
                concurrency_limit=6,  # Zwiększony limit dla głównego modelu
                supports_embedding=True,
                default_options={
                    "temperature": 0.1,  # Bardzo niska temperatura dla precyzji
                    "top_p": 0.85,
                    "top_k": 30,
                    "repeat_penalty": 1.15,
                    "num_predict": 200,
                },
                polish_optimized=True,  # Model zoptymalizowany dla polskiego
                concise_mode=False,  # Dłuższe odpowiedzi dla złożonych zadań
            ),
            "llama3.2:3b": ModelConfig(
                name="llama3.2:3b",
                complexity_levels=[
                    ModelComplexity.SIMPLE,
                    ModelComplexity.STANDARD,
                ],
                max_tokens=8192,
                cost_per_token=0.05,
                priority=2,
                concurrency_limit=8,
                supports_embedding=False,
                default_options={
                    "temperature": 0.2,
                    "top_p": 0.9,
                    "top_k": 40,
                    "repeat_penalty": 1.1,
                    "num_predict": 100,
                },
                polish_optimized=False,
                concise_mode=True,
            ),
            "llava:7b": ModelConfig(
                name="llava:7b",
                complexity_levels=[
                    ModelComplexity.SIMPLE,
                    ModelComplexity.STANDARD,
                    ModelComplexity.COMPLEX,
                ],
                max_tokens=16384,
                cost_per_token=0.12,
                priority=3,
                concurrency_limit=4,
                supports_embedding=False,
                default_options={
                    "temperature": 0.1,
                    "top_p": 0.9,
                    "top_k": 40,
                    "repeat_penalty": 1.1,
                    "num_predict": 512,
                },
                polish_optimized=False,
                concise_mode=False,
            ),
        }

    async def _get_complexity_level(
        self, messages: list[dict[str, str]], system_prompt: str | None = None
    ) -> tuple[ModelComplexity, float, list[str]]:
        """
        Determine complexity of the query for appropriate model selection.
        Returns: (complexity_level, complexity_score, priority_features)
        """
        query = next(
            (msg.get("content", "") for msg in messages if msg.get("role") == "user"),
            "",
        )

        # Wykrywanie języka dla wyboru modelu
        detected_language = "en"
        if query:
            detected_language, _ = language_detector.detect_language(query)
            logger.info(
                f"Detected language: {detected_language} for query: {query[:50]}..."
            )

        # Initialize score and features
        complexity_score = 0.0
        priority_features = []

        # 1. Length-based complexity
        query_length = len(query)
        if query_length < 50:
            complexity_score += 0.2
        elif query_length < 200:
            complexity_score += 0.5
            priority_features.append("medium_length")
        else:
            complexity_score += 0.8
            priority_features.append("long_query")

        # 2. Keyword-based complexity
        complex_keywords = [
            "wyjaśnij",
            "porównaj",
            "przeanalizuj",
            "uzasadnij",
            "zaprojektuj",
            "utwórz",
            "zaimplementuj",
            "kod",
            "program",
            "algorytm",
            "dlaczego",
            "jakie są przyczyny",
            "co by się stało gdyby",
        ]

        critical_keywords = [
            "pilne",
            "krytyczne",
            "ważne",
            "pomoc medyczna",
            "zagrożenie",
            "alert",
            "przeprowadź analizę",
            "złożony problem",
            "optymalizacja",
            "zrównoleglenie",
        ]

        keyword_score = 0.0

        for keyword in complex_keywords:
            if keyword.lower() in query.lower():
                keyword_score += 0.2
                priority_features.append(f"complex_term:{keyword}")

        for keyword in critical_keywords:
            if keyword.lower() in query.lower():
                keyword_score += 0.4
                priority_features.append(f"critical_term:{keyword}")

        # Cap keyword score
        keyword_score = min(1.0, keyword_score)
        complexity_score += keyword_score

        # 3. Pattern-based complexity
        if re.search(r"[\[\]\(\)\{\}]", query):  # Code-like characters
            complexity_score += 0.3
            priority_features.append("code_syntax")

        if query.count("\n") > 3:  # Multi-line text often indicates complex request
            complexity_score += 0.3
            priority_features.append("multi_line")

        if re.search(
            r"\d+[\.,]\d+", query
        ):  # Numbers with decimals often in technical content
            complexity_score += 0.2
            priority_features.append("technical_numbers")

        # 4. System prompt complexity (if provided)
        if system_prompt and len(system_prompt) > 200:
            complexity_score += 0.3
            priority_features.append("complex_system_prompt")

        # 5. History complexity (not implemented yet - would need full conversation history)

        # Normalize final score (0.0 - 1.0)
        normalized_score = min(1.0, complexity_score / 3.0)

        # Map score to complexity level
        if normalized_score < 0.3:
            complexity_level = ModelComplexity.SIMPLE
        elif normalized_score < 0.6:
            complexity_level = ModelComplexity.STANDARD
        elif normalized_score < 0.85:
            complexity_level = ModelComplexity.COMPLEX
        else:
            complexity_level = ModelComplexity.CRITICAL

        # Add language as a priority feature
        priority_features.append(f"language_{detected_language}")

        return complexity_level, normalized_score, priority_features

    def _select_model(
        self,
        complexity_level: ModelComplexity,
        complexity_score: float,
        priority_features: list[str],
    ) -> tuple[str, str]:
        """
        Select appropriate model based on complexity level, language, and available resources
        Returns: (model_name, selection_reason)
        """
        # Get query from priority features
        query = ""
        for feature in priority_features:
            if feature.startswith("query_"):
                query = feature[6:]
                break

        # Map complexity to ModelTask
        task = ModelTask.TEXT_ONLY
        if complexity_level == ModelComplexity.COMPLEX:
            task = ModelTask.CREATIVE
        elif complexity_level == ModelComplexity.CRITICAL:
            task = ModelTask.STRUCTURED_OUTPUT

        # Check for available models
        available_models = [
            name
            for name, config in self.model_configs.items()
            if config.is_enabled and self.semaphores[name]._value > 0
        ]

        if not available_models:
            # Jeśli wszystkie modele zajęte, używamy domyślnego
            available_models = [
                name for name, config in self.model_configs.items() if config.is_enabled
            ]
            if not available_models:
                logger.warning("No models available, falling back to default")
                return self.default_model, "No models available"

        # Użyj nowego selektora modeli
        best_model = model_selector.select_model(
            query=query,
            task=task,
            complexity=complexity_score,
            contains_images=False,  # Na razie obsługa obrazów nie jest zaimplementowana
            available_models=available_models,
        )

        reason = f"Selected {best_model} using ModelSelector (task: {task}, complexity: {complexity_score:.2f})"
        logger.info(reason)
        return best_model, reason

    async def chat(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        stream: bool = False,
        system_prompt: str | None = None,
        options: dict[str, Any] | None = None,
        force_complexity: ModelComplexity | None = None,
        use_bielik: bool | None = None,
        use_perplexity: bool | None = None,
        task: ModelTask | None = None,  # Nowy parametr
        contains_images: bool = False,  # Nowy parametr
        response_length: (
            ResponseLengthConfig | None
        ) = None,  # Nowy parametr dla kontroli długości
        timeout: int | None = None,  # Nowy parametr timeout
        **kwargs,
    ) -> dict[str, Any] | AsyncGenerator[dict[str, Any], None]:
        """
        Enhanced chat method with optimized parameters for receipt analysis
        """
        start_time = time.time()

        # Optymalizacja dla analizy paragonów - krótszy timeout
        if timeout is None:
            # Dla analizy paragonów używamy krótszego timeout
            if any(
                "receipt" in str(msg).lower() or "paragon" in str(msg).lower()
                for msg in messages
            ):
                timeout = 30  # 30 sekund dla analizy paragonów
            else:
                timeout = 60  # Standardowy timeout

        # Optymalizacja opcji dla szybszej odpowiedzi
        if options is None:
            options = {}

        # Dla analizy paragonów używamy bardziej agresywnych parametrów
        if any(
            "receipt" in str(msg).lower() or "paragon" in str(msg).lower()
            for msg in messages
        ):
            options.update(
                {
                    "temperature": 0.1,  # Niższa temperatura = bardziej deterministyczne odpowiedzi
                    "top_p": 0.9,  # Ograniczenie diversity
                    "top_k": 40,  # Ograniczenie wyboru tokenów
                    "repeat_penalty": 1.1,  # Zmniejszenie powtórzeń
                    "num_predict": 512,  # Ograniczenie długości odpowiedzi
                }
            )
        else:
            # Dla general chat używamy bardzo konserwatywnych parametrów przeciwko hallucinacjom
            options.update(
                {
                    "temperature": 0.1,  # Bardzo niska temperatura = maksymalna deterministyczność
                    "top_p": 0.8,  # Bardziej ograniczone diversity
                    "top_k": 20,  # Bardziej ograniczony wybór tokenów
                    "repeat_penalty": 1.2,  # Większe zmniejszenie powtórzeń
                    "num_predict": 800,  # Ograniczenie długości odpowiedzi
                }
            )

        try:
            # Reszta oryginalnej implementacji
            if model is None:
                model = self.default_model

            # Sprawdź czy model jest dostępny
            if model not in self.model_configs:
                logger.warning(f"Model {model} not found, using fallback")
                model = self.fallback_model

            # Użyj semaphore dla kontroli współbieżności
            async with self.semaphores[model]:
                # Sprawdź cache
                cache_key = self._generate_cache_key(messages, model, options)
                cached_response = self.caches[model].get(cache_key)
                if cached_response:
                    logger.info(f"Cache hit for model {model}")
                    return cached_response

                # Wywołaj LLM z timeout
                try:
                    response = await asyncio.wait_for(
                        self.base_client.chat(
                            messages=messages,
                            model=model,
                            stream=stream,
                            options=options,
                            **kwargs,
                        ),
                        timeout=timeout,
                    )

                    # Zapisz w cache
                    if not stream:
                        self.caches[model].set(cache_key, response)

                    # Aktualizuj statystyki
                    self._update_model_stats(model, time.time() - start_time, True)

                    return response

                except TimeoutError:
                    logger.error(f"Timeout after {timeout}s for model {model}")
                    self._update_model_stats(model, timeout, False, "timeout")

                    # Jeśli to nie jest już fallback model, spróbuj z fallback
                    if (
                        model != self.fallback_model
                        and self.fallback_model in self.model_configs
                    ):
                        logger.info(
                            f"Retrying with fallback model: {self.fallback_model}"
                        )
                        try:
                            fallback_response = await asyncio.wait_for(
                                self.base_client.chat(
                                    messages=messages,
                                    model=self.fallback_model,
                                    stream=stream,
                                    options=options,
                                    **kwargs,
                                ),
                                timeout=timeout,
                            )
                            logger.info("Fallback model response successful")
                            return fallback_response
                        except Exception as fallback_error:
                            logger.error(
                                f"Fallback model also failed: {fallback_error}"
                            )

                    raise
                except Exception as e:
                    logger.error(f"Error in chat for model {model}: {e}")
                    self._update_model_stats(
                        model, time.time() - start_time, False, str(e)
                    )

                    # Jeśli to nie jest już fallback model, spróbuj z fallback
                    if (
                        model != self.fallback_model
                        and self.fallback_model in self.model_configs
                    ):
                        logger.info(
                            f"Retrying with fallback model: {self.fallback_model}"
                        )
                        try:
                            fallback_response = await asyncio.wait_for(
                                self.base_client.chat(
                                    messages=messages,
                                    model=self.fallback_model,
                                    stream=stream,
                                    options=options,
                                    **kwargs,
                                ),
                                timeout=timeout,
                            )
                            logger.info("Fallback model response successful")
                            return fallback_response
                        except Exception as fallback_error:
                            logger.error(
                                f"Fallback model also failed: {fallback_error}"
                            )

                    raise

        except Exception as e:
            logger.error(f"Chat error: {e}")
            raise

    async def _wrap_streaming_response(
        self,
        model: str,
        messages: list[dict[str, str]],
        options: dict[str, Any] | None = None,
        response_length: ResponseLengthConfig | None = None,
    ) -> AsyncGenerator[dict[str, Any], None]:
        """Wrap streaming response with stats tracking and length control"""
        start_time = time.time()
        chunks_count = 0
        total_length = 0
        accumulated_text = ""

        try:
            # Get streaming response from base client
            stream = await self.base_client.chat(
                model=model, messages=messages, stream=True, options=options
            )

            # Process each chunk
            async for chunk in stream:
                chunks_count += 1
                if (
                    isinstance(chunk, dict)
                    and "message" in chunk
                    and "content" in chunk["message"]
                ):
                    chunk_content = chunk["message"]["content"]
                    total_length += len(chunk_content)
                    accumulated_text += chunk_content

                    # Apply length control if configured
                    if response_length and response_length.should_truncate_response(
                        len(accumulated_text)
                    ):
                        # Stop streaming if we've reached the limit
                        break

                yield chunk

            # Update success stats
            self.model_stats[model].successful_requests += 1
            # Estimate tokens (rough approximation)
            tokens = total_length // 4
            self.model_stats[model].total_tokens += tokens

            # Update latency
            latency = time.time() - start_time
            model_stats = self.model_stats[model]
            model_stats.average_latency = (
                (
                    model_stats.average_latency * (model_stats.successful_requests - 1)
                    + latency
                )
                / model_stats.successful_requests
                if model_stats.successful_requests > 0
                else latency
            )

        except Exception as error_msg:
            logger.error(f"Error in streaming response: {error_msg!s}")

            if model and model in self.model_stats:
                self.model_stats[model].failed_requests += 1
                self.model_stats[model].last_error = str(error_msg)

            # Yield an error response that matches the expected format
            error_message = f"Error in streaming response: {error_msg!s}"
            yield {
                "message": {"content": error_message},
                "text": error_message,
                "error_type": type(error_msg).__name__,
                "timestamp": datetime.now().isoformat(),
            }

    async def embed(self, text: str, model: str | None = None) -> list[float]:
        """Get embeddings with automatic model selection"""
        if not model:
            # Use Bielik as default embedding model
            embedding_models = [
                name
                for name, config in self.model_configs.items()
                if config.is_enabled and config.supports_embedding
            ]

            if embedding_models:
                # Use Bielik-11B for embeddings
                model = "SpeakLeash/bielik-11b-v2.3-instruct:Q5_K_M"
            else:
                # Default to Bielik-11B
                model = "SpeakLeash/bielik-11b-v2.3-instruct:Q5_K_M"

        # Ensure the model exists
        if model not in self.model_configs:
            logger.warning(f"Unknown embedding model: {model}, falling back to Bielik")
            model = "SpeakLeash/bielik-11b-v2.3-instruct:Q5_K_M"

        # Update usage stats
        self.model_stats[model].total_requests += 1
        self.model_stats[model].last_used = datetime.now()

        try:
            # Use semaphore for resource control
            async with self.semaphores[model]:
                embeddings = await self.base_client.embed(model=model, text=text)

                # Update success stats
                self.model_stats[model].successful_requests += 1

                return embeddings
        except Exception as e:
            logger.error(f"Error generating embeddings: {e!s}")
            self.model_stats[model].failed_requests += 1
            self.model_stats[model].last_error = str(e)
            return []

    def get_models_status(self) -> dict[str, dict[str, Any]]:
        """Get status of all models"""
        status = {}

        for name, config in self.model_configs.items():
            stats = self.model_stats[name]
            semaphore = self.semaphores[name]

            status[name] = {
                "enabled": config.is_enabled,
                "available_slots": semaphore._value,
                "max_concurrency": config.concurrency_limit,
                "total_requests": stats.total_requests,
                "success_rate": (
                    stats.successful_requests / stats.total_requests
                    if stats.total_requests > 0
                    else 1.0
                ),
                "average_latency": stats.average_latency,
                "last_used": stats.last_used.isoformat(),
                "complexity_levels": [
                    level.value for level in config.complexity_levels
                ],
            }

        return status

    def maintenance(self) -> dict[str, Any]:
        """Perform maintenance tasks and return stats"""
        # Cleanup old metrics
        now = datetime.now()
        if now - self.last_cleanup > timedelta(hours=1):
            # Keep only the last 100 metrics
            if len(self.selection_metrics) > 100:
                self.selection_metrics = self.selection_metrics[-100:]
            self.last_cleanup = now

        # Collect stats
        return {
            "models": self.get_models_status(),
            "total_requests": sum(
                stats.total_requests for stats in self.model_stats.values()
            ),
            "total_tokens": sum(
                stats.total_tokens for stats in self.model_stats.values()
            ),
            "metrics_collected": len(self.selection_metrics),
        }

    async def with_retry_fallback(
        self,
        messages: list[dict[str, str]],
        primary_model: str | None = None,
        fallback_model: str | None = None,
        max_retries: int = 2,
        stream: bool = False,
        response_length: ResponseLengthConfig | None = None,  # Nowy parametr
    ) -> Any:
        """Try with primary model, falling back to simpler model if necessary"""

        # Get the query for model selection
        query = next(
            (msg.get("content", "") for msg in messages if msg.get("role") == "user"),
            "",
        )

        # Determine primary model if none provided
        if not primary_model:
            # Use model selector to pick the best model
            task = ModelTask.TEXT_ONLY
            if any("```" in msg.get("content", "") for msg in messages):
                task = ModelTask.CODE_GENERATION

            available_models = [
                name for name, config in self.model_configs.items() if config.is_enabled
            ]

            primary_model = model_selector.select_model(
                query=query,
                task=task,
                complexity=0.5,
                contains_images=False,
                available_models=available_models,
            )

            logger.info(f"Selected primary model {primary_model} using ModelSelector")

        # Try primary model
        for attempt in range(max_retries):
            try:
                return await self.chat(
                    messages=messages,
                    model=primary_model,
                    stream=stream,
                    response_length=response_length,  # Przekaż konfigurację długości
                )
            except Exception as e:
                logger.warning(
                    f"Error with primary model {primary_model}, attempt {attempt + 1}: {e!s}"
                )
                await asyncio.sleep(0.5 * (2**attempt))

        # If primary model fails, try fallback model
        if not fallback_model:
            fallback_model = self.default_model

        logger.info(f"Falling back to {fallback_model}")

        try:
            return await self.chat(
                messages=messages,
                model=fallback_model,
                stream=stream,
                response_length=response_length,  # Przekaż konfigurację długości
            )
        except Exception as e:
            logger.error(f"Error with fallback model {fallback_model}: {e!s}")
            # If all else fails, return error
            return {
                "message": {
                    "content": f"Error processing request with all models: {e!s}"
                },
                "response": f"Error processing request with all models: {e!s}",
            }

    def get_available_models(self) -> list[str]:
        return [*list(self.model_configs.keys()), "perplexity"]

    def get_model_info(self, model_name: str) -> dict[str, Any]:
        if model_name == "perplexity":
            return {"name": "perplexity", "type": "api", "default": False}
        if model_name in self.model_configs:
            config = self.model_configs[model_name]
            return {
                "name": config.name,
                "type": "local",
                "default": model_name == self.default_model,
                "description": config.description,
            }
        raise ValueError(f"Unknown model: {model_name}")

    def _generate_cache_key(
        self, messages: list[dict[str, str]], model: str, options: dict[str, Any]
    ) -> str:
        """Generuje klucz cache na podstawie wiadomości, modelu i opcji"""
        import hashlib

        content = f"{model}:{json.dumps(messages, sort_keys=True)}:{json.dumps(options, sort_keys=True)}"
        return hashlib.md5(content.encode()).hexdigest()

    def _update_model_stats(
        self, model: str, latency: float, success: bool, error: str | None = None
    ):
        """Aktualizuje statystyki modelu"""
        if model in self.model_stats:
            stats = self.model_stats[model]
            stats.total_requests += 1
            stats.last_used = datetime.now()

            if success:
                stats.successful_requests += 1
                # Oblicz średnią latencję
                if stats.successful_requests > 0:
                    stats.average_latency = (
                        stats.average_latency * (stats.successful_requests - 1)
                        + latency
                    ) / stats.successful_requests
            else:
                stats.failed_requests += 1
                if error:
                    stats.last_error = error


# Global instance
hybrid_llm_client = HybridLLMClient()
