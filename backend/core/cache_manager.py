"""
Cache Manager for FoodSave AI using Redis

This module provides caching functionality for expensive operations like RAG searches,
internet queries, and embeddings with advanced optimization features.
"""

import asyncio
from collections import OrderedDict
from collections.abc import Callable
from functools import wraps
import hashlib
import json
import logging
import pickle
import threading
import time
from typing import Any, TypeVar

import numpy as np

try:
    import redis.asyncio as redis
    from redis.asyncio.client import Redis as RedisClient

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None  # type: ignore
    RedisClient = None  # type: ignore

from pydantic import BaseModel

from settings import settings

logger = logging.getLogger(__name__)

# Type for cached function return value
T = TypeVar("T")

# Cache configuration
DEFAULT_CACHE_TTL = 3600  # 1 hour in seconds
RAG_CACHE_TTL = 1800  # 30 minutes
INTERNET_CACHE_TTL = 600  # 10 minutes
EMBEDDING_CACHE_TTL = 86400  # 24 hours for embeddings


class EmbeddingCache:
    """Specialized cache for embeddings with optimized storage and retrieval"""

    def __init__(self, max_size: int = 1000, ttl: int = EMBEDDING_CACHE_TTL):
        self.max_size = max_size
        self.ttl = ttl
        self.cache: OrderedDict[str, tuple[np.ndarray, float]] = OrderedDict()
        self.hits = 0
        self.misses = 0
        self._lock = threading.RLock()

    def _generate_embedding_key(self, text: str, model_name: str = "default") -> str:
        """Generate cache key for embeddings"""
        content = f"{text}:{model_name}"
        return hashlib.md5(content.encode()).hexdigest()

    def get(self, text: str, model_name: str = "default") -> np.ndarray | None:
        """Get cached embedding"""
        with self._lock:
            key = self._generate_embedding_key(text, model_name)

            if key in self.cache:
                embedding, timestamp = self.cache[key]
                if time.time() - timestamp <= self.ttl:
                    # Move to end (most recently used)
                    self.cache.move_to_end(key)
                    self.hits += 1
                    return embedding
                else:
                    # Expired
                    del self.cache[key]

            self.misses += 1
            return None

    def set(
        self, text: str, embedding: np.ndarray, model_name: str = "default"
    ) -> None:
        """Cache embedding with LRU eviction"""
        with self._lock:
            key = self._generate_embedding_key(text, model_name)

            # LRU eviction if cache is full
            if len(self.cache) >= self.max_size and key not in self.cache:
                lru_key = next(iter(self.cache))
                del self.cache[lru_key]

            self.cache[key] = (embedding, time.time())
            self.cache.move_to_end(key)

    def get_batch(
        self, texts: list[str], model_name: str = "default"
    ) -> tuple[list[np.ndarray], list[int]]:
        """Get multiple embeddings at once, return cached and missing indices"""
        with self._lock:
            cached_embeddings = []
            missing_indices = []

            for i, text in enumerate(texts):
                embedding = self.get(text, model_name)
                if embedding is not None:
                    cached_embeddings.append(embedding)
                else:
                    missing_indices.append(i)

            return cached_embeddings, missing_indices

    def set_batch(
        self,
        texts: list[str],
        embeddings: list[np.ndarray],
        model_name: str = "default",
    ) -> None:
        """Cache multiple embeddings at once"""
        with self._lock:
            for text, embedding in zip(texts, embeddings, strict=False):
                self.set(text, embedding, model_name)

    def get_stats(self) -> dict[str, Any]:
        """Get embedding cache statistics"""
        with self._lock:
            total = self.hits + self.misses
            hit_rate = self.hits / total if total > 0 else 0

            return {
                "size": len(self.cache),
                "max_size": self.max_size,
                "ttl": self.ttl,
                "hits": self.hits,
                "misses": self.misses,
                "hit_rate": hit_rate,
                "memory_efficiency": (
                    len(self.cache) / self.max_size if self.max_size > 0 else 0
                ),
            }


