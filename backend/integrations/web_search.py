import asyncio
from datetime import datetime
import hashlib
import json
import logging
import os
from pathlib import Path
import time
from typing import Any

import httpx
from pydantic import BaseModel

from settings import settings

logger = logging.getLogger(__name__)

# Constants
DEFAULT_CACHE_DIR = os.path.join(
    os.path.dirname(__file__), "..", "..", "data", "search_cache"
)
DEFAULT_TTL = 600  # 10 minutes in seconds
MAX_RETRIES = 3
RETRY_DELAY = 1.0  # Start with 1 second delay, doubles each retry
REQUEST_TIMEOUT = 10.0  # 10 seconds

# Wikipedia API constants
WIKIPEDIA_API_BASE = "https://pl.wikipedia.org/api/rest_v1"
WIKIPEDIA_SEARCH_BASE = "https://pl.wikipedia.org/w/api.php"


# Sources configuration
class SourceConfig(BaseModel):
    """Configuration for a search source"""

    name: str
    enabled: bool = True
    api_key_env_var: str
    base_url: str
    api_key: str | None = None
    quota_per_day: int | None = None
    quota_per_minute: int | None = None
    priority: int = 1  # Lower number = higher priority
    whitelist: list[str] = []
    blacklist: list[str] = []


class SearchResult(BaseModel):
    """Search result model"""

    title: str
    url: str
    snippet: str
    source: str
    date: str | None = None
    source_confidence: float = 1.0
    knowledge_verified: bool = False


class SearchResponse(BaseModel):
    """API response for search"""

    query: str
    results: list[SearchResult]
    timestamp: str
    source: str
    cached: bool = False
    knowledge_verification_score: float = 0.0


class WikipediaSearchClient:
    """Client for Wikipedia API searches with knowledge verification"""

    def __init__(self, base_url: str = WIKIPEDIA_API_BASE):
        self.base_url = base_url
        self.client = httpx.AsyncClient(
            timeout=REQUEST_TIMEOUT, headers={"User-Agent": settings.USER_AGENT}
        )

    async def search(self, query: str, max_results: int = 5) -> list[SearchResult]:
        """Search Wikipedia for articles"""
        try:
            # Search for articles
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
                    # Get full article content for knowledge verification
                    article_content = await self._get_article_content(item["title"])

                    result = SearchResult(
                        title=item["title"],
                        url=f"https://pl.wikipedia.org/wiki/{item['title'].replace(' ', '_')}",
                        snippet=item.get("snippet", ""),
                        source="wikipedia",
                        date=item.get("timestamp"),
                        knowledge_verified=bool(article_content),
                        source_confidence=0.9 if article_content else 0.5,
                    )
                    results.append(result)

            return results

        except Exception as e:
            logger.error(f"Wikipedia search error: {e}")
            return []

    async def _get_article_content(self, title: str) -> str | None:
        """Get full article content for knowledge verification"""
        try:
            # Get article summary
            summary_url = f"{self.base_url}/page/summary/{title}"
            response = await self.client.get(summary_url)
            response.raise_for_status()
            data = response.json()

            return data.get("extract", "")
        except Exception as e:
            logger.debug(f"Could not get article content for {title}: {e}")
            return None

    async def close(self) -> None:
        """Close the client"""
        await self.client.aclose()


