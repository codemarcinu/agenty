"""
Caching system for product categorization results
Provides fast lookup for previously categorized products
"""

from datetime import datetime, timedelta
import hashlib
import logging
from typing import Any

from core.exceptions import FoodSaveError

logger = logging.getLogger(__name__)


class CategorizationCache:
    """Cache system for product categorization results"""

    def __init__(self, max_size: int = 10000, ttl_hours: int = 24):
        """
        Initialize categorization cache

        Args:
            max_size: Maximum number of cached items
            ttl_hours: Time to live in hours
        """
        self.max_size = max_size
        self.ttl_hours = ttl_hours
        self.cache: dict[str, dict[str, Any]] = {}
        self.access_times: dict[str, datetime] = {}

    def _generate_cache_key(self, product_name: str, store_name: str = "") -> str:
        """Generate cache key for product categorization"""
        # Normalize product name for consistent hashing
        normalized_name = product_name.lower().strip()
        normalized_store = store_name.lower().strip()

        # Create hash from normalized values
        content = f"{normalized_name}:{normalized_store}"
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def get(self, product_name: str, store_name: str = "") -> dict[str, Any] | None:
        """
        Get categorization result from cache

        Args:
            product_name: Name of the product
            store_name: Name of the store (optional)

        Returns:
            Cached categorization result or None if not found/expired
        """
        cache_key = self._generate_cache_key(product_name, store_name)

        if cache_key not in self.cache:
            return None

        # Check if cache entry is expired
        if cache_key in self.access_times:
            age = datetime.now() - self.access_times[cache_key]
            if age > timedelta(hours=self.ttl_hours):
                # Remove expired entry
                del self.cache[cache_key]
                del self.access_times[cache_key]
                return None

        # Update access time
        self.access_times[cache_key] = datetime.now()

        logger.debug(f"Cache hit for product: {product_name}")
        return self.cache[cache_key]

    def set(
        self,
        product_name: str,
        categorization_result: dict[str, Any],
        store_name: str = "",
    ) -> None:
        """
        Store categorization result in cache

        Args:
            product_name: Name of the product
            categorization_result: Result from categorization
            store_name: Name of the store (optional)
        """
        cache_key = self._generate_cache_key(product_name, store_name)

        # Add metadata to cache entry
        cache_entry = {
            "product_name": product_name,
            "store_name": store_name,
            "categorization": categorization_result,
            "cached_at": datetime.now().isoformat(),
            "cache_key": cache_key,
        }

        # Check if cache is full
        if len(self.cache) >= self.max_size:
            self._evict_oldest()

        # Store in cache
        self.cache[cache_key] = cache_entry
        self.access_times[cache_key] = datetime.now()

        logger.debug(f"Cached categorization for product: {product_name}")

    def _evict_oldest(self) -> None:
        """Evict oldest cache entries when cache is full"""
        if not self.access_times:
            return

        # Find oldest entry
        oldest_key = min(self.access_times.keys(), key=lambda k: self.access_times[k])

        # Remove oldest entry
        del self.cache[oldest_key]
        del self.access_times[oldest_key]

        logger.debug(f"Evicted oldest cache entry: {oldest_key}")

    def clear(self) -> None:
        """Clear all cache entries"""
        self.cache.clear()
        self.access_times.clear()
        logger.info("Categorization cache cleared")

    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics"""
        now = datetime.now()
        expired_count = 0

        for cache_key in list(self.access_times.keys()):
            age = now - self.access_times[cache_key]
            if age > timedelta(hours=self.ttl_hours):
                expired_count += 1
                del self.cache[cache_key]
                del self.access_times[cache_key]

        return {
            "total_entries": len(self.cache),
            "max_size": self.max_size,
            "ttl_hours": self.ttl_hours,
            "expired_entries_removed": expired_count,
            "utilization_percent": (len(self.cache) / self.max_size) * 100,
        }

    def export_cache(self) -> dict[str, Any]:
        """Export cache data for backup/analysis"""
        return {
            "cache": self.cache,
            "access_times": {k: v.isoformat() for k, v in self.access_times.items()},
            "stats": self.get_stats(),
        }

    def import_cache(self, cache_data: dict[str, Any]) -> None:
        """Import cache data from backup"""
        try:
            self.cache = cache_data.get("cache", {})
            self.access_times = {
                k: datetime.fromisoformat(v)
                for k, v in cache_data.get("access_times", {}).items()
            }
            logger.info(f"Imported {len(self.cache)} cache entries")
        except Exception as e:
            logger.error(f"Failed to import cache: {e}")
            raise FoodSaveError(f"Cache import failed: {e}")


# Global cache instance
categorization_cache = CategorizationCache()


class BatchCategorizationCache:
    """Specialized cache for batch categorization operations"""

    def __init__(self, base_cache: CategorizationCache):
        self.base_cache = base_cache
        self.batch_results: dict[str, Any] = {}

    async def categorize_batch_with_cache(
        self, products: list[dict[str, Any]], store_name: str = ""
    ) -> list[dict[str, Any]]:
        """
        Categorize a batch of products with caching

        Args:
            products: List of products to categorize
            store_name: Store name for context

        Returns:
            List of categorized products
        """
        results = []
        cache_hits = 0
        cache_misses = 0

        for product in products:
            product_name = product.get("name", "")

            # Try to get from cache first
            cached_result = self.base_cache.get(product_name, store_name)

            if cached_result:
                # Use cached result
                product.update(cached_result["categorization"])
                cache_hits += 1
                logger.debug(f"Cache hit for product: {product_name}")
            else:
                # Mark for processing
                cache_misses += 1
                logger.debug(f"Cache miss for product: {product_name}")

            results.append(product)

        logger.info(
            f"Batch categorization cache stats: {cache_hits} hits, {cache_misses} misses"
        )

        return results

    def store_batch_results(
        self, products: list[dict[str, Any]], store_name: str = ""
    ) -> None:
        """
        Store batch categorization results in cache

        Args:
            products: List of categorized products
            store_name: Store name for context
        """
        for product in products:
            product_name = product.get("name", "")

            # Extract categorization data
            categorization_data = {
                "category": product.get("category"),
                "category_en": product.get("category_en"),
                "gpt_category": product.get("gpt_category"),
                "category_confidence": product.get("category_confidence"),
                "category_method": product.get("category_method"),
            }

            # Store in cache
            self.base_cache.set(product_name, categorization_data, store_name)

        logger.info(f"Stored {len(products)} categorization results in cache")


# Global batch cache instance
batch_categorization_cache = BatchCategorizationCache(categorization_cache)
