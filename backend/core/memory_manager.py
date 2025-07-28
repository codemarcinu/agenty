"""
Enhanced memory management with automatic cleanup and monitoring.
"""

import asyncio
from collections.abc import Callable
from contextlib import contextmanager
from functools import wraps
import gc
import logging
import threading
import time
from typing import Any

import cv2
import psutil

logger = logging.getLogger(__name__)


class MemoryConfig:
    """Configuration for memory management"""

    # Memory limits (in MB)
    MAX_PROCESS_MEMORY = 1024  # 1GB max per process
    OCR_TASK_MEMORY_LIMIT = 256  # 256MB per OCR task
    WARNING_THRESHOLD = 512  # Warn at 512MB

    # Cleanup intervals
    CLEANUP_INTERVAL = 300  # 5 minutes
    FORCE_CLEANUP_INTERVAL = 900  # 15 minutes

    # Monitoring
    MEMORY_CHECK_INTERVAL = 60  # 1 minute
    LOG_MEMORY_USAGE = True


class MemoryStats:
    """Memory usage statistics"""

    def __init__(self):
        self.reset()

    def reset(self):
        self.peak_memory = 0
        self.current_memory = 0
        self.cleanup_count = 0
        self.warning_count = 0
        self.start_time = time.time()

    def update(self, memory_mb: float):
        self.current_memory = memory_mb
        if memory_mb > self.peak_memory:
            self.peak_memory = memory_mb

    def get_stats(self) -> dict[str, Any]:
        runtime = time.time() - self.start_time
        return {
            "current_memory_mb": self.current_memory,
            "peak_memory_mb": self.peak_memory,
            "cleanup_count": self.cleanup_count,
            "warning_count": self.warning_count,
            "runtime_seconds": runtime,
            "avg_memory_mb": self.current_memory,  # Could be enhanced with history
        }


