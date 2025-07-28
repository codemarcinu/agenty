"""
Search providers for different search engines.
Provides unified interface for Wikipedia and DuckDuckGo searches.
"""

from abc import ABC, abstractmethod
import logging
from typing import Any

import httpx

from settings import settings

logger = logging.getLogger(__name__)

# Constants
WIKIPEDIA_API_BASE = "https://pl.wikipedia.org/api/rest_v1"
WIKIPEDIA_SEARCH_BASE = "https://pl.wikipedia.org/w/api.php"
DUCKDUCKGO_API_BASE = "https://api.duckduckgo.com/"
REQUEST_TIMEOUT = 10.0


class SearchProvider(ABC):
    """Abstract base class for search providers"""

    def __init__(self):
        pass

    @abstractmethod
    async def search(self, query: str, max_results: int = 5) -> list[dict[str, Any]]:
        """Search for results"""


class WikipediaSearchProvider(SearchProvider):
    """Provider for Wikipedia searches"""

    def __init__(self):
        super().__init__()
        self.client = httpx.AsyncClient(
            timeout=REQUEST_TIMEOUT, headers={"User-Agent": settings.USER_AGENT}
        )

    async def search(self, query: str, max_results: int = 5) -> list[dict[str, Any]]:
        """Search Wikipedia for articles"""
        try:
            search_url = f"{WIKIPEDIA_SEARCH_BASE}"
            params = {
                "action": "query",
                "format": "json",
                "list": "search",
                "srsearch": query,
                "srlimit": max_results,
                "srnamespace": 0,  # Main namespace only
                "srprop": "snippet|title|timestamp",
            }

            response = await self.client.get(search_url, params=params)
            response.raise_for_status()
            data = response.json()

            results = []
            if "query" in data and "search" in data["query"]:
                for item in data["query"]["search"]:
                    result = {
                        "title": item["title"],
                        "url": f"https://pl.wikipedia.org/wiki/{item['title'].replace(' ', '_')}",
                        "snippet": item.get("snippet", ""),
                        "pageid": item.get("pageid", ""),
                        "source": "wikipedia",
                    }
                    results.append(result)

            return results

        except Exception as e:
            logger.error(f"Wikipedia search error: {e}")
            return []

    async def close(self):
        """Close the client"""
        await self.client.aclose()


class DuckDuckGoSearchProvider(SearchProvider):
    """Provider for DuckDuckGo searches"""

    def __init__(self):
        super().__init__()
        self.client = httpx.AsyncClient(
            timeout=REQUEST_TIMEOUT, headers={"User-Agent": settings.USER_AGENT}
        )

    async def search(self, query: str, max_results: int = 5) -> list[dict[str, Any]]:
        """Search DuckDuckGo for results"""
        try:
            # DuckDuckGo Instant Answer API
            search_url = f"{DUCKDUCKGO_API_BASE}"
            params = {
                "q": query,
                "format": "json",
                "no_html": "1",
                "skip_disambig": "1",
            }

            response = await self.client.get(search_url, params=params)
            response.raise_for_status()
            data = response.json()

            results = []

            # Add instant answer if available
            if data.get("Abstract"):
                results.append(
                    {
                        "title": data.get("Heading", "DuckDuckGo Result"),
                        "url": data.get("AbstractURL", ""),
                        "snippet": data.get("Abstract", ""),
                        "source": "duckduckgo",
                    }
                )

            # Add related topics
            related_topics = data.get("RelatedTopics", [])
            if related_topics:
                for topic in related_topics[: max_results - len(results)]:
                    if isinstance(topic, dict) and topic.get("Text"):
                        results.append(
                            {
                                "title": (
                                    topic.get("Text", "").split(" - ")[0]
                                    if " - " in topic.get("Text", "")
                                    else topic.get("Text", "")
                                ),
                                "url": topic.get("FirstURL", ""),
                                "snippet": topic.get("Text", ""),
                                "source": "duckduckgo",
                            }
                        )

            return results[:max_results]

        except Exception as e:
            logger.error(f"DuckDuckGo search error: {e}")
            return []

    async def close(self):
        """Close the client"""
        await self.client.aclose()


