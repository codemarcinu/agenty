"""
Database configuration and session management.
"""

import asyncio
import logging
import time
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Callable, TYPE_CHECKING

import aiosqlite  # Force aiosqlite import
from fastapi import HTTPException
from sqlalchemy import create_engine, event, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from sqlalchemy.pool import NullPool
from sqlalchemy.exc import OperationalError, DisconnectionError

from settings import settings

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

DATABASE_URL = settings.DATABASE_URL

# Fix SQLite async driver issue
if DATABASE_URL.startswith("sqlite:///"):
    DATABASE_URL = DATABASE_URL.replace("sqlite:///", "sqlite+aiosqlite:///")
elif DATABASE_URL.startswith("sqlite://"):
    DATABASE_URL = DATABASE_URL.replace("sqlite://", "sqlite+aiosqlite://")

logger.info(f"Database URL configured: {DATABASE_URL}")


# Retry configuration
DB_RETRY_ATTEMPTS = 3
DB_RETRY_DELAY = 1.0
DB_RETRY_BACKOFF = 2.0
DB_RETRY_EXCEPTIONS = (OperationalError, DisconnectionError, ConnectionError)


class DatabasePerformanceMonitor:
    """Monitor database performance metrics and connection pool statistics.

    This class tracks query performance, connection errors, retry attempts,
    and connection pool statistics to provide comprehensive database monitoring.

    Attributes:
        query_times: Dictionary mapping query types to execution times
        slow_queries: List of queries taking more than 1 second
        total_queries: Total number of queries executed
        failed_queries: Number of failed queries
        connection_errors: Number of connection errors
        retry_attempts: Number of retry attempts
        connection_pool_stats: Current connection pool statistics
    """

    def __init__(self) -> None:
        """Initialize the database performance monitor."""
        self.query_times: dict[str, list[float]] = {}
        self.slow_queries: list[dict[str, Any]] = []
        self.total_queries = 0
        self.failed_queries = 0
        self.connection_errors = 0
        self.retry_attempts = 0
        self.connection_pool_stats: dict[str, int] = {
            "checked_in": 0,
            "checked_out": 0,
            "overflow": 0,
            "size": 0,
        }

    def record_query(
        self, query_type: str, execution_time: float, success: bool = True
    ) -> None:
        """Record query performance metrics.

        Args:
            query_type: Type of query (SELECT, INSERT, UPDATE, DELETE, etc.)
            execution_time: Query execution time in seconds
            success: Whether the query was successful
        """
        self.total_queries += 1

        if not success:
            self.failed_queries += 1
            return

        if query_type not in self.query_times:
            self.query_times[query_type] = []

        self.query_times[query_type].append(execution_time)

        # Track slow queries (>1 second)
        if execution_time > 1.0:
            self.slow_queries.append(
                {
                    "query_type": query_type,
                    "execution_time": execution_time,
                    "timestamp": time.time(),
                }
            )

    def record_retry_attempt(self) -> None:
        """Record a retry attempt for database operations."""
        self.retry_attempts += 1

    def update_pool_stats(self, pool: Any) -> None:
        """Update connection pool statistics.

        Args:
            pool: SQLAlchemy connection pool object
        """
        try:
            if hasattr(pool, "_pool"):
                # Get pool size safely
                pool_size = getattr(pool, "size", lambda: 0)()
                checked_in = getattr(pool._pool, "qsize", lambda: 0)()
                checked_out = max(0, pool_size - checked_in)
                overflow = getattr(pool, "overflow", lambda: 0)()

                self.connection_pool_stats.update(
                    {
                        "checked_in": checked_in,
                        "checked_out": checked_out,
                        "overflow": overflow,
                        "size": pool_size,
                    }
                )
            else:
                # Fallback for different pool types
                self.connection_pool_stats.update(
                    {
                        "checked_in": 0,
                        "checked_out": 0,
                        "overflow": 0,
                        "size": 0,
                    }
                )
        except Exception as e:
            logger.warning(f"Could not update pool stats: {e}")
            # Set safe defaults
            self.connection_pool_stats.update(
                {
                    "checked_in": 0,
                    "checked_out": 0,
                    "overflow": 0,
                    "size": 0,
                }
            )

    def get_stats(self) -> dict[str, Any]:
        """Get comprehensive database performance statistics.

        Returns:
            Dictionary containing performance metrics including:
            - total_queries: Total number of queries
            - failed_queries: Number of failed queries
            - connection_errors: Number of connection errors
            - retry_attempts: Number of retry attempts
            - success_rate: Query success rate
            - slow_queries_count: Number of slow queries
            - query_types: Per-query-type statistics
            - pool_stats: Connection pool statistics
        """
        stats = {
            "total_queries": self.total_queries,
            "failed_queries": self.failed_queries,
            "connection_errors": self.connection_errors,
            "retry_attempts": self.retry_attempts,
            "success_rate": (self.total_queries - self.failed_queries)
            / max(self.total_queries, 1),
            "slow_queries_count": len(self.slow_queries),
            "query_types": {},
            "pool_stats": self.connection_pool_stats,
        }

        for query_type, times in self.query_times.items():
            if times:
                stats["query_types"][query_type] = {
                    "count": len(times),
                    "avg_time": sum(times) / len(times),
                    "max_time": max(times),
                    "min_time": min(times),
                }

        return stats