class OptimizedQueryCache:
    """Advanced in-memory cache with LRU eviction and statistics"""

    def __init__(
        self, name: str, ttl: int = DEFAULT_CACHE_TTL, max_size: int = 100
    ) -> None:
        """
        Initialize a new optimized query cache

        Args:
            name: Name of the cache for logging
            ttl: Time-to-live in seconds for cache entries
            max_size: Maximum number of items to store in cache
        """
        self.name = name
        self.ttl = ttl
        self.max_size = max_size
        # LRU cache with timestamp tracking
        self.cache: OrderedDict[str, tuple[Any, float, int]] = (
            OrderedDict()
        )  # {key: (value, timestamp, access_count)}
        self.hits = 0
        self.misses = 0
        self.evictions = 0
        self.total_requests = 0
        self._lock = threading.RLock()
        logger.info(f"Initialized {name} cache with TTL={ttl}s, max_size={max_size}")

    def _generate_key(self, query: str, **kwargs) -> str:
        """Generate a cache key from the query and additional parameters"""
        # Create a string representation of kwargs sorted by key
        kwargs_str = "&".join(
            f"{k}={v}" for k, v in sorted(kwargs.items()) if v is not None
        )
        key_str = f"{query}|{kwargs_str}" if kwargs_str else query
        return hashlib.md5(key_str.encode()).hexdigest()

    def get(self, query: str, **kwargs) -> Any | None:
        """
        Get a value from the cache with LRU tracking

        Args:
            query: The query string
            **kwargs: Additional parameters that affect the result

        Returns:
            The cached value or None if not found or expired
        """
        with self._lock:
            self.total_requests += 1
            key = self._generate_key(query, **kwargs)

            if key in self.cache:
                value, timestamp, access_count = self.cache[key]
                current_time = time.time()

                if current_time - timestamp <= self.ttl:
                    # Update access count and move to end (most recently used)
                    self.cache[key] = (value, timestamp, access_count + 1)
                    self.cache.move_to_end(key)
                    self.hits += 1
                    logger.debug(
                        f"{self.name} cache HIT: {query[:30]}... (access_count: {access_count + 1})"
                    )
                    return value
                else:
                    # Expired - remove from cache
                    del self.cache[key]
                    logger.debug(f"{self.name} cache EXPIRED: {query[:30]}...")

            self.misses += 1
            logger.debug(f"{self.name} cache MISS: {query[:30]}...")
            return None

    def set(self, query: str, value: Any, **kwargs) -> None:
        """
        Store a value in the cache with LRU eviction

        Args:
            query: The query string
            value: The value to cache
            **kwargs: Additional parameters that affect the result
        """
        with self._lock:
            key = self._generate_key(query, **kwargs)
            current_time = time.time()

            # If cache is full, remove LRU entry
            if len(self.cache) >= self.max_size and key not in self.cache:
                lru_key = next(iter(self.cache))  # First item is LRU
                del self.cache[lru_key]
                self.evictions += 1
                logger.debug(f"{self.name} cache EVICTED LRU entry")

            # Add/update entry (move to end if exists)
            self.cache[key] = (value, current_time, 1)
            self.cache.move_to_end(key)
            logger.debug(f"{self.name} cache SET: {query[:30]}...")

    def clear(self) -> None:
        """Clear the cache and reset statistics"""
        with self._lock:
            self.cache.clear()
            # Reset statistics but keep historical data for analysis
            logger.info(f"{self.name} cache cleared - kept statistics for analysis")

    def cleanup_expired(self) -> int:
        """Remove expired entries and return count of removed items"""
        with self._lock:
            current_time = time.time()
            expired_keys = []

            for key, (value, timestamp, access_count) in self.cache.items():
                if current_time - timestamp > self.ttl:
                    expired_keys.append(key)

            for key in expired_keys:
                del self.cache[key]

            if expired_keys:
                logger.debug(
                    f"{self.name} cache cleaned up {len(expired_keys)} expired entries"
                )

            return len(expired_keys)

    def get_top_accessed(self, limit: int = 10) -> list[tuple[str, int]]:
        """Get most frequently accessed cache entries"""
        with self._lock:
            items = [
                (key, access_count) for key, (_, _, access_count) in self.cache.items()
            ]
            return sorted(items, key=lambda x: x[1], reverse=True)[:limit]

    def get_stats(self) -> dict[str, Any]:
        """Get comprehensive cache statistics"""
        with self._lock:
            total = self.hits + self.misses
            hit_rate = self.hits / total if total > 0 else 0
            eviction_rate = (
                self.evictions / self.total_requests if self.total_requests > 0 else 0
            )

            # Calculate average access count
            avg_access_count = 0
            if self.cache:
                total_access = sum(
                    access_count for _, _, access_count in self.cache.values()
                )
                avg_access_count = total_access / len(self.cache)

            return {
                "name": self.name,
                "size": len(self.cache),
                "max_size": self.max_size,
                "ttl": self.ttl,
                "hits": self.hits,
                "misses": self.misses,
                "evictions": self.evictions,
                "total_requests": self.total_requests,
                "hit_rate": hit_rate,
                "eviction_rate": eviction_rate,
                "avg_access_count": avg_access_count,
                "memory_efficiency": (
                    len(self.cache) / self.max_size if self.max_size > 0 else 0
                ),
            }