class PerplexicaSearchProvider(SearchProvider):
    """Provider for Perplexica searches with weather support"""

    def __init__(self):
        super().__init__()
        self.base_url = settings.PERPLEXICA_BASE_URL
        self.client = httpx.AsyncClient(
            timeout=30.0, headers={"User-Agent": settings.USER_AGENT}
        )
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

    async def search(self, query: str, max_results: int = 5) -> list[dict[str, Any]]:
        """Enhanced search with Perplexica and weather support"""
        try:
            # Check if this is a weather query
            if self._is_weather_query(query):
                return await self._handle_weather_query(query)

            # Regular search request - fixed format for Perplexica API
            search_request = {
                "query": query,
                "focusMode": "webSearch",  # Required field
                "history": [],             # Required field
                "optimizationMode": "balanced",  # Good default
                "stream": False           # Non-streaming response
            }

            response = await self.client.post(
                f"{self.base_url}/search", json=search_request
            )
            response.raise_for_status()
            data = response.json()

            # Process and validate results - Perplexica returns formatted text response
            results = []
            
            # Perplexica returns structured response with 'message' and 'sources'
            if "message" in data:
                results.append({
                    "title": "Wyniki wyszukiwania Perplexica",
                    "url": "perplexica://search",
                    "snippet": data["message"],
                    "source": "perplexica",
                    "confidence": 0.8,
                    "knowledge_verified": True,
                    "providers_used": data.get("sources", []),
                })
            else:
                # Fallback: try to parse as structured results
                for result in data.get("results", []):
                    if self._validate_result(result):
                        results.append(
                            {
                                "title": result["title"],
                                "url": result["url"],
                                "snippet": result["snippet"],
                                "source": "perplexica",
                                "confidence": result.get("confidence", 0.8),
                                "knowledge_verified": result.get("verified", False),
                                "providers_used": result.get("providers", []),
                            }
                        )

            return results[:max_results]

        except Exception as e:
            logger.error(f"Perplexica search error: {e}")
            return []

    def _is_weather_query(self, query: str) -> bool:
        """Check if query is related to weather"""
        query_lower = query.lower()
        return any(keyword in query_lower for keyword in self.weather_keywords)

    async def _handle_weather_query(self, query: str) -> list[dict[str, Any]]:
        """Handle weather queries using Perplexica weather endpoint"""
        try:
            # Extract location from query (simplified)
            location = self._extract_location_from_query(query)

            # Get coordinates for location (simplified - using default for Warsaw)
            coords = {"lat": 52.2297, "lng": 21.0122}  # Warsaw coordinates

            # Call Perplexica weather endpoint
            response = await self.client.post(f"{self.base_url}/weather", json=coords)
            response.raise_for_status()
            weather_data = response.json()

            # Format weather data as search result
            weather_result = {
                "title": f"Pogoda w {location}",
                "url": f"weather://{location}",
                "snippet": f"Temperatura: {weather_data.get('temperature', 'N/A')}°C, "
                f"Warunki: {weather_data.get('condition', 'N/A')}, "
                f"Wilgotność: {weather_data.get('humidity', 'N/A')}%, "
                f"Wiatr: {weather_data.get('windSpeed', 'N/A')} km/h",
                "source": "perplexica_weather",
                "confidence": 0.95,
                "weather_data": weather_data,
                "location": location,
            }

            return [weather_result]

        except Exception as e:
            logger.error(f"Perplexica weather query error: {e}")
            return []

    def _extract_location_from_query(self, query: str) -> str:
        """Extract location from weather query with enhanced coverage"""
        query_lower = query.lower()

        # Enhanced Polish cities and towns with variations
        locations = {
            # Major cities
            "warszawa": "Warszawa",
            "warsaw": "Warszawa",
            "kraków": "Kraków",
            "krakow": "Kraków",
            "cracow": "Kraków",
            "wrocław": "Wrocław",
            "wroclaw": "Wrocław",
            "poznań": "Poznań",
            "poznan": "Poznań",
            "gdańsk": "Gdańsk",
            "gdansk": "Gdańsk",
            "danzig": "Gdańsk",
            "szczecin": "Szczecin",
            "łódź": "Łódź",
            "lodz": "Łódź",
            "lublin": "Lublin",
            "katowice": "Katowice",
            "białystok": "Białystok",
            "bialystok": "Białystok",
            "gdynia": "Gdynia",
            "częstochowa": "Częstochowa",
            "czestochowa": "Częstochowa",
            # Warsaw area suburbs and towns
            "ząbki": "Ząbki",
            "zabki": "Ząbki",
            "marki": "Marki",
            "kobyłka": "Kobyłka",
            "kobylka": "Kobyłka",
            "wołomin": "Wołomin",
            "wolomin": "Wołomin",
            "zielonka": "Zielonka",
            "sulejówek": "Sulejówek",
            "sulejowek": "Sulejówek",
            "legionowo": "Legionowo",
            "jabłonna": "Jabłonna",
            "jablonna": "Jabłonna",
            "piaseczno": "Piaseczno",
            "konstancin": "Konstancin-Jeziorna",
            "wilanów": "Wilanów",
            "wilanow": "Wilanów",
            "mokotów": "Mokotów",
            "mokotow": "Mokotów",
            "praga": "Praga",
            "wola": "Wola",
            "ochota": "Ochota",
            "żoliborz": "Żoliborz",
            "zoliborz": "Żoliborz",
            # Other major areas
            "sopot": "Sopot",
            "zakopane": "Zakopane",
            "kielce": "Kielce",
            "olsztyn": "Olsztyn",
            "toruń": "Toruń",
            "torun": "Toruń",
            "bydgoszcz": "Bydgoszcz",
            "radom": "Radom",
            "rzeszów": "Rzeszów",
            "rzeszow": "Rzeszów",
        }

        # Try exact matches first
        for location_key, location_name in locations.items():
            if location_key in query_lower:
                return location_name

        # Try partial matches for compound words
        words = query_lower.split()
        for word in words:
            if word in locations:
                return locations[word]

        # Check for "w" (in) preposition patterns like "w Ząbkach"
        import re

        location_pattern = r"\b(?:w|we|na)\s+([a-ząćęłńóśźż]+(?:ach|ech|ie|y)?)\b"
        match = re.search(location_pattern, query_lower)
        if match:
            location_word = match.group(1)
            # Try to match base form
            base_forms = {
                "ząbkach": "Ząbki",
                "zabkach": "Ząbki",
                "markach": "Marki",
                "kobyłce": "Kobyłka",
                "wołominie": "Wołomin",
                "wolominie": "Wołomin",
                "warszawie": "Warszawa",
                "krakowie": "Kraków",
                "poznaniu": "Poznań",
                "wrocławiu": "Wrocław",
            }
            if location_word in base_forms:
                return base_forms[location_word]

        return "Warszawa"  # Default location

    def _validate_result(self, result: dict) -> bool:
        """Validate search result quality"""
        required_fields = ["title", "url", "snippet"]
        return all(field in result for field in required_fields)

    async def close(self):
        """Close the client"""
        await self.client.aclose()


