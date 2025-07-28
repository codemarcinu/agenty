"""
Performance tests for memory management and caching systems

These tests measure the performance improvements from the optimization changes.
"""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import gc
import os
import time

import psutil
import pytest

from backend.core.cache_manager import MultiLayerCacheManager, OptimizedQueryCache
from backend.core.memory import MemoryManager


class PerformanceMetrics:
    """Helper class to collect performance metrics"""

    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.start_memory = None
        self.end_memory = None
        self.process = psutil.Process(os.getpid())

    def start(self):
        """Start performance measurement"""
        gc.collect()  # Clean up before measurement
        self.start_time = time.time()
        self.start_memory = self.process.memory_info().rss / 1024 / 1024  # MB

    def stop(self):
        """Stop performance measurement"""
        self.end_time = time.time()
        self.end_memory = self.process.memory_info().rss / 1024 / 1024  # MB

    @property
    def duration(self) -> float:
        """Get execution duration in seconds"""
        return (
            self.end_time - self.start_time if self.end_time and self.start_time else 0
        )

    @property
    def memory_usage(self) -> float:
        """Get memory usage change in MB"""
        return (
            self.end_memory - self.start_memory
            if self.end_memory and self.start_memory
            else 0
        )

    @property
    def memory_usage_mb(self) -> float:
        """Get current memory usage in MB"""
        return self.end_memory if self.end_memory else 0


class TestMemoryManagerPerformance:
    """Performance tests for optimized memory manager"""

    @pytest.mark.performance
    def test_context_creation_performance(self):
        """Test performance of context creation and retrieval"""
        memory_manager = MemoryManager(max_contexts=10000, cleanup_interval=3600)
        metrics = PerformanceMetrics()

        num_contexts = 1000

        metrics.start()

        # Create many contexts
        for i in range(num_contexts):
            memory_manager.get_or_create_context(f"session_{i}")
            # Add some data to make it realistic
            memory_manager.update_context(
                f"session_{i}",
                {
                    "user_id": f"user_{i}",
                    "conversation_data": f"data_{i}" * 10,  # Some text data
                    "timestamp": datetime.now().isoformat(),
                },
            )

        metrics.stop()

        # Performance assertions
        assert (
            metrics.duration < 2.0
        ), f"Context creation took too long: {metrics.duration:.2f}s"
        assert (
            metrics.memory_usage < 100
        ), f"Memory usage too high: {metrics.memory_usage:.2f}MB"

        # Verify all contexts were created
        assert len(memory_manager._contexts) == num_contexts


    @pytest.mark.performance
    def test_context_access_performance(self):
        """Test performance of context access patterns"""
        memory_manager = MemoryManager(max_contexts=1000, cleanup_interval=3600)

        # Pre-create contexts
        num_contexts = 500
        for i in range(num_contexts):
            memory_manager.get_or_create_context(f"session_{i}")

        metrics = PerformanceMetrics()
        metrics.start()

        # Simulate realistic access patterns
        num_accesses = 10000
        for i in range(num_accesses):
            session_id = f"session_{i % num_contexts}"
            memory_manager.get_or_create_context(session_id)

            # Simulate context usage
            if i % 10 == 0:  # Update context occasionally
                memory_manager.update_context(
                    session_id,
                    {"access_count": i, "last_access": datetime.now().isoformat()},
                )

        metrics.stop()

        # Performance assertions
        assert (
            metrics.duration < 1.0
        ), f"Context access took too long: {metrics.duration:.2f}s"

        # Calculate access rate
        access_rate = num_accesses / metrics.duration
        assert (
            access_rate > 5000
        ), f"Access rate too low: {access_rate:.0f} accesses/sec"


    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_memory_cleanup_performance(self):
        """Test performance of memory cleanup operations"""
        memory_manager = MemoryManager(max_contexts=1000, cleanup_interval=1)

        # Create contexts with varying access times
        num_contexts = 2000
        for i in range(num_contexts):
            memory_manager.get_or_create_context(f"session_{i}")
            # Simulate some contexts being older
            if i < num_contexts // 2:
                # Make half the contexts appear older
                memory_manager._access_times[f"session_{i}"] = (
                    datetime.now() - asyncio.get_event_loop().time() + 7200
                )  # 2 hours ago

        metrics = PerformanceMetrics()
        metrics.start()

        # Force cleanup
        await memory_manager.force_cleanup()

        metrics.stop()

        # Performance assertions
        assert metrics.duration < 0.5, f"Cleanup took too long: {metrics.duration:.2f}s"

        # Verify cleanup worked
        remaining_contexts = len(memory_manager._contexts)
        num_contexts - remaining_contexts


    @pytest.mark.performance
    def test_concurrent_access_performance(self):
        """Test performance under concurrent access"""
        memory_manager = MemoryManager(max_contexts=1000, cleanup_interval=3600)

        def worker_task(worker_id: int, num_operations: int):
            """Worker function for concurrent testing"""
            for i in range(num_operations):
                session_id = f"worker_{worker_id}_session_{i % 100}"
                memory_manager.get_or_create_context(session_id)

                if i % 10 == 0:
                    memory_manager.update_context(
                        session_id,
                        {
                            "worker_id": worker_id,
                            "operation": i,
                            "timestamp": datetime.now().isoformat(),
                        },
                    )

        metrics = PerformanceMetrics()
        metrics.start()

        # Run concurrent workers
        num_workers = 10
        operations_per_worker = 1000

        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            futures = [
                executor.submit(worker_task, worker_id, operations_per_worker)
                for worker_id in range(num_workers)
            ]

            # Wait for all workers to complete
            for future in futures:
                future.result()

        metrics.stop()

        # Performance assertions
        total_operations = num_workers * operations_per_worker
        operations_per_sec = total_operations / metrics.duration

        assert (
            metrics.duration < 5.0
        ), f"Concurrent operations took too long: {metrics.duration:.2f}s"
        assert (
            operations_per_sec > 1000
        ), f"Operation rate too low: {operations_per_sec:.0f} ops/sec"