class MultiLayerCacheManager:
    """
    Multi-layer cache manager with Redis and in-memory caching.
    Optimized for embeddings, RAG queries, and general caching.
    """

    def __init__(self) -> None:
        """Initialize the multi-layer cache manager"""
        self.redis_client: RedisClient | None = None
        self.connected = False
        self.default_ttl = 3600  # 1 hour default

        # Initialize specialized caches
        self.embedding_cache = EmbeddingCache(max_size=1000, ttl=EMBEDDING_CACHE_TTL)
        self.rag_cache = OptimizedQueryCache("RAG", ttl=RAG_CACHE_TTL, max_size=500)
        self.internet_cache = OptimizedQueryCache(
            "Internet", ttl=INTERNET_CACHE_TTL, max_size=200
        )
        self.general_cache = OptimizedQueryCache(
            "General", ttl=DEFAULT_CACHE_TTL, max_size=300
        )

        # L1 Cache - In-memory with different strategies per cache type
        self.l1_caches: dict[str, OptimizedQueryCache] = {
            "rag": self.rag_cache,
            "internet": self.internet_cache,
            "general": self.general_cache,
            "semantic": OptimizedQueryCache(
                "L1-Semantic", ttl=7200, max_size=100
            ),  # 2 hours for semantic
        }

        # Statistics tracking
        self.stats = {
            "l1_hits": 0,
            "l1_misses": 0,
            "l2_hits": 0,
            "l2_misses": 0,
            "l2_promotions": 0,  # Items promoted from L2 to L1
            "total_requests": 0,
        }

        # Performance metrics
        self.performance_metrics = {
            "total_operations": 0,
            "redis_operations": 0,
            "memory_operations": 0,
            "embedding_operations": 0,
            "batch_operations": 0,
        }

        # Cleanup task - initialize lazily
        self._cleanup_task: asyncio.Task | None = None
        self._cleanup_started = False

    async def connect(self) -> bool:
        """Connect to Redis if available"""
        if not REDIS_AVAILABLE:
            logger.warning("Redis not available, using in-memory cache only")
            return False

        try:
            self.redis_client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                password=settings.REDIS_PASSWORD,
                decode_responses=False,  # Keep binary for pickle
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30,
                max_connections=20,
                retry_on_error=[redis.ConnectionError, redis.TimeoutError],
            )

            # Test connection
            await self.redis_client.ping()
            self.connected = True
            logger.info("Successfully connected to Redis")
            return True

        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self.connected = False
            return False

    async def disconnect(self) -> None:
        """Disconnect from Redis"""
        if self.redis_client:
            await self.redis_client.close()
            self.connected = False
            logger.info("Disconnected from Redis")

    async def get_embedding(
        self, text: str, model_name: str = "default"
    ) -> np.ndarray | None:
        """Get cached embedding with optimized retrieval"""
        self.performance_metrics["embedding_operations"] += 1

        # Try memory cache first
        embedding = self.embedding_cache.get(text, model_name)
        if embedding is not None:
            self.performance_metrics["memory_operations"] += 1
            return embedding

        # Try Redis if available
        if self.connected and self.redis_client:
            try:
                key = f"embedding:{model_name}:{hashlib.md5(text.encode()).hexdigest()}"
                data = await self.redis_client.get(key)
                if data:
                    embedding = pickle.loads(data)
                    # Cache in memory for faster access
                    self.embedding_cache.set(text, embedding, model_name)
                    self.performance_metrics["redis_operations"] += 1
                    return embedding
            except Exception as e:
                logger.warning(f"Redis embedding retrieval failed: {e}")

        return None

    async def set_embedding(
        self, text: str, embedding: np.ndarray, model_name: str = "default"
    ) -> None:
        """Cache embedding in both memory and Redis"""
        self.performance_metrics["embedding_operations"] += 1

        # Cache in memory
        self.embedding_cache.set(text, embedding, model_name)
        self.performance_metrics["memory_operations"] += 1

        # Cache in Redis if available
        if self.connected and self.redis_client:
            try:
                key = f"embedding:{model_name}:{hashlib.md5(text.encode()).hexdigest()}"
                data = pickle.dumps(embedding)
                await self.redis_client.setex(key, EMBEDDING_CACHE_TTL, data)
                self.performance_metrics["redis_operations"] += 1
            except Exception as e:
                logger.warning(f"Redis embedding storage failed: {e}")

    async def get_embeddings_batch(
        self, texts: list[str], model_name: str = "default"
    ) -> tuple[list[np.ndarray], list[int]]:
        """Get multiple embeddings efficiently"""
        self.performance_metrics["batch_operations"] += 1

        # Get cached embeddings from memory
        cached_embeddings, missing_indices = self.embedding_cache.get_batch(
            texts, model_name
        )

        # Get missing embeddings from Redis if available
        if missing_indices and self.connected and self.redis_client:
            try:
                # Batch Redis operations
                pipeline = self.redis_client.pipeline()
                for idx in missing_indices:
                    text = texts[idx]
                    key = f"embedding:{model_name}:{hashlib.md5(text.encode()).hexdigest()}"
                    pipeline.get(key)

                results = await pipeline.execute()

                # Process results
                for i, (idx, result) in enumerate(
                    zip(missing_indices, results, strict=False)
                ):
                    if result:
                        embedding = pickle.loads(result)
                        cached_embeddings.append(embedding)
                        # Cache in memory
                        self.embedding_cache.set(texts[idx], embedding, model_name)
                    else:
                        # Still missing
                        missing_indices[i] = idx

                self.performance_metrics["redis_operations"] += 1

            except Exception as e:
                logger.warning(f"Redis batch embedding retrieval failed: {e}")

        return cached_embeddings, missing_indices

    async def set_embeddings_batch(
        self,
        texts: list[str],
        embeddings: list[np.ndarray],
        model_name: str = "default",
    ) -> None:
        """Cache multiple embeddings efficiently"""
        self.performance_metrics["batch_operations"] += 1

        # Cache in memory
        self.embedding_cache.set_batch(texts, embeddings, model_name)
        self.performance_metrics["memory_operations"] += 1

        # Cache in Redis if available
        if self.connected and self.redis_client:
            try:
                pipeline = self.redis_client.pipeline()
                for text, embedding in zip(texts, embeddings, strict=False):
                    key = f"embedding:{model_name}:{hashlib.md5(text.encode()).hexdigest()}"
                    data = pickle.dumps(embedding)
                    pipeline.setex(key, EMBEDDING_CACHE_TTL, data)

                await pipeline.execute()
                self.performance_metrics["redis_operations"] += 1

            except Exception as e:
                logger.warning(f"Redis batch embedding storage failed: {e}")

    async def set(
        self,
        key: str,
        value: Any,
        cache_type: str = "general",
        ttl: int | None = None,
        serialize: bool = True,
    ) -> bool:
        """Set value in multi-layer cache (L1 + L2)"""
        # Set in L1 cache
        l1_cache = self.get_l1_cache(cache_type)
        l1_cache.set(key, value)

        # Set in L2 cache (Redis)
        if not self.connected or not self.redis_client:
            logger.debug(f"L1 cache set for key: {key[:30]}... (Redis unavailable)")
            return True  # L1 cache still works

        try:
            if serialize:
                if isinstance(value, BaseModel):
                    data = value.model_dump_json().encode("utf-8")
                elif isinstance(value, dict | list):
                    data = json.dumps(value, ensure_ascii=False).encode("utf-8")
                else:
                    data = pickle.dumps(value)
            else:
                data = str(value).encode("utf-8")

            ttl = ttl or self.default_ttl
            await self.redis_client.set(key, data, ex=ttl)
            logger.debug(f"Multi-layer cache set: {key[:30]}... (TTL: {ttl}s)")
            return True

        except Exception as e:
            logger.error(f"Failed to set L2 cache for key {key}: {e}")
            return True  # L1 cache still works

    async def get(
        self,
        key: str,
        cache_type: str = "general",
        deserialize: bool = True,
        default: Any = None,
        expected_type: type | None = None,
    ) -> Any:
        """Get value from multi-layer cache (L1 -> L2)"""
        self.stats["total_requests"] += 1

        # Try L1 cache first
        l1_cache = self.get_l1_cache(cache_type)
        l1_result = l1_cache.get(key)

        if l1_result is not None:
            self.stats["l1_hits"] += 1
            logger.debug(f"L1 cache hit for key: {key[:30]}...")
            return l1_result

        self.stats["l1_misses"] += 1

        # Try L2 cache (Redis)
        if not self.connected or not self.redis_client:
            self.stats["l2_misses"] += 1
            return default

        try:
            data = await self.redis_client.get(key)
            if data is None:
                self.stats["l2_misses"] += 1
                return default

            # Deserialize data
            if deserialize:
                if expected_type and issubclass(expected_type, BaseModel):
                    result = expected_type.model_validate_json(data.decode("utf-8"))
                else:
                    try:
                        # Try JSON first
                        result = json.loads(data.decode("utf-8"))
                    except (json.JSONDecodeError, UnicodeDecodeError):
                        # Fallback to pickle
                        result = pickle.loads(data)
            else:
                result = data.decode("utf-8")

            # Promote to L1 cache
            l1_cache.set(key, result)
            self.stats["l2_hits"] += 1
            self.stats["l2_promotions"] += 1

            logger.debug(f"L2 cache hit and promoted to L1 for key: {key[:30]}...")
            return result

        except Exception as e:
            logger.error(f"Failed to get cache for key {key}: {e}")
            self.stats["l2_misses"] += 1
            return default

    async def delete(self, key: str) -> bool:
        """Delete key from cache"""
        if not self.connected or not self.redis_client:
            return False

        try:
            result = await self.redis_client.delete(key)
            logger.debug(f"Cache delete: {key}")
            return result > 0
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            return False

    async def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        if not self.connected or not self.redis_client:
            return False

        try:
            return await self.redis_client.exists(key) > 0
        except Exception as e:
            logger.error(f"Cache exists error for key {key}: {e}")
            return False

    async def expire(self, key: str, ttl: int) -> bool:
        """Set expiration for key"""
        if not self.connected or not self.redis_client:
            return False

        try:
            return await self.redis_client.expire(key, ttl)
        except Exception as e:
            logger.error(f"Cache expire error for key {key}: {e}")
            return False

    async def ttl(self, key: str) -> int:
        """Get TTL for key"""
        if not self.connected or not self.redis_client:
            return -1

        try:
            return await self.redis_client.ttl(key)
        except Exception as e:
            logger.error(f"Cache TTL error for key {key}: {e}")
            return -1

    async def clear_pattern(self, pattern: str) -> int:
        """Clear all keys matching pattern"""
        if not self.connected or not self.redis_client:
            return 0

        try:
            keys = await self.redis_client.keys(pattern)
            if keys:
                deleted = await self.redis_client.delete(*keys)
                logger.info(f"Cleared {deleted} keys matching pattern: {pattern}")
                return deleted
            return 0
        except Exception as e:
            logger.error(f"Cache clear pattern error for {pattern}: {e}")
            return 0

    async def get_stats(self) -> dict[str, Any]:
        """Get comprehensive multi-layer cache statistics"""
        l1_stats = {name: cache.get_stats() for name, cache in self.l1_caches.items()}

        # Calculate overall L1 statistics
        total_l1_hits = sum(cache.hits for cache in self.l1_caches.values())
        total_l1_misses = sum(cache.misses for cache in self.l1_caches.values())
        total_l1_requests = total_l1_hits + total_l1_misses
        l1_hit_rate = total_l1_hits / total_l1_requests if total_l1_requests > 0 else 0

        # Calculate overall hit rates
        total_requests = self.stats["total_requests"]
        overall_hit_rate = (
            (self.stats["l1_hits"] + self.stats["l2_hits"]) / total_requests
            if total_requests > 0
            else 0
        )

        stats = {
            "multi_layer": True,
            "l1_caches": l1_stats,
            "l1_summary": {
                "total_hits": total_l1_hits,
                "total_misses": total_l1_misses,
                "hit_rate": l1_hit_rate,
            },
            "l2_redis": {
                "connected": self.connected,
            },
            "overall_stats": self.stats,
            "performance": {
                "overall_hit_rate": overall_hit_rate,
                "l1_hit_rate": (
                    self.stats["l1_hits"] / total_requests if total_requests > 0 else 0
                ),
                "l2_hit_rate": (
                    self.stats["l2_hits"] / total_requests if total_requests > 0 else 0
                ),
                "cache_efficiency": (
                    self.stats["l2_promotions"] / self.stats["l2_hits"]
                    if self.stats["l2_hits"] > 0
                    else 0
                ),
            },
        }

        # Add Redis stats if available
        if self.connected and self.redis_client:
            try:
                info = await self.redis_client.info()
                stats["l2_redis"].update(
                    {
                        "used_memory": info.get("used_memory_human", "N/A"),
                        "connected_clients": info.get("connected_clients", 0),
                        "total_commands_processed": info.get(
                            "total_commands_processed", 0
                        ),
                        "keyspace_hits": info.get("keyspace_hits", 0),
                        "keyspace_misses": info.get("keyspace_misses", 0),
                    }
                )
            except Exception as e:
                stats["l2_redis"]["error"] = str(e)

        return stats

    async def health_check(self) -> bool:
        """Health check for cache"""
        if not self.connected or not self.redis_client:
            return False

        try:
            await self.redis_client.ping()
            return True
        except Exception as e:
            logger.error(f"Cache health check failed: {e}")
            return False

    async def store_semantic_context(self, session_id: str, semantic_hash: str) -> None:
        """Store semantic context (for compatibility)"""
        # Możesz tu dodać logikę jeśli chcesz cache'ować semantycznie
        logger.debug(
            f"Stub store_semantic_context called for session_id={session_id}, semantic_hash={semantic_hash}"
        )

    async def find_similar_context(self, session_id: str) -> str | None:
        """Find similar context by session ID (stub implementation)"""
        logger.debug(f"Stub find_similar_context called for session_id={session_id}")
        return None

    async def remove_semantic_context(self, session_id: str) -> None:
        """Remove semantic context (stub implementation)"""
        logger.debug(f"Stub remove_semantic_context called for session_id={session_id}")

    def get_hit_rate(self) -> float:
        """Get cache hit rate (stub implementation)"""
        return 0.0

    def get_l1_cache(self, cache_type: str) -> OptimizedQueryCache:
        """Get L1 cache for specified type"""
        return self.l1_caches.get(cache_type, self.l1_caches["general"])

    def get_performance_metrics(self) -> dict[str, Any]:
        """Get comprehensive performance metrics"""
        return {
            **self.performance_metrics,
            "embedding_cache_stats": self.embedding_cache.get_stats(),
            "rag_cache_stats": self.rag_cache.get_stats(),
            "internet_cache_stats": self.internet_cache.get_stats(),
            "general_cache_stats": self.general_cache.get_stats(),
            "redis_connected": self.connected,
            "total_cache_hit_rate": (
                (
                    self.embedding_cache.hits
                    + self.rag_cache.hits
                    + self.internet_cache.hits
                    + self.general_cache.hits
                )
                / max(self.performance_metrics["total_operations"], 1)
            ),
        }

    def _start_cleanup_task(self) -> None:
        """Start cleanup task only if event loop is running"""
        try:
            if not self._cleanup_started and asyncio.get_running_loop():
                self._cleanup_task = asyncio.create_task(self._periodic_cleanup())
                self._cleanup_started = True
        except RuntimeError:
            # No event loop running, skip cleanup task
            pass

    async def _periodic_cleanup(self) -> None:
        """Periodic cleanup of expired L1 cache entries"""
        while True:
            try:
                await asyncio.sleep(300)  # Cleanup every 5 minutes
                total_cleaned = 0
                for cache in self.l1_caches.values():
                    total_cleaned += cache.cleanup_expired()

                if total_cleaned > 0:
                    logger.info(
                        f"Periodic cleanup removed {total_cleaned} expired entries from L1 caches"
                    )

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in periodic cleanup: {e}")

    async def warm_cache(self, cache_type: str, warm_data: dict[str, Any]) -> None:
        """Warm cache with frequently accessed data"""
        l1_cache = self.get_l1_cache(cache_type)

        for key, value in warm_data.items():
            l1_cache.set(key, value)
            if self.connected and self.redis_client:
                await self.set(key, value, cache_type=cache_type)

        logger.info(f"Warmed {cache_type} cache with {len(warm_data)} entries")

    def __del__(self) -> None:
        """Cleanup when manager is destroyed"""
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()