class WebSearchClient:
    """Client for making API calls to search engines with caching and source verification"""

    def __init__(
        self,
        cache_dir: str = DEFAULT_CACHE_DIR,
        ttl: int = DEFAULT_TTL,
        sources_config: list[dict[str, Any]] | None = None,
    ) -> None:
        self.cache_dir = cache_dir
        self.ttl = ttl
        self.sources: list[SourceConfig] = []
        self.source_usage: dict[str, dict[str, Any]] = {}
        self.client = httpx.AsyncClient(
            timeout=REQUEST_TIMEOUT, headers={"User-Agent": settings.USER_AGENT}
        )
        self.wikipedia_client = WikipediaSearchClient()

        # Create cache directory if it doesn't exist
        os.makedirs(cache_dir, exist_ok=True)

        # Initialize sources
        self._init_sources(sources_config)

    def _init_sources(self, sources_config: list[dict[str, Any]] | None = None) -> None:
        """Initialize search sources from config"""
        default_sources = [
            {
                "name": "wikipedia",
                "enabled": True,
                "api_key_env_var": "",
                "base_url": WIKIPEDIA_API_BASE,
                "priority": 1,
                "whitelist": ["wikipedia.org"],
            },
        ]

        config_to_use = sources_config or default_sources

        for src_config in config_to_use:
            source = SourceConfig(**src_config)

            # Get API key from environment (optional for Wikipedia)
            if source.name != "wikipedia" and hasattr(settings, source.api_key_env_var):
                source.api_key = getattr(settings, source.api_key_env_var)
            elif source.name != "wikipedia":
                source.api_key = os.environ.get(source.api_key_env_var)

            # Enable Wikipedia even without API key
            if source.name == "wikipedia" or source.api_key:
                self.sources.append(source)
                # Initialize usage tracking
                self.source_usage[source.name] = {
                    "daily_count": 0,
                    "minute_count": 0,
                    "last_minute": datetime.now().minute,
                    "last_reset_day": datetime.now().day,
                    "errors": 0,
                    "last_error": None,
                }
            else:
                logger.warning(
                    f"No API key found for {source.name} (env var: {source.api_key_env_var})"
                )

        # Sort sources by priority
        self.sources.sort(key=lambda x: x.priority)

        logger.info(f"Initialized {len(self.sources)} search sources")

    def _get_cache_path(self, query: str) -> str:
        """Get cache file path for a query"""
        # Create a hash of the query to use as filename
        query_hash = hashlib.md5(query.encode()).hexdigest()
        return os.path.join(self.cache_dir, f"{query_hash}.json")

    def _is_cache_valid(self, cache_path: str) -> bool:
        """Check if cache file exists and is within TTL"""
        if not Path(cache_path).exists():
            return False

        # Check file modification time
        mod_time = os.path.getmtime(cache_path)
        age = time.time() - mod_time

        return age < self.ttl

    async def _load_from_cache(self, query: str) -> SearchResponse | None:
        """Load search results from cache if available"""
        cache_path = self._get_cache_path(query)

        if self._is_cache_valid(cache_path):
            try:
                with open(cache_path) as f:
                    data = json.load(f)

                response = SearchResponse(**data)
                response.cached = True

                logger.info(f"Loaded results for '{query}' from cache")
                return response
            except Exception as e:
                logger.error(f"Error loading from cache: {e}")

        return None

    async def _save_to_cache(self, response: SearchResponse) -> None:
        """Save search results to cache"""
        cache_path = self._get_cache_path(response.query)

        try:
            # Check if directory is writable
            if not os.access(self.cache_dir, os.W_OK):
                logger.warning(
                    f"Cache directory {self.cache_dir} is not writable, skipping cache save"
                )
                return

            with open(cache_path, "w") as f:
                json.dump(response.dict(), f)

            logger.debug(f"Saved results for '{response.query}' to cache")
        except PermissionError as e:
            logger.warning(f"Permission denied when saving to cache: {e}")
            # Continue without caching
        except OSError as e:
            logger.warning(f"OS error when saving to cache: {e}")
            # Continue without caching
        except Exception as e:
            logger.error(f"Error saving to cache: {e}")
            # Continue without caching

    async def _make_request(
        self, source: SourceConfig, query: str, retries: int = MAX_RETRIES
    ) -> dict[str, Any] | None:
        """Make a request to a search API with retries"""
        # Track usage
        source_stats = self.source_usage[source.name]

        # Reset daily count if day changed
        current_day = datetime.now().day
        if source_stats["last_reset_day"] != current_day:
            source_stats["daily_count"] = 0
            source_stats["last_reset_day"] = current_day

        # Reset minute count if minute changed
        current_minute = datetime.now().minute
        if source_stats["last_minute"] != current_minute:
            source_stats["minute_count"] = 0
            source_stats["last_minute"] = current_minute

        # Check quotas
        if source.quota_per_day and source_stats["daily_count"] >= source.quota_per_day:
            logger.warning(f"Daily quota exceeded for {source.name}")
            return None

        if (
            source.quota_per_minute
            and source_stats["minute_count"] >= source.quota_per_minute
        ):
            logger.warning(f"Minute quota exceeded for {source.name}")
            return None

        # Make request with retries
        for attempt in range(retries):
            try:
                if source.name == "wikipedia":
                    # Use Wikipedia client
                    results = await self.wikipedia_client.search(query, max_results=5)
                    return {
                        "results": [result.dict() for result in results],
                        "source": "wikipedia",
                        "query": query,
                    }
                if source.name == "newsapi":
                    return await self._make_newsapi_request(source, query)
                if source.name == "bing":
                    return await self._make_bing_request(source, query)
                logger.warning(f"Unknown source: {source.name}")
                return None

            except Exception as e:
                source_stats["errors"] += 1
                source_stats["last_error"] = str(e)
                logger.error(
                    f"Request failed for {source.name} (attempt {attempt + 1}): {e}"
                )

                if attempt < retries - 1:
                    await asyncio.sleep(RETRY_DELAY * (2**attempt))
                else:
                    return None

        return None

    async def _make_newsapi_request(
        self, source: SourceConfig, query: str
    ) -> dict[str, Any] | None:
        """Make request to NewsAPI"""
        url = f"{source.base_url}/everything"
        params = {
            "q": query,
            "apiKey": source.api_key,
            "language": "pl",
            "sortBy": "relevancy",
            "pageSize": 5,
        }

        response = await self.client.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        return self._parse_newsapi_response(data, query)

    async def _make_bing_request(
        self, source: SourceConfig, query: str
    ) -> dict[str, Any] | None:
        """Make request to Bing Search API"""
        url = source.base_url
        headers = {"Ocp-Apim-Subscription-Key": source.api_key}
        params = {"q": query, "count": 5, "mkt": "pl-PL", "safesearch": "moderate"}

        response = await self.client.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()

        return self._parse_bing_response(data, query)

    def _parse_newsapi_response(
        self, data: dict[str, Any], query: str
    ) -> dict[str, Any]:
        """Parse NewsAPI response"""
        results = []
        for article in data.get("articles", []):
            # Verify source credibility
            source_url = article.get("url", "")
            is_verified = self._verify_source(source_url, "newsapi")

            result = SearchResult(
                title=article.get("title", ""),
                url=source_url,
                snippet=article.get("description", ""),
                source="newsapi",
                date=article.get("publishedAt"),
                knowledge_verified=is_verified,
                source_confidence=0.8 if is_verified else 0.4,
            )
            results.append(result)

        return {
            "results": [result.dict() for result in results],
            "source": "newsapi",
            "query": query,
        }

    def _parse_bing_response(self, data: dict[str, Any], query: str) -> dict[str, Any]:
        """Parse Bing Search API response"""
        results = []
        for item in data.get("webPages", {}).get("value", []):
            # Verify source credibility
            source_url = item.get("url", "")
            is_verified = self._verify_source(source_url, "bing")

            result = SearchResult(
                title=item.get("name", ""),
                url=source_url,
                snippet=item.get("snippet", ""),
                source="bing",
                knowledge_verified=is_verified,
                source_confidence=0.7 if is_verified else 0.3,
            )
            results.append(result)

        return {
            "results": [result.dict() for result in results],
            "source": "bing",
            "query": query,
        }

    def _verify_source(self, source: str, provider: str) -> bool:
        """Verify source credibility based on provider and domain"""
        if not source:
            return False

        # Check against whitelist/blacklist for the provider
        source_config = next((s for s in self.sources if s.name == provider), None)
        if not source_config:
            return False

        # Extract domain from URL
        try:
            from urllib.parse import urlparse

            domain = urlparse(source).netloc.lower()
        except Exception:
            return False

        # Check blacklist
        if any(blacklisted in domain for blacklisted in source_config.blacklist):
            return False

        # Check whitelist (if empty, accept all)
        if source_config.whitelist:
            return any(whitelisted in domain for whitelisted in source_config.whitelist)

        return True

    async def search(self, query: str, force_refresh: bool = False) -> SearchResponse:
        """Perform a search across all available sources"""
        # Check cache first
        if not force_refresh:
            cached_response = await self._load_from_cache(query)
            if cached_response:
                return cached_response

        all_results = []
        knowledge_scores = []

        # Search across all sources
        for source in self.sources:
            if not source.enabled:
                continue

            try:
                result = await self._make_request(source, query)
                if result:
                    # Update usage counters
                    source_stats = self.source_usage[source.name]
                    source_stats["daily_count"] += 1
                    source_stats["minute_count"] += 1

                    # Add results
                    for item in result["results"]:
                        search_result = SearchResult(**item)
                        all_results.append(search_result)
                        if search_result.knowledge_verified:
                            knowledge_scores.append(search_result.source_confidence)

            except Exception as e:
                logger.error(f"Error searching {source.name}: {e}")

        # Calculate knowledge verification score
        knowledge_verification_score = (
            sum(knowledge_scores) / len(knowledge_scores) if knowledge_scores else 0.0
        )

        # Create response
        response = SearchResponse(
            query=query,
            results=all_results[:10],  # Limit to top 10 results
            timestamp=datetime.now().isoformat(),
            source="multi",
            knowledge_verification_score=knowledge_verification_score,
        )

        # Cache the response
        await self._save_to_cache(response)

        return response

    async def close(self) -> None:
        """Close all clients"""
        await self.client.aclose()
        await self.wikipedia_client.close()