class SerpAPISearchProvider(SearchProvider):
    """Provider for SerpAPI Google Search with advanced features"""

    def __init__(self):
        super().__init__()
        self.api_key = settings.SERPAPI_API_KEY
        self.base_url = "https://serpapi.com/search"
        self.client = httpx.AsyncClient(
            timeout=30.0, headers={"User-Agent": settings.USER_AGENT}
        )
        self.engine = settings.SERPAPI_ENGINE
        self.location = settings.SERPAPI_LOCATION
        self.language = settings.SERPAPI_LANGUAGE
        self.enabled = settings.SERPAPI_ENABLED and bool(self.api_key)

    async def search(self, query: str, max_results: int = 5) -> list[dict[str, Any]]:
        """Search using SerpAPI Google Search"""
        if not self.enabled:
            logger.warning("SerpAPI is disabled or API key not configured")
            return []

        try:
            params = {
                "api_key": self.api_key,
                "engine": self.engine,
                "q": query,
                "location": self.location,
                "hl": self.language,
                "gl": "pl",  # Google country
                "num": max_results,
                "safe": "active",  # Safe search
                "device": "desktop"
            }

            response = await self.client.get(self.base_url, params=params)
            response.raise_for_status()
            data = response.json()

            results = []
            
            # Handle different result types
            organic_results = data.get("organic_results", [])
            answer_box = data.get("answer_box", {})
            knowledge_graph = data.get("knowledge_graph", {})
            
            # Add answer box if available (high quality results)
            if answer_box:
                results.append({
                    "title": answer_box.get("title", "Odpowiedź Google"),
                    "url": answer_box.get("link", ""),
                    "snippet": answer_box.get("answer", answer_box.get("snippet", "")),
                    "source": "serpapi_answer_box",
                    "confidence": 0.95,
                    "knowledge_verified": True,
                    "result_type": "answer_box"
                })

            # Add knowledge graph if available
            if knowledge_graph:
                results.append({
                    "title": knowledge_graph.get("title", "Wiedza Google"),
                    "url": knowledge_graph.get("website", ""),
                    "snippet": knowledge_graph.get("description", ""),
                    "source": "serpapi_knowledge_graph",
                    "confidence": 0.90,
                    "knowledge_verified": True,
                    "result_type": "knowledge_graph",
                    "kgmid": knowledge_graph.get("kgmid", "")
                })

            # Add organic results
            for result in organic_results[:max_results]:
                # Enhanced quality scoring
                confidence = self._calculate_confidence(result)
                
                results.append({
                    "title": result.get("title", ""),
                    "url": result.get("link", ""),
                    "snippet": result.get("snippet", ""),
                    "source": "serpapi_organic",
                    "confidence": confidence,
                    "knowledge_verified": confidence > 0.7,
                    "result_type": "organic",
                    "position": result.get("position", 0),
                    "displayed_link": result.get("displayed_link", "")
                })

            # Handle featured snippets
            featured_snippet = data.get("featured_snippet", {})
            if featured_snippet:
                results.insert(0, {
                    "title": featured_snippet.get("title", "Fragment wyróżniony"),
                    "url": featured_snippet.get("link", ""),
                    "snippet": featured_snippet.get("snippet", ""),
                    "source": "serpapi_featured_snippet",
                    "confidence": 0.92,
                    "knowledge_verified": True,
                    "result_type": "featured_snippet"
                })

            # Handle related questions (People Also Ask)
            related_questions = data.get("related_questions", [])
            if related_questions and len(results) < max_results:
                for q in related_questions[:max_results - len(results)]:
                    results.append({
                        "title": f"Pytanie: {q.get('question', '')}",
                        "url": q.get("link", ""),
                        "snippet": q.get("snippet", ""),
                        "source": "serpapi_related_question",
                        "confidence": 0.75,
                        "knowledge_verified": False,
                        "result_type": "related_question"
                    })

            return results[:max_results]

        except Exception as e:
            logger.error(f"SerpAPI search error: {e}")
            return []

    def _calculate_confidence(self, result: dict) -> float:
        """Calculate confidence score based on result quality indicators"""
        confidence = 0.5  # Base confidence
        
        # Higher confidence for well-known domains
        url = result.get("link", "").lower()
        trusted_domains = [
            "wikipedia.org", "gov.pl", "edu.pl", ".edu", "pap.pl",
            "reuters.com", "bbc.com", "cnn.com", "bloomberg.com",
            "stackoverflow.com", "github.com", "microsoft.com",
            "google.com", "mozilla.org", "w3.org"
        ]
        
        if any(domain in url for domain in trusted_domains):
            confidence += 0.3
            
        # Higher confidence for HTTPS
        if url.startswith("https://"):
            confidence += 0.1
            
        # Higher confidence for longer, more detailed snippets
        snippet_length = len(result.get("snippet", ""))
        if snippet_length > 100:
            confidence += 0.1
        elif snippet_length > 50:
            confidence += 0.05
            
        # Higher confidence for top positions
        position = result.get("position", 10)
        if position <= 3:
            confidence += 0.1
        elif position <= 5:
            confidence += 0.05
            
        return min(confidence, 1.0)

    async def search_images(self, query: str, max_results: int = 5) -> list[dict[str, Any]]:
        """Search for images using SerpAPI"""
        if not self.enabled:
            return []

        try:
            params = {
                "api_key": self.api_key,
                "engine": "google_images",
                "q": query,
                "location": self.location,
                "hl": self.language,
                "gl": "pl",
                "num": max_results,
                "safe": "active"
            }

            response = await self.client.get(self.base_url, params=params)
            response.raise_for_status()
            data = response.json()

            results = []
            images_results = data.get("images_results", [])
            
            for img in images_results[:max_results]:
                results.append({
                    "title": img.get("title", ""),
                    "url": img.get("link", ""),
                    "thumbnail": img.get("thumbnail", ""),
                    "original": img.get("original", ""),
                    "source": "serpapi_image",
                    "confidence": 0.8,
                    "result_type": "image",
                    "width": img.get("original_width", 0),
                    "height": img.get("original_height", 0)
                })

            return results

        except Exception as e:
            logger.error(f"SerpAPI image search error: {e}")
            return []

    async def search_news(self, query: str, max_results: int = 5) -> list[dict[str, Any]]:
        """Search for news using SerpAPI"""
        if not self.enabled:
            return []

        try:
            params = {
                "api_key": self.api_key,
                "engine": "google_news",
                "q": query,
                "location": self.location,
                "hl": self.language,
                "gl": "pl",
                "num": max_results
            }

            response = await self.client.get(self.base_url, params=params)
            response.raise_for_status()
            data = response.json()

            results = []
            news_results = data.get("news_results", [])
            
            for news in news_results[:max_results]:
                results.append({
                    "title": news.get("title", ""),
                    "url": news.get("link", ""),
                    "snippet": news.get("snippet", ""),
                    "source": "serpapi_news",
                    "confidence": 0.85,
                    "knowledge_verified": True,
                    "result_type": "news",
                    "date": news.get("date", ""),
                    "source_name": news.get("source", "")
                })

            return results

        except Exception as e:
            logger.error(f"SerpAPI news search error: {e}")
            return []

    def is_enabled(self) -> bool:
        """Check if SerpAPI is properly configured"""
        return self.enabled

    async def close(self):
        """Close the client"""
        await self.client.aclose()