# Legacy CacheManager for backward compatibility
class CacheManager(MultiLayerCacheManager):
    """Backward compatible cache manager"""


# Global cache manager instance
cache_manager = MultiLayerCacheManager()


# Legacy cache instances for backward compatibility
class QueryCache(OptimizedQueryCache):
    """Legacy QueryCache for backward compatibility"""


# Create global cache instances
rag_cache = QueryCache("RAG", ttl=RAG_CACHE_TTL)
internet_cache = QueryCache("Internet", ttl=INTERNET_CACHE_TTL)


def cached_async(cache_instance: OptimizedQueryCache) -> None:
    """
    Decorator for caching async function results

    Args:
        cache_instance: The cache instance to use

    Returns:
        Decorated function
    """

    def decorator(func) -> None:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> None:
            # Extract query from args or kwargs
            query = None
            if len(args) > 1:  # Assuming first arg is self, second is query
                query = args[1]
            elif "query" in kwargs:
                query = kwargs["query"]

            if not query:
                return await func(*args, **kwargs)

            # Try to get from cache
            cache_result = cache_instance.get(query, **kwargs)
            if cache_result is not None:
                return cache_result

            # Not in cache, call function
            result = await func(*args, **kwargs)

            # Store in cache
            cache_instance.set(query, result, **kwargs)
            return result

        return wrapper

    return decorator