class TestCachePerformance:
    """Performance tests for optimized caching system"""

    @pytest.mark.performance
    def test_query_cache_performance(self):
        """Test performance of optimized query cache"""
        cache = OptimizedQueryCache("performance_test", ttl=3600, max_size=1000)
        metrics = PerformanceMetrics()

        # Prepare test data
        test_queries = [f"query_{i}" for i in range(1000)]
        test_data = {
            query: {"result": f"result_for_{query}", "data": list(range(100))}
            for query in test_queries
        }

        metrics.start()

        # Test cache set performance
        for query, data in test_data.items():
            cache.set(query, data)

        # Test cache get performance (should all hit)
        hit_count = 0
        for query in test_queries:
            result = cache.get(query)
            if result is not None:
                hit_count += 1

        metrics.stop()

        # Performance assertions
        assert (
            metrics.duration < 1.0
        ), f"Cache operations took too long: {metrics.duration:.2f}s"
        assert hit_count == len(
            test_queries
        ), f"Cache hit rate not 100%: {hit_count}/{len(test_queries)}"

        # Check cache statistics
        stats = cache.get_stats()
        assert stats["hit_rate"] > 0.5, f"Hit rate too low: {stats['hit_rate']:.2f}"


    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_multi_layer_cache_performance(self):
        """Test performance of multi-layer cache system"""
        cache_manager = MultiLayerCacheManager()
        metrics = PerformanceMetrics()

        # Prepare test data
        num_items = 1000
        test_data = {
            f"key_{i}": {
                "id": i,
                "data": f"value_{i}" * 10,
                "metadata": {"created": datetime.now().isoformat()},
            }
            for i in range(num_items)
        }

        metrics.start()

        # Test L1 cache performance
        for key, data in test_data.items():
            await cache_manager.set(key, data, cache_type="performance_test")

        # Test retrieval performance (L1 cache hits)
        l1_hits = 0
        for key in test_data:
            result = await cache_manager.get(key, cache_type="performance_test")
            if result is not None:
                l1_hits += 1

        metrics.stop()

        # Performance assertions
        assert (
            metrics.duration < 2.0
        ), f"Multi-layer cache operations took too long: {metrics.duration:.2f}s"
        assert (
            l1_hits == num_items
        ), f"L1 cache hit rate not 100%: {l1_hits}/{num_items}"

        # Check statistics
        stats = await cache_manager.get_stats()
        stats["performance"]["overall_hit_rate"]


    @pytest.mark.performance
    def test_cache_eviction_performance(self):
        """Test performance of cache eviction mechanisms"""
        cache = OptimizedQueryCache("eviction_test", ttl=3600, max_size=100)
        metrics = PerformanceMetrics()

        metrics.start()

        # Fill cache beyond capacity to trigger evictions
        num_items = 500  # 5x the cache capacity
        for i in range(num_items):
            cache.set(f"key_{i}", {"data": f"value_{i}", "index": i})

        # Access some items to test LRU behavior
        for i in range(0, 50, 2):  # Access every other item in first 50
            cache.get(f"key_{i}")

        metrics.stop()

        # Performance assertions
        assert (
            metrics.duration < 1.0
        ), f"Cache eviction took too long: {metrics.duration:.2f}s"

        # Check cache statistics
        stats = cache.get_stats()
        assert stats["evictions"] > 0, "No evictions occurred"
        assert (
            stats["size"] <= cache.max_size
        ), f"Cache size exceeded max: {stats['size']} > {cache.max_size}"

        stats["evictions"] / stats["total_requests"]


    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_cache_concurrent_performance(self):
        """Test cache performance under concurrent load"""
        cache_manager = MultiLayerCacheManager()

        async def cache_worker(worker_id: int, num_operations: int):
            """Async worker for cache testing"""
            for i in range(num_operations):
                key = f"worker_{worker_id}_key_{i % 100}"
                data = {"worker": worker_id, "operation": i, "data": "x" * 100}

                # Mix of set and get operations
                if i % 3 == 0:
                    await cache_manager.set(key, data, cache_type="concurrent_test")
                else:
                    await cache_manager.get(key, cache_type="concurrent_test")

        metrics = PerformanceMetrics()
        metrics.start()

        # Run concurrent cache operations
        num_workers = 20
        operations_per_worker = 500

        workers = [
            cache_worker(worker_id, operations_per_worker)
            for worker_id in range(num_workers)
        ]

        await asyncio.gather(*workers)

        metrics.stop()

        # Performance assertions
        total_operations = num_workers * operations_per_worker
        operations_per_sec = total_operations / metrics.duration

        assert (
            metrics.duration < 10.0
        ), f"Concurrent cache operations took too long: {metrics.duration:.2f}s"
        assert (
            operations_per_sec > 500
        ), f"Cache operation rate too low: {operations_per_sec:.0f} ops/sec"

        # Check cache statistics
        await cache_manager.get_stats()