class MemoryManager:
    """Enhanced memory manager with automatic cleanup and monitoring"""

    def __init__(self, config: MemoryConfig | None = None):
        self.config = config or MemoryConfig()
        self.stats = MemoryStats()
        self.process = psutil.Process()
        self.monitoring_task = None
        self.cleanup_callbacks: list[Callable] = []
        self.memory_history: list[tuple[float, float]] = []  # (timestamp, memory_mb)
        self._lock = threading.Lock()

    def start_monitoring(self):
        """Start memory monitoring task"""
        if self.monitoring_task is None:
            self.monitoring_task = asyncio.create_task(self._monitor_memory())
            logger.info("Memory monitoring started")

    def stop_monitoring(self):
        """Stop memory monitoring task"""
        if self.monitoring_task:
            self.monitoring_task.cancel()
            self.monitoring_task = None
            logger.info("Memory monitoring stopped")

    async def _monitor_memory(self):
        """Background memory monitoring task"""
        while True:
            try:
                await asyncio.sleep(self.config.MEMORY_CHECK_INTERVAL)

                memory_mb = self.get_memory_usage()
                self.stats.update(memory_mb)

                # Update history
                with self._lock:
                    current_time = time.time()
                    self.memory_history.append((current_time, memory_mb))

                    # Keep only last hour of history
                    cutoff_time = current_time - 3600
                    self.memory_history = [
                        (t, m) for t, m in self.memory_history if t > cutoff_time
                    ]

                # Check for warnings
                if memory_mb > self.config.WARNING_THRESHOLD:
                    self.stats.warning_count += 1
                    logger.warning(f"High memory usage: {memory_mb:.1f}MB")

                    # Trigger cleanup if memory is high
                    if memory_mb > self.config.MAX_PROCESS_MEMORY * 0.8:
                        await self.cleanup_memory()

                # Log memory usage periodically
                if self.config.LOG_MEMORY_USAGE:
                    logger.debug(f"Memory usage: {memory_mb:.1f}MB")

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Memory monitoring error: {e}")

    def get_memory_usage(self) -> float:
        """Get current memory usage in MB"""
        try:
            memory_info = self.process.memory_info()
            return memory_info.rss / 1024 / 1024  # Convert to MB
        except Exception as e:
            logger.error(f"Failed to get memory usage: {e}")
            return 0.0

    def check_memory_limit(self, operation: str = "unknown") -> bool:
        """Check if memory usage is within limits"""
        memory_mb = self.get_memory_usage()

        if memory_mb > self.config.MAX_PROCESS_MEMORY:
            logger.error(
                f"Memory limit exceeded during {operation}: "
                f"{memory_mb:.1f}MB > {self.config.MAX_PROCESS_MEMORY}MB"
            )
            return False

        return True

    async def cleanup_memory(self, force: bool = False):
        """Perform memory cleanup"""
        start_memory = self.get_memory_usage()

        logger.info(f"Starting memory cleanup (force={force})")

        try:
            # Call registered cleanup callbacks
            for callback in self.cleanup_callbacks:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback()
                    else:
                        callback()
                except Exception as e:
                    logger.error(f"Cleanup callback error: {e}")

            # Standard cleanup
            self._cleanup_opencv()
            self._cleanup_numpy()

            # Force garbage collection
            gc.collect()

            # Additional cleanup for high memory usage
            if force or start_memory > self.config.WARNING_THRESHOLD:
                # More aggressive cleanup
                for _ in range(3):
                    gc.collect()
                    await asyncio.sleep(0.1)

            end_memory = self.get_memory_usage()
            freed_mb = start_memory - end_memory

            self.stats.cleanup_count += 1

            logger.info(
                f"Memory cleanup completed: "
                f"{start_memory:.1f}MB -> {end_memory:.1f}MB "
                f"(freed: {freed_mb:.1f}MB)"
            )

        except Exception as e:
            logger.error(f"Memory cleanup error: {e}")

    def _cleanup_opencv(self):
        """Cleanup OpenCV resources"""
        try:
            cv2.destroyAllWindows()
            # Additional OpenCV cleanup if needed
        except Exception as e:
            logger.debug(f"OpenCV cleanup error: {e}")

    def _cleanup_numpy(self):
        """Cleanup NumPy resources"""
        try:
            # NumPy doesn't have specific cleanup, but we can clear caches
            pass
        except Exception as e:
            logger.debug(f"NumPy cleanup error: {e}")

    def add_cleanup_callback(self, callback: Callable):
        """Add a cleanup callback function"""
        self.cleanup_callbacks.append(callback)

    def remove_cleanup_callback(self, callback: Callable):
        """Remove a cleanup callback function"""
        if callback in self.cleanup_callbacks:
            self.cleanup_callbacks.remove(callback)

    @contextmanager
    def memory_context(self, operation: str = "unknown", limit_mb: float | None = None):
        """Context manager for memory-limited operations"""
        limit_mb = limit_mb or self.config.OCR_TASK_MEMORY_LIMIT
        start_memory = self.get_memory_usage()

        logger.debug(f"Starting {operation} (memory limit: {limit_mb}MB)")

        try:
            yield

        finally:
            end_memory = self.get_memory_usage()
            memory_used = end_memory - start_memory

            if memory_used > limit_mb:
                logger.warning(
                    f"Operation {operation} exceeded memory limit: "
                    f"{memory_used:.1f}MB > {limit_mb}MB"
                )

                # Trigger cleanup
                asyncio.create_task(self.cleanup_memory())

            logger.debug(
                f"Operation {operation} completed: "
                f"used {memory_used:.1f}MB, current: {end_memory:.1f}MB"
            )

    def get_memory_stats(self) -> dict[str, Any]:
        """Get comprehensive memory statistics"""
        stats = self.stats.get_stats()

        # Add system memory info
        try:
            system_memory = psutil.virtual_memory()
            stats.update(
                {
                    "system_total_mb": system_memory.total / 1024 / 1024,
                    "system_available_mb": system_memory.available / 1024 / 1024,
                    "system_percent": system_memory.percent,
                }
            )
        except Exception as e:
            logger.debug(f"Failed to get system memory stats: {e}")

        # Add memory history summary
        with self._lock:
            if self.memory_history:
                recent_memory = [
                    m for t, m in self.memory_history[-10:]
                ]  # Last 10 readings
                stats.update(
                    {
                        "avg_recent_memory_mb": sum(recent_memory) / len(recent_memory),
                        "min_recent_memory_mb": min(recent_memory),
                        "max_recent_memory_mb": max(recent_memory),
                    }
                )

        return stats

    def memory_limit_decorator(self, limit_mb: float | None = None):
        """Decorator for memory-limited functions"""

        def decorator(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                with self.memory_context(func.__name__, limit_mb):
                    return await func(*args, **kwargs)

            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                with self.memory_context(func.__name__, limit_mb):
                    return func(*args, **kwargs)

            return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

        return decorator


# Global memory manager instance
memory_manager = MemoryManager()


# Convenience decorators
def with_memory_limit(limit_mb: float | None = None):
    """Decorator for memory-limited operations"""
    return memory_manager.memory_limit_decorator(limit_mb)


def with_ocr_memory_limit(func):
    """Decorator for OCR operations with memory limit"""
    return memory_manager.memory_limit_decorator(MemoryConfig.OCR_TASK_MEMORY_LIMIT)(
        func
    )


@contextmanager
def memory_context(operation: str = "unknown", limit_mb: float | None = None):
    """Context manager for memory-limited operations"""
    with memory_manager.memory_context(operation, limit_mb):
        yield


# Utility functions
def get_memory_usage() -> float:
    """Get current memory usage in MB"""
    return memory_manager.get_memory_usage()


async def cleanup_memory(force: bool = False):
    """Perform memory cleanup"""
    await memory_manager.cleanup_memory(force)


def check_memory_limit(operation: str = "unknown") -> bool:
    """Check if memory usage is within limits"""
    return memory_manager.check_memory_limit(operation)


# Auto-start monitoring
def start_memory_monitoring():
    """Start memory monitoring (call once at startup)"""
    memory_manager.start_monitoring()


def stop_memory_monitoring():
    """Stop memory monitoring (call at shutdown)"""
    memory_manager.stop_monitoring()