# Cache decorator for functions
def cache_result(
    key_prefix: str,
    ttl: int = 3600,
    key_builder: Callable | None = None,
) -> None:
    """
    Decorator to cache the result of an async function in Redis.
    It automatically serializes/deserializes Pydantic models, dicts, lists, and other pickleable objects.
    """

    def decorator(func) -> None:
        async def async_wrapper(*args, **kwargs) -> None:
            # Build cache key
            if key_builder:
                cache_key = key_builder(*args, **kwargs)
            else:
                # Simple key based on function name and arguments
                key_parts = [key_prefix, func.__name__]
                key_parts.extend([str(arg) for arg in args])
                key_parts.extend([f"{k}:{v}" for k, v in sorted(kwargs.items())])
                cache_key = ":".join(key_parts)

            # Try to get from cache
            cached_result = await cache_manager.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit for {cache_key}")
                return cached_result

            # Execute function and cache result
            result = await func(*args, **kwargs)
            await cache_manager.set(cache_key, result, ttl)
            logger.debug(f"Cache miss for {cache_key}, stored result")

            return result

        def sync_wrapper(*args, **kwargs) -> None:
            # For sync functions, we can't use async cache directly
            # This would need to be handled differently
            return func(*args, **kwargs)

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator

import asyncio
import hashlib
import json
import logging
import time
from collections import OrderedDict
from datetime import datetime, timedelta
from functools import wraps
from typing import Any, Callable, Dict, Optional, TypeVar, Union

