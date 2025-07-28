"""
Search cache implementation for caching search results.
Provides in-memory caching with TTL support for search queries.
"""

from collections import OrderedDict
import logging
import time
from typing import Any

logger = logging.getLogger(__name__)


class SearchCache:
    """In-memory cache for search results with TTL support"""

    def __init__(self, max_size: int = 1000, default_ttl: int = 600):
        """
        Initialize search cache

        Args:
            max_size: Maximum number of cached items
            default_ttl: Default time-to-live in seconds (10 minutes)
        """
        self._cache: OrderedDict = OrderedDict()
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._stats = {"hits": 0, "misses": 0, "sets": 0, "evictions": 0}

    def _get_cache_key(self, query: str, provider: str) -> str:
        """Generate cache key from query and provider"""
        return f"{provider}:{query.lower().strip()}"

    def _is_expired(self, cache_entry: dict[str, Any]) -> bool:
        """Check if cache entry is expired"""
        return time.time() > cache_entry.get("expires_at", 0)

    def get(self, query: str, provider: str) -> list[dict[str, Any]] | None:
        """
        Get cached results for query and provider

        Args:
            query: Search query
            provider: Search provider name

        Returns:
            Cached results or None if not found/expired
        """
        cache_key = self._get_cache_key(query, provider)

        if cache_key in self._cache:
            entry = self._cache[cache_key]

            if self._is_expired(entry):
                # Remove expired entry
                del self._cache[cache_key]
                self._stats["misses"] += 1
                return None

            # Move to end (LRU)
            self._cache.move_to_end(cache_key)
            self._stats["hits"] += 1
            return entry["results"]

        self._stats["misses"] += 1
        return None

    def set(
        self,
        query: str,
        provider: str,
        results: list[dict[str, Any]],
        ttl: int | None = None,
    ) -> None:
        """
        Cache search results

        Args:
            query: Search query
            provider: Search provider name
            results: Search results to cache
            ttl: Time-to-live in seconds (uses default if None)
        """
        cache_key = self._get_cache_key(query, provider)
        ttl = ttl or self.default_ttl

        # Remove if exists
        if cache_key in self._cache:
            del self._cache[cache_key]

        # Check if we need to evict oldest entry
        if len(self._cache) >= self.max_size:
            oldest_key = next(iter(self._cache))
            del self._cache[oldest_key]
            self._stats["evictions"] += 1

        # Add new entry
        self._cache[cache_key] = {
            "results": results,
            "expires_at": time.time() + ttl,
            "created_at": time.time(),
            "provider": provider,
            "query": query,
        }

        self._stats["sets"] += 1

    def clear(self) -> None:
        """Clear all cached entries"""
        self._cache.clear()
        logger.info("Search cache cleared")

    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics"""
        total_requests = self._stats["hits"] + self._stats["misses"]
        hit_rate = (
            (self._stats["hits"] / total_requests * 100) if total_requests > 0 else 0
        )

        return {
            "size": len(self._cache),
            "max_size": self.max_size,
            "hits": self._stats["hits"],
            "misses": self._stats["misses"],
            "sets": self._stats["sets"],
            "evictions": self._stats["evictions"],
            "hit_rate": round(hit_rate, 2),
            "total_requests": total_requests,
        }

    def cleanup_expired(self) -> int:
        """
        Remove expired entries from cache

        Returns:
            Number of entries removed
        """
        expired_keys = [
            key for key, entry in self._cache.items() if self._is_expired(entry)
        ]

        for key in expired_keys:
            del self._cache[key]

        if expired_keys:
            logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")

        return len(expired_keys)

    def get_cache_info(self) -> dict[str, Any]:
        """Get detailed cache information"""
        self.cleanup_expired()

        return {
            "stats": self.get_stats(),
            "entries": [
                {
                    "key": key,
                    "provider": entry["provider"],
                    "query": entry["query"],
                    "created_at": entry["created_at"],
                    "expires_at": entry["expires_at"],
                    "results_count": len(entry["results"]),
                }
                for key, entry in self._cache.items()
            ],
        }


# Global search cache instance
search_cache = SearchCache()
