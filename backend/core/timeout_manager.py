"""
Enhanced timeout management with progressive timeouts and fallback strategies.
"""

import asyncio
import builtins
from collections.abc import Callable
from contextlib import asynccontextmanager
import functools
import logging
import time
from typing import Any, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


class TimeoutConfig:
    """Configuration for timeout management"""

    # OCR timeouts
    OCR_QUICK_TIMEOUT = 45  # Quick attempt - increased for better quality
    OCR_STANDARD_TIMEOUT = 90  # Standard processing
    OCR_FALLBACK_TIMEOUT = 180  # Fallback with aggressive preprocessing

    # AI Analysis timeouts
    AI_ANALYSIS_TIMEOUT = 600  # AI analysis (10 minut)
    AI_FALLBACK_TIMEOUT = 60  # Fallback parsing

    # API timeouts
    API_RESPONSE_TIMEOUT = 120  # Total API response time
    UPLOAD_TIMEOUT = 300  # File upload timeout

    # Database timeouts
    DB_QUERY_TIMEOUT = 10  # Database query timeout
    DB_TRANSACTION_TIMEOUT = 30  # Database transaction timeout


class TimeoutError(Exception):
    """Custom timeout error with context"""

    def __init__(self, message: str, timeout: float, operation: str):
        self.timeout = timeout
        self.operation = operation
        super().__init__(f"{message} (timeout: {timeout}s, operation: {operation})")


class TimeoutManager:
    """Enhanced timeout manager with progressive strategies"""

    def __init__(self):
        self.config = TimeoutConfig()
        self.active_timeouts = {}

    def with_timeout(self, timeout: float, operation: str = "unknown"):
        """Decorator for adding timeout to async functions"""

        def decorator(func: Callable[..., T]) -> Callable[..., T]:
            @functools.wraps(func)
            async def wrapper(*args, **kwargs) -> T:
                return await self.run_with_timeout(
                    func(*args, **kwargs), timeout, operation
                )

            return wrapper

        return decorator

    async def run_with_timeout(
        self, coro: Any, timeout: float, operation: str = "unknown"
    ) -> Any:
        """Run coroutine with timeout and proper error handling"""
        start_time = time.time()

        try:
            result = await asyncio.wait_for(coro, timeout=timeout)
            execution_time = time.time() - start_time

            if execution_time > timeout * 0.8:  # Warn if close to timeout
                logger.warning(
                    f"Operation '{operation}' took {execution_time:.2f}s "
                    f"(timeout: {timeout}s)"
                )

            return result

        except builtins.TimeoutError:
            execution_time = time.time() - start_time
            logger.error(
                f"Operation '{operation}' timed out after {execution_time:.2f}s "
                f"(timeout: {timeout}s)"
            )
            raise TimeoutError(f"Operation '{operation}' timed out", timeout, operation)

    async def progressive_timeout(
        self,
        operations: list[tuple[Callable, float, str]],
        operation_name: str = "progressive_operation",
    ) -> Any:
        """
        Execute operations with progressive timeouts (quick -> standard -> fallback)

        Args:
            operations: List of (function, timeout, description) tuples
            operation_name: Name for logging

        Returns:
            Result from first successful operation
        """
        last_error = None

        for i, (func, timeout, description) in enumerate(operations):
            try:
                logger.info(
                    f"Attempting {operation_name} - {description} "
                    f"(timeout: {timeout}s)"
                )

                result = await self.run_with_timeout(
                    func(), timeout, f"{operation_name}_{description}"
                )

                if i > 0:  # Not the first attempt
                    logger.info(
                        f"{operation_name} succeeded with {description} "
                        f"after {i} failed attempts"
                    )

                return result

            except Exception as e:
                last_error = e
                logger.warning(f"{operation_name} failed with {description}: {e!s}")

                if i < len(operations) - 1:  # Not the last attempt
                    continue

        # All operations failed
        logger.error(f"All {operation_name} attempts failed")
        raise last_error or TimeoutError(
            f"All {operation_name} attempts failed",
            sum(op[1] for op in operations),
            operation_name,
        )

    @asynccontextmanager
    async def timeout_context(self, timeout: float, operation: str = "unknown"):
        """Context manager for timeout handling"""
        start_time = time.time()

        try:
            task = asyncio.create_task(asyncio.sleep(timeout))
            self.active_timeouts[operation] = task

            yield

        except builtins.TimeoutError:
            execution_time = time.time() - start_time
            logger.error(
                f"Context operation '{operation}' timed out after "
                f"{execution_time:.2f}s (timeout: {timeout}s)"
            )
            raise TimeoutError(
                f"Context operation '{operation}' timed out", timeout, operation
            )

        finally:
            if operation in self.active_timeouts:
                self.active_timeouts[operation].cancel()
                del self.active_timeouts[operation]

    def cancel_operation(self, operation: str) -> bool:
        """Cancel a running operation by name"""
        if operation in self.active_timeouts:
            self.active_timeouts[operation].cancel()
            del self.active_timeouts[operation]
            logger.info(f"Cancelled operation: {operation}")
            return True
        return False

    def get_active_operations(self) -> list[str]:
        """Get list of currently active operations"""
        return list(self.active_timeouts.keys())


# Global timeout manager instance
timeout_manager = TimeoutManager()


# Convenience decorators
def with_quick_timeout(func: Callable[..., T]) -> Callable[..., T]:
    """Decorator for quick operations (15s timeout)"""
    return timeout_manager.with_timeout(TimeoutConfig.OCR_QUICK_TIMEOUT, func.__name__)(
        func
    )


def with_standard_timeout(func: Callable[..., T]) -> Callable[..., T]:
    """Decorator for standard operations (30s timeout)"""
    return timeout_manager.with_timeout(
        TimeoutConfig.OCR_STANDARD_TIMEOUT, func.__name__
    )(func)


def with_api_timeout(func: Callable[..., T]) -> Callable[..., T]:
    """Decorator for API operations (120s timeout)"""
    return timeout_manager.with_timeout(
        TimeoutConfig.API_RESPONSE_TIMEOUT, func.__name__
    )(func)


def with_db_timeout(func: Callable[..., T]) -> Callable[..., T]:
    """Decorator for database operations (10s timeout)"""
    return timeout_manager.with_timeout(TimeoutConfig.DB_QUERY_TIMEOUT, func.__name__)(
        func
    )


# Async context managers
async def quick_timeout_context(operation: str = "quick_operation"):
    """Context manager for quick operations"""
    async with timeout_manager.timeout_context(
        TimeoutConfig.OCR_QUICK_TIMEOUT, operation
    ):
        yield


async def standard_timeout_context(operation: str = "standard_operation"):
    """Context manager for standard operations"""
    async with timeout_manager.timeout_context(
        TimeoutConfig.OCR_STANDARD_TIMEOUT, operation
    ):
        yield


async def api_timeout_context(operation: str = "api_operation"):
    """Context manager for API operations"""
    async with timeout_manager.timeout_context(
        TimeoutConfig.API_RESPONSE_TIMEOUT, operation
    ):
        yield