# Global performance monitor
db_performance_monitor = DatabasePerformanceMonitor()

# Database connection pooling configuration
DATABASE_POOL_SIZE = 20
DATABASE_MAX_OVERFLOW = 30
DATABASE_POOL_TIMEOUT = 30
DATABASE_POOL_RECYCLE = 3600

# Create engine with connection pooling - fixed for container environment
if settings.DATABASE_URL.startswith("sqlite"):
    # SQLite configuration for containers
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=settings.DEBUG,
        connect_args={
            "check_same_thread": False,
            "timeout": 20,
        },
        poolclass=NullPool,  # SQLite doesn't support connection pooling
    )
else:
    # For other databases (future migration)
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=settings.DEBUG,
        pool_size=DATABASE_POOL_SIZE,
        max_overflow=DATABASE_MAX_OVERFLOW,
        pool_timeout=DATABASE_POOL_TIMEOUT,
        pool_recycle=DATABASE_POOL_RECYCLE,
        pool_pre_ping=True,
    )

# Session factory with optimized settings
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,  # Prevent lazy loading issues
    autoflush=True,
    autocommit=False,
)


def get_async_session_factory() -> async_sessionmaker[AsyncSession]:
    """Return async session factory for database operations.

    Returns:
        Configured async session factory
    """
    return AsyncSessionLocal


async def retry_db_operation(
    operation: Callable[..., Any],
    max_retries: int = DB_RETRY_ATTEMPTS,
    delay: float = DB_RETRY_DELAY,
    backoff_factor: float = DB_RETRY_BACKOFF,
    exceptions: tuple[type[Exception], ...] = DB_RETRY_EXCEPTIONS,
    *args: Any,
    **kwargs: Any,
) -> Any:
    """Retry database operation with exponential backoff.

    This function implements a robust retry mechanism for database operations
    with exponential backoff to handle transient connection issues.

    Args:
        operation: Database operation to retry (can be async or sync)
        max_retries: Maximum number of retry attempts
        delay: Initial delay between retries in seconds
        backoff_factor: Multiplier for delay on each retry
        exceptions: Tuple of exceptions to catch and retry
        *args: Arguments to pass to operation
        **kwargs: Keyword arguments to pass to operation

    Returns:
        Result of the operation

    Raises:
        Last exception if all retries fail
        RuntimeError: If retry loop exits unexpectedly
    """
    last_exception = None
    current_delay = delay

    for attempt in range(max_retries + 1):
        try:
            if asyncio.iscoroutinefunction(operation):
                return await operation(*args, **kwargs)
            # Run sync function in thread pool
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, operation, *args, **kwargs)

        except exceptions as e:
            last_exception = e
            db_performance_monitor.record_retry_attempt()
            
            if attempt < max_retries:
                logger.warning(
                    f"Database operation retry attempt {attempt + 1}/{max_retries} "
                    f"after error: {e}. Retrying in {current_delay:.2f}s..."
                )
                await asyncio.sleep(current_delay)
                current_delay *= backoff_factor
            else:
                logger.error(
                    f"All {max_retries + 1} database operation attempts failed: {e}"
                )
                raise last_exception

    # This should never be reached, but just in case
    raise RuntimeError("Retry loop exited unexpectedly")