import redis.asyncio as redis
from pydantic import BaseModel

from settings import settings

logger = logging.getLogger(__name__)

T = TypeVar("T")

# Intelligent cache TTL based on query type
CACHE_TTL_MAP = {
    "rag": 3600,  # 1 hour for RAG results
    "internet": 1800,  # 30 minutes for internet search
    "weather": 900,  # 15 minutes for weather
    "simple": 7200,  # 2 hours for simple queries
    "complex": 1800,  # 30 minutes for complex queries
    "default": 3600,  # 1 hour default
}

class IntelligentCache:
    """Enhanced cache with intelligent TTL and query type detection"""
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 3600):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.cache: OrderedDict = OrderedDict()
        self.timestamps: Dict[str, float] = {}
        
    def _detect_query_type(self, query: str) -> str:
        """Detect query type for intelligent TTL"""
        query_lower = query.lower()
        
        # Weather queries
        if any(word in query_lower for word in ["pogoda", "temperatura", "deszcz", "słońce"]):
            return "weather"
        
        # Simple queries (greetings, basic questions)
        if any(word in query_lower for word in ["cześć", "witaj", "hello", "hi", "jak się masz"]):
            return "simple"
            
        # Complex queries (analysis, detailed questions)
        if len(query.split()) > 10 or any(word in query_lower for word in ["analiza", "porównaj", "wyjaśnij"]):
            return "complex"
            
        return "default"
    
    def _get_ttl_for_query(self, query: str) -> int:
        """Get TTL based on query type"""
        query_type = self._detect_query_type(query)
        return CACHE_TTL_MAP.get(query_type, self.default_ttl)
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache with TTL check"""
        if key in self.cache:
            timestamp = self.timestamps.get(key, 0)
            ttl = self._get_ttl_for_query(key)
            
            if time.time() - timestamp < ttl:
                # Move to end (LRU)
                self.cache.move_to_end(key)
                return self.cache[key]
            else:
                # Expired, remove
                del self.cache[key]
                del self.timestamps[key]
        
        return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache with intelligent TTL"""
        if ttl is None:
            ttl = self._get_ttl_for_query(key)
            
        # Remove if exists
        if key in self.cache:
            del self.cache[key]
            del self.timestamps[key]
        
        # Add new entry
        self.cache[key] = value
        self.timestamps[key] = time.time()
        
        # LRU eviction
        if len(self.cache) > self.max_size:
            oldest_key = next(iter(self.cache))
            del self.cache[oldest_key]
            del self.timestamps[oldest_key]
    
    def clear(self) -> None:
        """Clear all cache entries"""
        self.cache.clear()
        self.timestamps.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        current_time = time.time()
        expired_count = 0
        valid_count = 0
        
        for key, timestamp in self.timestamps.items():
            ttl = self._get_ttl_for_query(key)
            if current_time - timestamp < ttl:
                valid_count += 1
            else:
                expired_count += 1
        
        return {
            "total_entries": len(self.cache),
            "valid_entries": valid_count,
            "expired_entries": expired_count,
            "max_size": self.max_size,
            "memory_usage_mb": len(json.dumps(self.cache)) / 1024 / 1024
        }