class TestIntegratedPerformance:
    """Performance tests for integrated memory and cache systems"""

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_realistic_workload_performance(self):
        """Test performance under realistic workload simulation"""
        memory_manager = MemoryManager(max_contexts=1000, cleanup_interval=3600)
        cache_manager = MultiLayerCacheManager()

        async def simulate_user_session(user_id: int, num_interactions: int):
            """Simulate a user session with memory and cache usage"""
            session_id = f"user_{user_id}_session"

            for i in range(num_interactions):
                # Memory operations
                memory_manager.get_or_create_context(session_id)
                memory_manager.update_context(
                    session_id,
                    {
                        "interaction": i,
                        "timestamp": datetime.now().isoformat(),
                        "user_input": f"user input {i}",
                    },
                )

                # Cache operations
                cache_key = f"user_{user_id}_query_{i % 10}"  # Simulate query reuse
                cached_result = await cache_manager.get(cache_key, cache_type="session")

                if cached_result is None:
                    # Simulate generating result
                    result = {
                        "query_result": f"result for query {i % 10}",
                        "generated_at": datetime.now().isoformat(),
                    }
                    await cache_manager.set(cache_key, result, cache_type="session")

        metrics = PerformanceMetrics()
        metrics.start()

        # Simulate multiple concurrent user sessions
        num_users = 50
        interactions_per_user = 20

        sessions = [
            simulate_user_session(user_id, interactions_per_user)
            for user_id in range(num_users)
        ]

        await asyncio.gather(*sessions)

        metrics.stop()

        # Performance assertions
        total_interactions = num_users * interactions_per_user
        interactions_per_sec = total_interactions / metrics.duration

        assert (
            metrics.duration < 15.0
        ), f"Realistic workload took too long: {metrics.duration:.2f}s"
        assert (
            interactions_per_sec > 50
        ), f"Interaction rate too low: {interactions_per_sec:.0f} interactions/sec"

        # Check system statistics
        memory_manager.get_memory_stats()
        await cache_manager.get_stats()


    @pytest.mark.performance
    def test_memory_leak_prevention(self):
        """Test that memory optimizations prevent memory leaks"""
        memory_manager = MemoryManager(max_contexts=100, cleanup_interval=1)

        initial_metrics = PerformanceMetrics()
        initial_metrics.start()
        initial_metrics.stop()

        # Create and destroy many contexts
        num_cycles = 10
        contexts_per_cycle = 200

        for cycle in range(num_cycles):
            # Create contexts
            for i in range(contexts_per_cycle):
                session_id = f"cycle_{cycle}_session_{i}"
                memory_manager.get_or_create_context(session_id)
                memory_manager.update_context(
                    session_id,
                    {"cycle": cycle, "data": "x" * 1000},  # Some data to consume memory
                )

            # Force garbage collection and cleanup
            gc.collect()

            # Clear some contexts to simulate normal cleanup
            for i in range(contexts_per_cycle // 2):
                session_id = f"cycle_{cycle}_session_{i}"
                memory_manager.clear_context(session_id)

        final_metrics = PerformanceMetrics()
        final_metrics.start()
        final_metrics.stop()

        # Memory growth should be bounded
        memory_growth = final_metrics.memory_usage_mb - initial_metrics.memory_usage_mb

        # Allow some memory growth but not excessive
        assert (
            memory_growth < 50
        ), f"Excessive memory growth detected: {memory_growth:.2f}MB"

        # Verify memory manager statistics
        memory_manager.get_memory_stats()

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_cache_memory_efficiency(self):
        """Test memory efficiency of cache system"""
        cache_manager = MultiLayerCacheManager()

        initial_metrics = PerformanceMetrics()
        initial_metrics.start()
        initial_metrics.stop()

        # Fill caches with data
        num_items = 5000
        for i in range(num_items):
            data = {
                "id": i,
                "content": "x" * 100,  # 100 bytes per item
                "metadata": {"created": datetime.now().isoformat()},
            }
            await cache_manager.set(f"item_{i}", data, cache_type="memory_test")

        # Force cache cleanup
        for cache in cache_manager.l1_caches.values():
            cache.cleanup_expired()

        final_metrics = PerformanceMetrics()
        final_metrics.start()
        final_metrics.stop()

        # Calculate memory efficiency
        memory_growth = final_metrics.memory_usage_mb - initial_metrics.memory_usage_mb

        # Get cache statistics
        stats = await cache_manager.get_stats()
        total_cached_items = sum(
            cache_stats["size"] for cache_stats in stats["l1_caches"].values()
        )

        memory_per_item = (
            memory_growth / total_cached_items if total_cached_items > 0 else 0
        )


        # Memory usage should be reasonable
        assert (
            memory_per_item < 0.01
        ), f"Memory per item too high: {memory_per_item:.3f}MB"


@pytest.mark.benchmark
class TestBenchmarks:
    """Benchmark tests for performance comparisons"""

    def test_memory_manager_benchmark(self, benchmark):
        """Benchmark memory manager operations"""
        memory_manager = MemoryManager(max_contexts=1000, cleanup_interval=3600)

        def benchmark_operations():
            for i in range(100):
                session_id = f"benchmark_session_{i}"
                memory_manager.get_or_create_context(session_id)
                memory_manager.update_context(
                    session_id,
                    {
                        "benchmark_data": f"data_{i}",
                        "timestamp": datetime.now().isoformat(),
                    },
                )

        benchmark(benchmark_operations)

    def test_cache_benchmark(self, benchmark):
        """Benchmark cache operations"""
        cache = OptimizedQueryCache("benchmark", ttl=3600, max_size=1000)

        def benchmark_cache_operations():
            # Fill cache
            for i in range(100):
                cache.set(f"key_{i}", {"data": f"value_{i}", "index": i})

            # Access cache
            for i in range(100):
                cache.get(f"key_{i}")

        benchmark(benchmark_cache_operations)


if __name__ == "__main__":
    # Run performance tests
    pytest.main([__file__, "-v", "-m", "performance", "--tb=short"])
