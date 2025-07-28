import asyncio
from collections.abc import AsyncGenerator
from functools import lru_cache
import logging
import re
import time
from typing import Any

from agents.base_agent import BaseAgent
from agents.interfaces import AgentResponse
from agents.response_generator import ResponseGenerator
from agents.tools.search_providers import (
    DuckDuckGoSearchProvider,
    PerplexicaSearchProvider,
    SerpAPISearchProvider,
    WikipediaSearchProvider,
)
from core.anti_hallucination_decorator_optimized import with_search_validation
from core.anti_hallucination_system import ValidationLevel
from core.decorators import handle_exceptions
from core.hybrid_llm_client import hybrid_llm_client
from core.search_cache import search_cache
from integrations.web_search import web_search

logger = logging.getLogger(__name__)


class SearchAgentInput:
    """Input model for SearchAgent"""

    def __init__(
        self, query: str, model: str | None = None, max_results: int = 5
    ) -> None:
        self.query = query
        self.model = (
            model or "SpeakLeash/bielik-11b-v2.3-instruct:Q5_K_M"
        )  # Use Bielik-11B as default
        self.max_results = max_results


class SearchAgent(BaseAgent):
    """
    Agent do wyszukiwania informacji z różnych źródeł (Perplexica, Wikipedia, DuckDuckGo).
    Obsługuje weather queries przez Perplexica weather endpoint.
    Wybór providera na podstawie heurystyki, prefixu lub fallbacku.
    Zintegrowany z ResponseGenerator dla spójnych odpowiedzi.
    Zoptymalizowany z zaawansowanym cache'owaniem i równoległym przetwarzaniem.
    """

    def __init__(self, config: dict[str, Any] | None = None, **kwargs) -> None:
        super().__init__(name="SearchAgent", **kwargs)

        # Initialize search providers with connection pooling
        self.search_providers = {
            "perplexica": PerplexicaSearchProvider(),  # Primary provider with weather support
            "serpapi": SerpAPISearchProvider(),        # Google Search with high-quality results
            "wikipedia": WikipediaSearchProvider(),
            "duck": DuckDuckGoSearchProvider(),
        }
        self.default_provider = "perplexica"
        self.response_generator = ResponseGenerator()

        # Enhanced caching configuration
        self.cache_enabled = config.get("cache_enabled", True) if config else True
        self.cache_ttl = config.get("cache_ttl", 3600) if config else 3600  # 1 hour
        self.parallel_search_enabled = (
            config.get("parallel_search_enabled", True) if config else True
        )
        self.max_parallel_searches = (
            config.get("max_parallel_searches", 3) if config else 3
        )

        # Initialize HTTP client with connection pooling
        import httpx

        self.http_client = httpx.AsyncClient(
            timeout=30.0,
            limits=httpx.Limits(max_connections=20, max_keepalive_connections=10),
        )

        # Initialize web_search and knowledge verification threshold
        self.web_search = web_search
        self.knowledge_verification_threshold = (
            config.get("knowledge_verification_threshold", 0.7) if config else 0.7
        )

        # Weather keywords for detection
        self.weather_keywords = {
            "pogoda",
            "weather",
            "temperatura",
            "temperature",
            "deszcz",
            "rain",
            "śnieg",
            "snow",
            "wiatr",
            "wind",
            "wilgotność",
            "humidity",
            "słońce",
            "sun",
            "chmury",
            "clouds",
            "burza",
            "storm",
            "mgła",
            "fog",
            "grad",
            "hail",
        }

        # Performance metrics
        self.performance_metrics = {
            "total_searches": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "average_response_time": 0.0,
            "parallel_searches": 0,
        }

        # Ignoruj nieznane kwargs przekazywane przez DI, testy, monitoring, kontenery
        for key in list(kwargs.keys()):
            if key not in [
                "name",
                "error_handler",
                "fallback_manager",
                "alert_service",
            ]:
                kwargs.pop(key, None)

    @lru_cache(maxsize=1000)
    def detect_search_type(self, query: str) -> str:
        """
        Wybiera providera na podstawie prefixu lub heurystyki.
        Obsługuje weather queries przez Perplexica.
        Zoptymalizowany z cache'owaniem.
        """
        q = query.lower().strip()

        # Weather queries - kieruj do Perplexica
        if any(keyword in q for keyword in self.weather_keywords):
            return "perplexica"

        # Explicit provider prefixes
        if q.startswith("serpapi:"):
            return "serpapi"
        if q.startswith("google:"):
            return "serpapi"
        if q.startswith("wikipedia:"):
            return "wikipedia"
        if q.startswith(("duck:", "duckduckgo:")):
            return "duck"
        if q.startswith("perplexica:"):
            return "perplexica"

        # High-priority queries that benefit from Google's knowledge graph
        high_priority_keywords = [
            "aktualności", "news", "latest", "current", "today",
            "najnowsze", "breaking", "pilne", "wydarzenie",
            "definicja", "co to jest", "what is", "meaning",
            "firma", "company", "corporation", "organization"
        ]
        if any(kw in q for kw in high_priority_keywords):
            # Use SerpAPI if available, otherwise fallback
            serpapi_provider = self.search_providers.get("serpapi")
            if serpapi_provider and serpapi_provider.is_enabled():
                return "serpapi"

        # Heurystyka encyklopedyczna
        wiki_keywords = [
            "wikipedia",
            "kto to",
            "co to",
            "definicja",
            "biografia",
            "historia",
            "encyklopedia",
        ]
        if any(kw in q for kw in wiki_keywords):
            return "wikipedia"
        # Heurystyka webowa
        duck_keywords = [
            "szukaj",
            "search",
            "find",
            "najlepsze strony",
            "aktualności",
            "news",
        ]
        if any(kw in q for kw in duck_keywords):
            return "duck"
        return self.default_provider

    def format_search_results(
        self, results: list[dict[str, Any]], provider: str
    ) -> str:
        """
        Formatuje wyniki wyszukiwania w czytelny tekst.
        Obsługuje weather results z Perplexica.
        """
        if not results:
            return "Nie znaleziono wyników wyszukiwania."

        # Special handling for weather results
        if (
            provider == "perplexica"
            and results
            and results[0].get("source") == "perplexica_weather"
        ):
            weather_result = results[0]
            weather_data = weather_result.get("weather_data", {})
            location = weather_result.get("location", "Nieznana lokalizacja")

            weather_text = f"🌤️ **Pogoda w {location}**\n\n"
            weather_text += (
                f"🌡️ **Temperatura:** {weather_data.get('temperature', 'N/A')}°C\n"
            )
            weather_text += f"☁️ **Warunki:** {weather_data.get('condition', 'N/A')}\n"
            weather_text += (
                f"💧 **Wilgotność:** {weather_data.get('humidity', 'N/A')}%\n"
            )
            weather_text += (
                f"💨 **Wiatr:** {weather_data.get('windSpeed', 'N/A')} km/h\n"
            )

            if weather_data.get("icon"):
                weather_text += f"🎯 **Ikona:** {weather_data['icon']}\n"

            return weather_text

        formatted_results = []
        for i, result in enumerate(results[:5], 1):  # Maksymalnie 5 wyników
            title = result.get("title", "Brak tytułu")
            snippet = result.get("snippet", "Brak opisu")

            if provider == "wikipedia":
                pageid = result.get("pageid", "")
                formatted_results.append(
                    f"{i}. **{title}** (ID: {pageid})\n   {snippet}"
                )
            elif provider == "perplexica":
                url = result.get("url", "")
                confidence = result.get("confidence", 0)
                formatted_results.append(
                    f"{i}. **{title}** (Pewność: {confidence:.1%})\n   {snippet}\n   URL: {url}"
                )
            elif provider == "serpapi":
                url = result.get("url", "")
                confidence = result.get("confidence", 0)
                result_type = result.get("result_type", "organic")
                
                # Special formatting for different SerpAPI result types
                if result_type == "answer_box":
                    formatted_results.append(
                        f"📋 **{title}** (Odpowiedź Google)\n   {snippet}\n   URL: {url}"
                    )
                elif result_type == "knowledge_graph":
                    formatted_results.append(
                        f"🧠 **{title}** (Wiedza Google)\n   {snippet}\n   URL: {url}"
                    )
                elif result_type == "featured_snippet":
                    formatted_results.append(
                        f"⭐ **{title}** (Fragment wyróżniony)\n   {snippet}\n   URL: {url}"
                    )
                elif result_type == "news":
                    date = result.get("date", "")
                    source_name = result.get("source_name", "")
                    formatted_results.append(
                        f"📰 **{title}** ({source_name})\n   {snippet}\n   📅 {date}\n   URL: {url}"
                    )
                elif result_type == "image":
                    width = result.get("width", 0)
                    height = result.get("height", 0)
                    formatted_results.append(
                        f"🖼️ **{title}** ({width}x{height})\n   {snippet}\n   URL: {url}"
                    )
                else:
                    formatted_results.append(
                        f"{i}. **{title}** (Google - Pewność: {confidence:.1%})\n   {snippet}\n   URL: {url}"
                    )
            else:  # duck
                url = result.get("url", "")
                formatted_results.append(
                    f"{i}. **{title}**\n   {snippet}\n   URL: {url}"
                )

        return "\n\n".join(formatted_results)

    @with_search_validation(
        validation_level=ValidationLevel.MODERATE
    )
    async def process(self, input_data: dict[str, Any]) -> AgentResponse:
        """
        Główna metoda przetwarzania zgodna z interfejsem BaseAgent.
        Zoptymalizowana z pomiarem wydajności.
        """
        start_time = time.time()
        query = input_data.get("query", "")
        context = input_data.get("context")

        if not query:
            return AgentResponse(
                success=False,
                error="Brak zapytania wyszukiwania",
                text="Proszę podać zapytanie do wyszukiwania.",
            )

        try:
            # Zoptymalizowane przetwarzanie z równoległymi wyszukiwaniami
            if self.parallel_search_enabled:
                results = await self._process_request_parallel(query, context)
            else:
                results = await self.process_request(query, context)

            # ANTY-HALUCYNACYJNA WALIDACJA WYNIKÓW
            validated_results = self._validate_search_results(results, query)

            if not validated_results["is_valid"]:
                return AgentResponse(
                    success=True,
                    text="Przepraszam, ale nie mogę zweryfikować wiarygodności znalezionych informacji. Zalecam sprawdzenie źródeł osobiście.",
                    confidence=0.3,
                    metadata={
                        "validation_warning": True,
                        "processing_time": time.time() - start_time,
                    },
                )

            formatted_results = self.format_search_results(
                results, self.detect_search_type(query)
            )

            # Aktualizuj metryki wydajności
            processing_time = time.time() - start_time
            self._update_performance_metrics(processing_time, cache_hit=False)

            return AgentResponse(
                success=True,
                text=formatted_results,
                confidence=validated_results.get("confidence", 0.7),
                metadata={
                    "provider": self.detect_search_type(query),
                    "results_count": len(results),
                    "processing_time": processing_time,
                    "cache_hit": False,
                },
            )

        except Exception as e:
            logger.error(f"SearchAgent error: {e}")
            processing_time = time.time() - start_time
            self._update_performance_metrics(processing_time, cache_hit=False)

            return AgentResponse(
                success=False,
                error=f"Błąd wyszukiwania: {e!s}",
                text="Przepraszam, wystąpił błąd podczas wyszukiwania. Spróbuj ponownie później.",
                metadata={"processing_time": processing_time},
            )

    async def _process_request_parallel(
        self, query: str, context: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        """
        Zoptymalizowane przetwarzanie z równoległymi wyszukiwaniami.
        """
        provider_key = self.detect_search_type(query)

        # Sprawdź cache jeśli włączony
        if self.cache_enabled:
            cached_results = search_cache.get(query, provider_key)
            if cached_results:
                logger.info(f"Cache hit for query: {query}, provider: {provider_key}")
                self.performance_metrics["cache_hits"] += 1
                return cached_results

        self.performance_metrics["cache_misses"] += 1

        # Równoległe wyszukiwanie z fallback
        search_tasks = []

        # Główny provider
        search_tasks.append(self._search_with_provider(query, provider_key))

        # Fallback providers (równolegle)
        fallback_providers = [
            k for k in self.search_providers if k != provider_key
        ]
        for fallback_key in fallback_providers[: self.max_parallel_searches - 1]:
            search_tasks.append(self._search_with_provider(query, fallback_key))

        # Wykonaj wszystkie wyszukiwania równolegle
        results = await asyncio.gather(*search_tasks, return_exceptions=True)

        # Wybierz najlepszy wynik
        best_results = []
        for result in results:
            if isinstance(result, list) and result:
                best_results = result
                break

        # Zapisz w cache jeśli włączony
        if self.cache_enabled and best_results:
            search_cache.set(query, provider_key, best_results, ttl=self.cache_ttl)

        self.performance_metrics["parallel_searches"] += 1
        return best_results

    async def _search_with_provider(
        self, query: str, provider_key: str
    ) -> list[dict[str, Any]]:
        """
        Wyszukiwanie z konkretnym providerem z obsługą błędów.
        """
        try:
            provider = self.search_providers[provider_key]
            
            # Handle special search types for SerpAPI
            if provider_key == "serpapi" and hasattr(provider, 'is_enabled') and provider.is_enabled():
                # Check for image search
                if any(keyword in query.lower() for keyword in ["obrazy", "images", "zdjęcia", "photos"]):
                    results = await provider.search_images(query)
                    return results if results else []
                
                # Check for news search
                elif any(keyword in query.lower() for keyword in ["wiadomości", "news", "aktualności"]):
                    results = await provider.search_news(query)
                    return results if results else []
            
            results = await provider.search(query)
            return results if results else []
        except Exception as e:
            logger.warning(f"Search failed with {provider_key}: {e}")
            return []

    async def process_request(
        self, query: str, context: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        """
        Przetwarza zapytanie, wybiera providera, obsługuje fallback i cache.
        Zwraca listę wyników (tytuł, snippet, url/pageid).
        Zoptymalizowane z lepszym cache'owaniem.
        """
        provider_key = self.detect_search_type(query)

        # Sprawdź cache jeśli włączony
        if self.cache_enabled:
            cached_results = search_cache.get(query, provider_key)
            if cached_results:
                logger.info(f"Cache hit for query: {query}, provider: {provider_key}")
                self.performance_metrics["cache_hits"] += 1
                return cached_results

        self.performance_metrics["cache_misses"] += 1

        provider = self.search_providers[provider_key]
        try:
            results = await provider.search(query)
            if results:
                # Zapisz w cache jeśli włączony
                if self.cache_enabled:
                    search_cache.set(query, provider_key, results, ttl=self.cache_ttl)
                return results

            # Fallback na drugi provider jeśli brak wyników
            fallback_key = "duck" if provider_key == "wikipedia" else "wikipedia"
            fallback_provider = self.search_providers[fallback_key]

            # Sprawdź cache dla fallback providera
            if self.cache_enabled:
                cached_fallback = search_cache.get(query, fallback_key)
                if cached_fallback:
                    logger.info(
                        f"Cache hit for fallback query: {query}, provider: {fallback_key}"
                    )
                    return cached_fallback

            fallback_results = await fallback_provider.search(query)

            # Zapisz fallback wyniki w cache
            if self.cache_enabled and fallback_results:
                search_cache.set(
                    query, fallback_key, fallback_results, ttl=self.cache_ttl
                )

            return fallback_results

        except Exception as e:
            logger.error(f"SearchAgent error with {provider_key}: {e}")
            # Fallback na drugi provider w razie błędu
            fallback_key = "duck" if provider_key == "wikipedia" else "wikipedia"
            try:
                fallback_provider = self.search_providers[fallback_key]

                # Sprawdź cache dla fallback providera
                if self.cache_enabled:
                    cached_fallback = search_cache.get(query, fallback_key)
                    if cached_fallback:
                        return cached_fallback

                fallback_results = await fallback_provider.search(query)

                # Zapisz fallback wyniki w cache
                if self.cache_enabled and fallback_results:
                    search_cache.set(
                        query, fallback_key, fallback_results, ttl=self.cache_ttl
                    )

                return fallback_results
            except Exception as e2:
                logger.error(f"SearchAgent fallback error: {e2}")
                return []

    def _update_performance_metrics(self, processing_time: float, cache_hit: bool):
        """
        Aktualizuje metryki wydajności.
        """
        self.performance_metrics["total_searches"] += 1

        # Aktualizuj średni czas odpowiedzi
        current_avg = self.performance_metrics["average_response_time"]
        total_searches = self.performance_metrics["total_searches"]
        self.performance_metrics["average_response_time"] = (
            current_avg * (total_searches - 1) + processing_time
        ) / total_searches

    def get_performance_metrics(self) -> dict[str, Any]:
        """
        Zwraca metryki wydajności agenta.
        """
        return {
            **self.performance_metrics,
            "cache_hit_rate": (
                self.performance_metrics["cache_hits"]
                / max(self.performance_metrics["total_searches"], 1)
            ),
            "parallel_search_rate": (
                self.performance_metrics["parallel_searches"]
                / max(self.performance_metrics["total_searches"], 1)
            ),
        }

    @handle_exceptions(max_retries=2)
    async def process_with_verification(
        self, input_data: dict[str, Any]
    ) -> AgentResponse:
        """Main processing method - performs search and returns results in a stream"""
        query = input_data.get("query", "")
        if not query:
            return AgentResponse(
                success=False,
                error="Query is required",
                text="Przepraszam, ale potrzebuję zapytania do wyszukania.",
            )

        max_results = input_data.get("max_results", 5)
        use_perplexity = input_data.get("use_perplexity", True)  # Domyślnie Perplexity
        verify_knowledge = input_data.get(
            "verify_knowledge", True
        )  # Domyślnie włączona weryfikacja

        async def stream_generator() -> AsyncGenerator[str, None]:
            try:
                yield "Rozpoczynam wyszukiwanie z weryfikacją wiedzy...\n"

                if use_perplexity:
                    logger.info(f"Using Perplexity for search query: {query}")
                    yield "Korzystam z Perplexity...\n"
                    search_results = await self.web_search.search(
                        query, max_results=max_results
                    )
                    if search_results:
                        # Format results as content
                        content_parts = []
                        for result in search_results:
                            content_parts.append(f"**{result['title']}**")
                            content_parts.append(f"{result['snippet']}")
                            content_parts.append(f"Źródło: {result['url']}\n")
                        yield "\n".join(content_parts)
                    else:
                        yield "Nie znaleziono wyników wyszukiwania."
                else:
                    # Użyj ulepszonego systemu wyszukiwania z weryfikacją wiedzy
                    logger.info(f"Using enhanced web search for query: {query}")
                    yield "Korzystam z ulepszonego systemu wyszukiwania...\n"

                    if verify_knowledge:
                        yield "🔍 Weryfikuję wiarygodność źródeł...\n"
                        enhanced_result = await self._enhanced_search_with_verification(
                            query, max_results
                        )
                        yield enhanced_result
                    else:
                        basic_result = await self._basic_search(query, max_results)
                        yield basic_result

            except Exception as e:
                logger.error(f"[SearchAgent] Error during stream generation: {e}")
                yield f"Wystąpił wewnętrzny błąd: {e}"

        return AgentResponse(
            success=True,
            text_stream=stream_generator(),
            message="Search stream started.",
        )

    async def _enhanced_search_with_verification(
        self, query: str, max_results: int
    ) -> str:
        """Perform enhanced search with knowledge verification"""
        try:
            # Użyj nowego systemu wyszukiwania z weryfikacją
            search_response = await web_search.search_with_verification(
                query, max_results
            )

            if not search_response["results"]:
                return "Nie znaleziono odpowiednich wyników wyszukiwania."

            # Analizuj wyniki wyszukiwania
            verified_results = [
                r for r in search_response["results"] if r["knowledge_verified"]
            ]
            total_results = len(search_response["results"])
            verification_score = search_response["knowledge_verification_score"]

            # Przygotuj odpowiedź
            response_parts = []
            response_parts.append(f"📊 **Wyniki wyszukiwania dla: '{query}'**\n")
            response_parts.append(f"🔍 Znaleziono {total_results} wyników")
            response_parts.append(
                f"✅ Zweryfikowane źródła: {len(verified_results)}/{total_results}"
            )
            response_parts.append(
                f"📈 Wskaźnik wiarygodności: {verification_score:.2f}\n"
            )

            # Dodaj najlepsze wyniki
            response_parts.append("**Najlepsze wyniki:**\n")
            for i, result in enumerate(search_response["results"][:3], 1):
                verification_icon = "✅" if result["knowledge_verified"] else "⚠️"
                confidence_icon = (
                    "🟢"
                    if result["confidence"] > 0.7
                    else "🟡" if result["confidence"] > 0.4 else "🔴"
                )

                response_parts.append(
                    f"{i}. {verification_icon} {confidence_icon} **{result['title']}**"
                )
                response_parts.append(f"   📝 {result['snippet'][:150]}...")
                response_parts.append(f"   🔗 {result['url']}")
                response_parts.append(f"   📊 Wiarygodność: {result['confidence']:.2f}")
                response_parts.append("")

            # Dodaj rekomendację na podstawie weryfikacji
            if verification_score > self.knowledge_verification_threshold:
                response_parts.append(
                    "✅ **Wysoka wiarygodność źródeł** - wyniki są godne zaufania."
                )
            elif verification_score > 0.4:
                response_parts.append(
                    "⚠️ **Średnia wiarygodność źródeł** - zalecana dodatkowa weryfikacja."
                )
            else:
                response_parts.append(
                    "🔴 **Niska wiarygodność źródeł** - zalecana ostrożność przy interpretacji."
                )

            return "\n".join(response_parts)

        except Exception as e:
            logger.error(f"Error in enhanced search: {e}")
            return f"Błąd podczas wyszukiwania: {e}"

    async def _basic_search(self, query: str, max_results: int) -> str:
        """Perform basic search without verification"""
        try:
            results = await web_search.search(query, max_results)

            if not results:
                return "Nie znaleziono odpowiednich wyników wyszukiwania."

            response_parts = []
            response_parts.append(f"📊 **Wyniki wyszukiwania dla: '{query}'**\n")

            for i, result in enumerate(results[:3], 1):
                response_parts.append(f"{i}. **{result['title']}**")
                response_parts.append(f"   📝 {result['snippet'][:150]}...")
                response_parts.append(f"   🔗 {result['url']}")
                response_parts.append("")

            return "\n".join(response_parts)

        except Exception as e:
            logger.error(f"Error in basic search: {e}")
            return f"Błąd podczas wyszukiwania: {e}"

    async def _perform_search(
        self, query: str, model: str, max_results: int
    ) -> dict[str, Any]:
        """Perform search using Perplexity API"""
        try:
            # Translate query to English for better results
            english_query = await self._translate_to_english(query, model)

            # Perform search with Perplexity
            search_results = await self.web_search.search(
                query=english_query,
                max_results=max_results,
            )

            if search_results:
                # Format results as content
                content_parts = []
                for result in search_results:
                    content_parts.append(f"**{result['title']}**")
                    content_parts.append(f"{result['snippet']}")
                    content_parts.append(f"Źródło: {result['url']}")

                content = "\n\n".join(content_parts)

                # Translate response back to Polish if needed
                polish_response = await self._translate_to_polish(content, model)

                return {
                    "success": True,
                    "content": polish_response,
                    "source": "web_search",
                    "query": query,
                }
            return {"success": False, "error": "No results found", "content": ""}

        except Exception as e:
            logger.error(f"Error in Perplexity search: {e}")
            return {"success": False, "error": str(e), "content": ""}

    async def _duckduckgo_search(self, query: str) -> dict[str, Any]:
        """Fallback search using DuckDuckGo"""
        try:
            # Simple DuckDuckGo search implementation
            search_url = f"https://api.duckduckgo.com/?q={query}&format=json&no_html=1&skip_disambig=1"

            response = await self.http_client.get(search_url)
            response.raise_for_status()

            data = response.json()

            # Extract relevant information
            abstract = data.get("Abstract", "")
            answer = data.get("Answer", "")
            related_topics = data.get("RelatedTopics", [])

            # Combine results
            content_parts = []
            if answer:
                content_parts.append(f"Odpowiedź: {answer}")
            if abstract:
                content_parts.append(f"Opis: {abstract}")
            if related_topics:
                topics = [topic.get("Text", "") for topic in related_topics[:3]]
                content_parts.append(f"Powiązane tematy: {'; '.join(topics)}")

            content = (
                "\n\n".join(content_parts)
                if content_parts
                else "Nie znaleziono odpowiednich wyników."
            )

            return {
                "success": True,
                "content": content,
                "source": "duckduckgo",
                "query": query,
            }

        except Exception as e:
            logger.error(f"Error in DuckDuckGo search: {e}")
            return {"success": False, "error": str(e), "content": ""}

    async def _translate_to_english(self, polish_query: str, model: str) -> str:
        """Translate Polish query to English for better search results"""
        prompt = (
            f"Przetłumacz poniższe zapytanie z języka polskiego na angielski:\n\n"
            f"Zapytanie: '{polish_query}'\n\n"
            f"Zwróć tylko tłumaczenie, bez dodatkowego tekstu."
        )

        try:
            response = await hybrid_llm_client.chat(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": "Jesteś pomocnym asystentem, który tłumaczy zapytania z polskiego na angielski.",
                    },
                    {"role": "user", "content": prompt},
                ],
                stream=False,
            )

            if not response or not isinstance(response, dict):
                return polish_query

            content = response.get("message", {}).get("content", "")
            if not content:
                return polish_query

            # Clean up the response
            content = content.strip()
            if content.startswith('"') and content.endswith('"'):
                content = content[1:-1]

            return content if content else polish_query

        except Exception as e:
            logger.error(f"Translation error: {e}")
            return polish_query

    async def _translate_to_polish(self, english_content: str, model: str) -> str:
        """Translate English content back to Polish"""
        prompt = (
            f"Przetłumacz poniższą treść z języka angielskiego na polski:\n\n"
            f"Treść: '{english_content}'\n\n"
            f"Zwróć tylko tłumaczenie, bez dodatkowego tekstu."
        )

        try:
            response = await hybrid_llm_client.chat(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": "Jesteś pomocnym asystentem, który tłumaczy treść z angielskiego na polski.",
                    },
                    {"role": "user", "content": prompt},
                ],
                stream=False,
            )

            if not response or not isinstance(response, dict):
                return english_content

            content = response.get("message", {}).get("content", "")
            return content.strip() if content else english_content

        except Exception as e:
            logger.error(f"Translation error: {e}")
            return english_content

    def _validate_search_results(
        self, results: list[dict[str, Any]], query: str
    ) -> dict[str, Any]:
        """Waliduje wyniki wyszukiwania pod kątem halucynacji"""
        if not results:
            return {"is_valid": False, "reason": "Brak wyników wyszukiwania"}

        # Sprawdź czy wyniki zawierają niezweryfikowane informacje
        query_lower = query.lower()

        # Wzorce halucynacji dla wyszukiwania - zmniejszona restrykcyjność
        hallucination_patterns = [
            # Tylko najbardziej podejrzane wzorce
            r"jego\s+najważniejsze\s+osiągnięcia\s+to\s+bez\s+wątpienia",
            r"obchodzony\s+jest\s+dokładnie\s+[a-ząćęłńóśźż\s]+dzień\s+o\s+godzinie",
        ]

        # Sprawdź każdy wynik
        for result in results:
            snippet = result.get("snippet", "").lower()
            title = result.get("title", "").lower()

            # Sprawdź czy wynik zawiera wzorce halucynacji
            for pattern in hallucination_patterns:
                if re.search(pattern, snippet, re.IGNORECASE) or re.search(
                    pattern, title, re.IGNORECASE
                ):
                    return {
                        "is_valid": False,
                        "reason": "Wyniki zawierają niezweryfikowane informacje",
                    }

        # Sprawdź czy wyniki są odpowiednie dla zapytania - mniej restrykcyjna walidacja
        if any(word in query_lower for word in ["kto", "kim", "osoba", "biografia"]):
            # Dla zapytań o osoby, sprawdź czy są jakiekolwiek źródła
            has_sources = any(
                "wikipedia" in result.get("url", "").lower()
                or "encyklopedia" in result.get("url", "").lower()
                or "biografia" in result.get("url", "").lower()
                or len(result.get("snippet", "")) > 50  # Akceptuj wyniki z wystarczającą ilością treści
                for result in results
            )

            if not has_sources and len(results) < 1:
                return {
                    "is_valid": False,
                    "reason": "Brak wyników wyszukiwania dla informacji o osobie",
                }

        return {"is_valid": True, "reason": "Wyniki zweryfikowane"}

    @handle_exceptions(max_retries=1)
    def get_dependencies(self) -> list[type]:
        """Return list of dependencies this agent requires"""
        # Import modules here to avoid circular imports
        import httpx

        from core.hybrid_llm_client import hybrid_llm_client
        from core.response_generator import ResponseGenerator
        from integrations.web_search import web_search

        return [
            type(httpx),
            type(hybrid_llm_client),
            type(web_search),
            type(ResponseGenerator),
        ]

    def get_metadata(self) -> dict[str, Any]:
        """Zwraca metadane agenta."""
        return {
            "agent_type": "search",
            "capabilities": [
                "web_search",
                "wikipedia_search",
                "google_search",
                "image_search",
                "news_search",
                "fallback_support",
                "caching",
                "knowledge_graph",
                "featured_snippets",
            ],
            "providers": list(self.search_providers.keys()),
            "version": "1.0.0",
            "cache_enabled": self.cache_enabled,
            "cache_stats": search_cache.get_stats() if self.cache_enabled else None,
        }

    def is_healthy(self) -> bool:
        """Check if the agent is healthy and ready to process requests"""
        return True  # Simple health check - could be enhanced

    async def verify_knowledge_claim(
        self, claim: str, context: str = ""
    ) -> dict[str, Any]:
        """Verify a specific knowledge claim against external sources"""
        try:
            # Search for the claim
            search_query = f"{claim} {context}".strip()
            search_response = await web_search.search_with_verification(
                search_query, max_results=3
            )

            # Analyze results for claim verification
            verified_sources = [
                r for r in search_response["results"] if r["knowledge_verified"]
            ]
            high_confidence_sources = [
                r for r in search_response["results"] if r["confidence"] > 0.7
            ]

            verification_result = {
                "claim": claim,
                "verified": len(verified_sources) > 0,
                "confidence_score": search_response["knowledge_verification_score"],
                "high_confidence_sources": len(high_confidence_sources),
                "total_sources": len(search_response["results"]),
                "supporting_evidence": [r["snippet"] for r in verified_sources[:2]],
                "sources": [r["url"] for r in verified_sources[:2]],
            }

            return verification_result

        except Exception as e:
            logger.error(f"Error verifying knowledge claim: {e}")
            return {
                "claim": claim,
                "verified": False,
                "error": str(e),
                "confidence_score": 0.0,
            }