# Global cache instances with compatibility
intelligent_cache = IntelligentCache(max_size=2000)
rag_cache = intelligent_cache  # Use intelligent cache for RAG
internet_cache = intelligent_cache  # Use intelligent cache for internet
weather_cache = IntelligentCache(max_size=200, default_ttl=900)

# Compatibility layer for existing cache decorators
class CacheCompatibility:
    """Compatibility layer for existing cache decorators"""
    
    def __init__(self, cache_instance: IntelligentCache):
        self.cache = cache_instance
    
    def get(self, key: str) -> Any:
        return self.cache.get(key)
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        self.cache.set(key, value, ttl)
    
    def clear(self) -> None:
        self.cache.clear()

# Create compatibility instances
rag_cache_compat = CacheCompatibility(rag_cache)
internet_cache_compat = CacheCompatibility(internet_cache)
weather_cache_compat = CacheCompatibility(weather_cache)

# Export for backward compatibility
rag_cache = rag_cache_compat
internet_cache = internet_cache_compat
weather_cache = weather_cache_compat

# Global cache manager instance for backward compatibility
_cache_manager_instance = None

def get_cache_manager() -> MultiLayerCacheManager:
    """Get global cache manager instance (singleton pattern)"""
    global _cache_manager_instance
    if _cache_manager_instance is None:
        _cache_manager_instance = MultiLayerCacheManager()
    return _cache_manager_instance