class WebSearch:
    """Main interface for web search functionality"""

    def __init__(self, client: WebSearchClient | None = None) -> None:
        self.client = client or WebSearchClient()

    async def search(self, query: str, max_results: int = 5) -> list[dict[str, Any]]:
        """Perform a web search and return simplified results"""
        response = await self.client.search(query)
        return [
            {
                "title": r.title,
                "url": r.url,
                "snippet": r.snippet,
                "source": r.source,
                "knowledge_verified": r.knowledge_verified,
                "confidence": r.source_confidence,
            }
            for r in response.results[:max_results]
        ]

    async def search_with_verification(
        self, query: str, max_results: int = 5
    ) -> dict[str, Any]:
        """Perform a search with knowledge verification details"""
        response = await self.client.search(query)
        return {
            "query": query,
            "results": [
                {
                    "title": r.title,
                    "url": r.url,
                    "snippet": r.snippet,
                    "source": r.source,
                    "knowledge_verified": r.knowledge_verified,
                    "confidence": r.source_confidence,
                }
                for r in response.results[:max_results]
            ],
            "knowledge_verification_score": response.knowledge_verification_score,
            "total_results": len(response.results),
            "cached": response.cached,
        }

    async def close(self) -> None:
        """Close underlying client"""
        await self.client.close()


# Global instance
web_search = WebSearch()