async def optimize_sqlite_database() -> None:
    """Apply SQLite optimizations for production use.

    This function applies various SQLite-specific optimizations including:
    - WAL mode for better concurrent access
    - Optimized cache size and page size
    - Memory-based temp storage
    - Foreign key constraints
    - Memory mapping for better performance

    Raises:
        Exception: If optimizations fail to apply
    """
    if not DATABASE_URL.startswith("sqlite"):
        return

    async def _optimize() -> None:
        async with engine.begin() as conn:
            # Enable WAL mode for better concurrent access
            await conn.execute(text("PRAGMA journal_mode=WAL;"))

            # Optimize cache size (64MB)
            await conn.execute(text("PRAGMA cache_size=-64000;"))

            # Set synchronous mode to NORMAL for better performance
            await conn.execute(text("PRAGMA synchronous=NORMAL;"))

            # Use memory for temp tables
            await conn.execute(text("PRAGMA temp_store=MEMORY;"))

            # Optimize page size
            await conn.execute(text("PRAGMA page_size=4096;"))

            # Enable foreign key constraints
            await conn.execute(text("PRAGMA foreign_keys=ON;"))

            # Additional optimizations
            await conn.execute(text("PRAGMA mmap_size=268435456;"))  # 256MB mmap
            await conn.execute(text("PRAGMA auto_vacuum=INCREMENTAL;"))

    try:
        await retry_db_operation(_optimize)
        logger.info("SQLite database optimizations applied successfully")
    except Exception as e:
        logger.error(f"Error applying SQLite optimizations: {e}")
        raise


async def create_database_indexes() -> None:
    """Create database indexes for better query performance.

    This function creates indexes on frequently queried columns to improve
    query performance. Indexes are created for:
    - User sessions (user_id, created_at)
    - Products (name, category, store)
    - Receipts (date, store, user_id)
    - Conversations (user_id, created_at)
    - Messages (conversation_id, created_at)
    - Search cache (query, timestamp)

    Raises:
        Exception: If index creation fails
    """
    async def _create_indexes() -> None:
        async with engine.begin() as conn:
            # Create indexes for frequently queried columns
            indexes = [
                # User sessions
                "CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id ON user_sessions(user_id);",
                "CREATE INDEX IF NOT EXISTS idx_user_sessions_created_at ON user_sessions(created_at);",
                # Products
                "CREATE INDEX IF NOT EXISTS idx_products_name ON products(name);",
                "CREATE INDEX IF NOT EXISTS idx_products_category ON products(category);",
                "CREATE INDEX IF NOT EXISTS idx_products_store ON products(store);",
                # Receipts
                "CREATE INDEX IF NOT EXISTS idx_receipts_date ON receipts(date);",
                "CREATE INDEX IF NOT EXISTS idx_receipts_store ON receipts(store);",
                "CREATE INDEX IF NOT EXISTS idx_receipts_user_id ON receipts(user_id);",
                # Conversations
                "CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversations(user_id);",
                "CREATE INDEX IF NOT EXISTS idx_conversations_created_at ON conversations(created_at);",
                # Messages
                "CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON messages(conversation_id);",
                "CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages(created_at);",
                # Search cache
                "CREATE INDEX IF NOT EXISTS idx_search_cache_query ON search_cache(query);",
                "CREATE INDEX IF NOT EXISTS idx_search_cache_timestamp ON search_cache(timestamp);",
            ]

            for index_sql in indexes:
                try:
                    await conn.execute(text(index_sql))
                except Exception as e:
                    logger.warning(f"Failed to create index: {e}")

    try:
        await retry_db_operation(_create_indexes)
        logger.info("Database indexes created successfully")
    except Exception as e:
        logger.error(f"Error creating database indexes: {e}")
        raise


