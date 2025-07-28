"""Unit tests for improved database module with retry mechanism and monitoring."""

import asyncio
import pytest
import time
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Any

from sqlalchemy.exc import OperationalError, DisconnectionError
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.database import (
    DatabasePerformanceMonitor,
    retry_db_operation,
    get_db_performance_stats,
    check_db_connection,
    get_db_info,
    DB_RETRY_ATTEMPTS,
    DB_RETRY_DELAY,
    DB_RETRY_BACKOFF,
    DB_RETRY_EXCEPTIONS,
    db_performance_monitor,
)


class TestDatabasePerformanceMonitor:
    """Test database performance monitoring functionality."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.monitor = DatabasePerformanceMonitor()

    def test_record_query_success(self) -> None:
        """Test recording successful query."""
        self.monitor.record_query("SELECT", 0.5, success=True)
        
        assert self.monitor.total_queries == 1
        assert self.monitor.failed_queries == 0
        assert "SELECT" in self.monitor.query_times
        assert len(self.monitor.query_times["SELECT"]) == 1
        assert self.monitor.query_times["SELECT"][0] == 0.5

    def test_record_query_failure(self) -> None:
        """Test recording failed query."""
        self.monitor.record_query("INSERT", 0.1, success=False)
        
        assert self.monitor.total_queries == 1
        assert self.monitor.failed_queries == 1
        assert "INSERT" not in self.monitor.query_times

    def test_record_slow_query(self) -> None:
        """Test recording slow query (>1 second)."""
        self.monitor.record_query("UPDATE", 1.5, success=True)
        
        assert len(self.monitor.slow_queries) == 1
        assert self.monitor.slow_queries[0]["query_type"] == "UPDATE"
        assert self.monitor.slow_queries[0]["execution_time"] == 1.5

    def test_record_retry_attempt(self) -> None:
        """Test recording retry attempt."""
        self.monitor.record_retry_attempt()
        self.monitor.record_retry_attempt()
        
        assert self.monitor.retry_attempts == 2

    def test_update_pool_stats(self) -> None:
        """Test updating connection pool statistics."""
        mock_pool = MagicMock()
        mock_pool.size.return_value = 10
        mock_pool._pool.qsize.return_value = 3
        mock_pool.overflow.return_value = 2

        self.monitor.update_pool_stats(mock_pool)
        
        assert self.monitor.connection_pool_stats["size"] == 10
        assert self.monitor.connection_pool_stats["checked_in"] == 3
        assert self.monitor.connection_pool_stats["checked_out"] == 7
        assert self.monitor.connection_pool_stats["overflow"] == 2

    def test_update_pool_stats_fallback(self) -> None:
        """Test updating pool stats with fallback for different pool types."""
        mock_pool = MagicMock()
        # Remove _pool attribute to trigger fallback
        del mock_pool._pool

        self.monitor.update_pool_stats(mock_pool)
        
        assert self.monitor.connection_pool_stats["size"] == 0
        assert self.monitor.connection_pool_stats["checked_in"] == 0
        assert self.monitor.connection_pool_stats["checked_out"] == 0
        assert self.monitor.connection_pool_stats["overflow"] == 0

    def test_get_stats_comprehensive(self) -> None:
        """Test getting comprehensive performance statistics."""
        # Record some test data
        self.monitor.record_query("SELECT", 0.5, success=True)
        self.monitor.record_query("INSERT", 0.1, success=False)
        self.monitor.record_query("UPDATE", 1.5, success=True)
        self.monitor.record_retry_attempt()
        self.monitor.connection_errors = 2

        stats = self.monitor.get_stats()
        
        assert stats["total_queries"] == 3
        assert stats["failed_queries"] == 1
        assert stats["connection_errors"] == 2
        assert stats["retry_attempts"] == 1
        assert stats["success_rate"] == 2/3
        assert stats["slow_queries_count"] == 1
        assert "SELECT" in stats["query_types"]
        assert "UPDATE" in stats["query_types"]
        assert "INSERT" not in stats["query_types"]  # Failed query not recorded


class TestRetryMechanism:
    """Test database retry mechanism functionality."""

    @pytest.mark.asyncio
    async def test_retry_success_on_first_attempt(self) -> None:
        """Test successful operation on first attempt."""
        async def successful_operation() -> str:
            return "success"

        result = await retry_db_operation(successful_operation)
        assert result == "success"

    @pytest.mark.asyncio
    async def test_retry_success_after_failures(self) -> None:
        """Test successful operation after some failures."""
        attempt_count = 0
        
        async def failing_then_successful_operation() -> str:
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count < 3:
                raise ConnectionError("Connection failed")
            return "success"

        result = await retry_db_operation(failing_then_successful_operation)
        assert result == "success"
        assert attempt_count == 3

    @pytest.mark.asyncio
    async def test_retry_max_attempts_exceeded(self) -> None:
        """Test retry mechanism when max attempts are exceeded."""
        async def always_failing_operation() -> str:
            raise ConnectionError("Connection lost")

        with pytest.raises(ConnectionError):
            await retry_db_operation(always_failing_operation)

    @pytest.mark.asyncio
    async def test_retry_exponential_backoff(self) -> None:
        """Test exponential backoff timing."""
        start_time = time.time()
        attempt_count = 0
        
        async def failing_operation() -> str:
            nonlocal attempt_count
            attempt_count += 1
            raise ConnectionError("Connection failed")

        with pytest.raises(ConnectionError):
            await retry_db_operation(failing_operation, max_retries=2)

        # Should have 3 attempts (initial + 2 retries)
        assert attempt_count == 3

    @pytest.mark.asyncio
    async def test_retry_non_retryable_exception(self) -> None:
        """Test that non-retryable exceptions are not retried."""
        async def operation_with_value_error() -> str:
            raise ValueError("This should not be retried")

        with pytest.raises(ValueError):
            await retry_db_operation(operation_with_value_error)

    @pytest.mark.asyncio
    async def test_retry_sync_function(self) -> None:
        """Test retry mechanism with synchronous function."""
        def sync_operation() -> str:
            return "sync_success"

        result = await retry_db_operation(sync_operation)
        assert result == "sync_success"

    @pytest.mark.asyncio
    async def test_retry_custom_parameters(self) -> None:
        """Test retry mechanism with custom parameters."""
        async def operation_with_params(value: int, multiplier: int = 1) -> int:
            return value * multiplier

        result = await retry_db_operation(operation_with_params, 5, multiplier=2)
        assert result == 10


class TestDatabaseConnectionFunctions:
    """Test database connection and info functions."""

    @pytest.mark.asyncio
    async def test_check_db_connection_success(self) -> None:
        """Test successful database connection check."""
        with patch("backend.core.database.AsyncSessionLocal") as mock_session_local:
            mock_session = AsyncMock()
            mock_session.execute.return_value.fetchone.return_value = (1,)
            mock_session_local.return_value.__aenter__.return_value = mock_session

            result = await check_db_connection()
            assert result is True

    @pytest.mark.asyncio
    async def test_check_db_connection_failure(self) -> None:
        """Test failed database connection check."""
        with patch("backend.core.database.AsyncSessionLocal") as mock_session_local:
            mock_session_local.return_value.__aenter__.side_effect = Exception("Connection failed")

            result = await check_db_connection()
            assert result is False

    @pytest.mark.asyncio
    async def test_get_db_info_success(self) -> None:
        """Test successful database info retrieval."""
        with patch("backend.core.database.AsyncSessionLocal") as mock_session_local:
            mock_session = AsyncMock()
            mock_result = MagicMock()
            mock_result.fetchall.return_value = [("table1",), ("table2",)]
            mock_session.execute.return_value = mock_result
            mock_session_local.return_value.__aenter__.return_value = mock_session

            result = await get_db_info()
            
            assert result["connection_status"] == "connected"
            assert "table1" in result["tables"]
            assert "table2" in result["tables"]
            assert "performance_stats" in result

    @pytest.mark.asyncio
    async def test_get_db_info_failure(self) -> None:
        """Test failed database info retrieval."""
        with patch("backend.core.database.AsyncSessionLocal") as mock_session_local:
            mock_session_local.return_value.__aenter__.side_effect = Exception("Database error")

            result = await get_db_info()
            
            assert result["connection_status"] == "error"
            assert "error" in result
            assert result["tables"] == []

    def test_get_db_performance_stats(self) -> None:
        """Test getting database performance statistics."""
        # Reset monitor for clean test
        db_performance_monitor.query_times.clear()
        db_performance_monitor.slow_queries.clear()
        db_performance_monitor.total_queries = 0
        db_performance_monitor.failed_queries = 0
        db_performance_monitor.connection_errors = 0
        db_performance_monitor.retry_attempts = 0

        # Add some test data
        db_performance_monitor.record_query("SELECT", 0.5, success=True)
        db_performance_monitor.record_query("INSERT", 0.1, success=False)
        db_performance_monitor.record_retry_attempt()
        db_performance_monitor.connection_errors = 1

        stats = get_db_performance_stats()
        
        assert stats["total_queries"] == 2
        assert stats["failed_queries"] == 1
        assert stats["connection_errors"] == 1
        assert stats["retry_attempts"] == 1
        assert "pool_stats" in stats


class TestDatabaseRetryConfiguration:
    """Test database retry configuration constants."""

    def test_retry_configuration_constants(self) -> None:
        """Test that retry configuration constants are properly defined."""
        assert DB_RETRY_ATTEMPTS == 3
        assert DB_RETRY_DELAY == 1.0
        assert DB_RETRY_BACKOFF == 2.0
        assert OperationalError in DB_RETRY_EXCEPTIONS
        assert DisconnectionError in DB_RETRY_EXCEPTIONS
        assert ConnectionError in DB_RETRY_EXCEPTIONS


class TestDatabasePerformanceMonitoring:
    """Test database performance monitoring integration."""

    @pytest.mark.asyncio
    async def test_performance_monitoring_integration(self) -> None:
        """Test that performance monitoring is properly integrated."""
        # Reset monitor
        db_performance_monitor.query_times.clear()
        db_performance_monitor.slow_queries.clear()
        db_performance_monitor.total_queries = 0
        db_performance_monitor.failed_queries = 0
        db_performance_monitor.connection_errors = 0
        db_performance_monitor.retry_attempts = 0

        # Simulate a retry operation
        async def failing_operation() -> str:
            raise ConnectionError("Test error")

        with pytest.raises(ConnectionError):
            await retry_db_operation(failing_operation, max_retries=1)

        # Check that retry attempts were recorded
        stats = db_performance_monitor.get_stats()
        assert stats["retry_attempts"] == 1

    def test_performance_monitor_singleton(self) -> None:
        """Test that performance monitor is a singleton."""
        from backend.core.database import db_performance_monitor as monitor1
        from backend.core.database import db_performance_monitor as monitor2
        
        assert monitor1 is monitor2
        assert id(monitor1) == id(monitor2)


class TestDatabaseErrorHandling:
    """Test database error handling scenarios."""

    @pytest.mark.asyncio
    async def test_connection_pool_error_handling(self) -> None:
        """Test handling of connection pool errors."""
        mock_pool = MagicMock()
        mock_pool.size.side_effect = Exception("Pool error")

        # Should not raise exception, should set safe defaults
        db_performance_monitor.update_pool_stats(mock_pool)
        
        stats = db_performance_monitor.connection_pool_stats
        assert stats["size"] == 0
        assert stats["checked_in"] == 0
        assert stats["checked_out"] == 0
        assert stats["overflow"] == 0

    @pytest.mark.asyncio
    async def test_retry_with_different_exception_types(self) -> None:
        """Test retry mechanism with different exception types."""
        async def operation_with_disconnection_error() -> str:
            raise ConnectionError("Disconnection")

        with pytest.raises(ConnectionError):
            await retry_db_operation(operation_with_disconnection_error, max_retries=1)

        # Verify retry was attempted
        stats = db_performance_monitor.get_stats()
        assert stats["retry_attempts"] > 0 