@asynccontextmanager
async def get_optimized_db() -> AsyncGenerator[AsyncSession, None]:
    """Optimized database session with performance monitoring and retry mechanism.

    This context manager provides a database session with:
    - Performance monitoring
    - Retry mechanism for transient errors
    - Proper error handling and logging
    - Automatic session cleanup

    Yields:
        AsyncSession: Configured database session

    Raises:
        Exception: If session creation or operation fails
    """
    start_time = time.time()
    session = None

    async def _get_session() -> AsyncSession:
        nonlocal session
        session = AsyncSessionLocal()
        return session

    try:
        session = await retry_db_operation(_get_session)
        yield session
        db_performance_monitor.record_query(
            "session", time.time() - start_time, success=True
        )

    except Exception as e:
        db_performance_monitor.connection_errors += 1
        db_performance_monitor.record_query(
            "session", time.time() - start_time, success=False
        )
        logger.error(f"Database session error: {e}")
        raise

    finally:
        if session:
            await session.close()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Standard database session with retry mechanism.

    This function provides a standard database session with retry capability
    for handling transient connection issues.

    Yields:
        AsyncSession: Database session

    Raises:
        Exception: If session creation or operation fails
    """
    async def _get_session() -> AsyncSession:
        async with AsyncSessionLocal() as session:
            return session

    try:
        session = await retry_db_operation(_get_session)
        yield session
    except Exception as e:
        logger.error(f"Database session error: {e}")
        raise


async def get_db_with_error_handling() -> AsyncGenerator[AsyncSession, None]:
    """Database dependency with proper error handling and retry mechanism.

    This function is designed to be used as a FastAPI dependency for database
    operations. It includes comprehensive error handling and retry logic.

    Yields:
        AsyncSession: Database session

    Raises:
        HTTPException: If database connection fails with 500 status code
    """
    try:
        async def _get_session() -> AsyncSession:
            async with AsyncSessionLocal() as session:
                return session

        session = await retry_db_operation(_get_session)
        yield session
    except Exception:
        logger.error("Database connection failed", exc_info=True)
        db_performance_monitor.connection_errors += 1
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Database connection failed",
                "error_code": "INTERNAL_SERVER_ERROR",
            },
        )


async def init_db() -> None:
    """Initialize database with all tables, migrations, and optimizations.

    This function performs complete database initialization including:
    - Table creation
    - Migration execution
    - SQLite optimizations
    - Index creation

    Raises:
        Exception: If database initialization fails
    """
    try:
        from core.database_migrations import run_all_migrations
        from models.conversation import Base as ConversationBase

        async def _init_database() -> None:
            # Create all tables
            async with engine.begin() as conn:
                await conn.run_sync(ConversationBase.metadata.create_all)

            # Run migrations
            await run_all_migrations()

            # Apply database optimizations
            await optimize_sqlite_database()

            # Create performance indexes
            await create_database_indexes()

        await retry_db_operation(_init_database)
        logger.info("Database initialized successfully with optimizations")

    except Exception:
        logger.exception("Database initialization failed")
        raise


async def check_db_connection() -> bool:
    """Check if database connection is working with retry mechanism.

    This function performs a simple connection test to verify database
    availability and connectivity.

    Returns:
        True if connection is successful, False otherwise
    """
    async def _check_connection() -> bool:
        async with AsyncSessionLocal() as session:
            result = await session.execute(text("SELECT 1"))
            result.fetchone()
            return True

    try:
        return await retry_db_operation(_check_connection)
    except Exception:
        logger.exception("Database connection check failed")
        return False


async def get_db_info() -> dict[str, Any]:
    """Get database information with performance metrics and pool monitoring.

    This function provides comprehensive database information including:
    - Database URL
    - Table list
    - Connection status
    - Performance statistics
    - Connection pool statistics

    Returns:
        Dictionary containing database information and statistics
    """
    async def _get_database_info() -> dict[str, Any]:
        async with AsyncSessionLocal() as session:
            # Get table information
            result = await session.execute(
                text(
                    """
                SELECT name FROM sqlite_master
                WHERE type='table' AND name NOT LIKE 'sqlite_%'
                ORDER BY name
            """
                )
            )
            tables = [row[0] for row in result.fetchall()]

            # Update pool statistics
            db_performance_monitor.update_pool_stats(engine.pool)

            return {
                "database_url": DATABASE_URL,
                "tables": tables,
                "connection_status": "connected",
                "performance_stats": db_performance_monitor.get_stats(),
            }

    try:
        return await retry_db_operation(_get_database_info)
    except Exception as e:
        logger.exception("Error getting database info")
        # Update pool statistics even on error
        db_performance_monitor.update_pool_stats(engine.pool)
        
        return {
            "database_url": DATABASE_URL,
            "tables": [],
            "connection_status": "error",
            "error": str(e),
            "performance_stats": db_performance_monitor.get_stats(),
        }


def get_db_performance_stats() -> dict[str, Any]:
    """Get database performance statistics with pool monitoring.

    This function provides current database performance statistics including
    query metrics, connection pool status, and error tracking.

    Returns:
        Dictionary containing comprehensive performance statistics
    """
    # Update pool statistics
    db_performance_monitor.update_pool_stats(engine.pool)
    return db_performance_monitor.get_stats()


class Base(DeclarativeBase):
    """Unified Base class for all SQLAlchemy models.

    This class serves as the base for all SQLAlchemy models in the application,
    providing a consistent foundation for database schema definitions.
    """
