# 🗄️ Database Optimization Guide - FoodSave AI

> **Ostatnia aktualizacja:** 2025-07-27

## 📊 Overview

This guide documents the database optimizations implemented in FoodSave AI to improve performance, reliability, and monitoring capabilities.

## 🚀 Key Features

### 1. Performance Monitoring
- **Query tracking** - Monitor execution times for all database operations
- **Slow query detection** - Identify queries taking >1 second
- **Success rate tracking** - Monitor query success/failure rates
- **Connection pool monitoring** - Track pool utilization

### 2. Retry Mechanism
- **Exponential backoff** - Intelligent retry with increasing delays
- **Configurable retries** - Up to 3 attempts with configurable delays
- **Exception handling** - Handle transient connection issues
- **Error logging** - Comprehensive error tracking

### 3. SQLite Optimizations
- **WAL mode** - Better concurrent access
- **Cache optimization** - 64MB cache size
- **Page size optimization** - 4KB page size
- **Memory-based temp storage** - Faster temporary operations
- **Foreign key constraints** - Data integrity
- **Memory mapping** - 256MB mmap for better performance

### 4. Database Indexes
- **Automatic index creation** - Performance indexes for common queries
- **User sessions** - Indexes on user_id and created_at
- **Products** - Indexes on name, category, store
- **Receipts** - Indexes on date, store, user_id
- **Conversations** - Indexes on user_id and created_at
- **Messages** - Indexes on conversation_id and created_at
- **Search cache** - Indexes on query and timestamp

## 🔧 Implementation Details

### Database Performance Monitor

```python
class DatabasePerformanceMonitor:
    """Monitor database performance metrics and connection pool statistics."""
    
    def record_query(self, query_type: str, execution_time: float, success: bool = True):
        """Record query performance metrics."""
        
    def get_stats(self) -> dict[str, Any]:
        """Get comprehensive database performance statistics."""
```

### Retry Mechanism

```python
async def retry_db_operation(
    operation: Callable[..., Any],
    max_retries: int = 3,
    delay: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions: tuple[type[Exception], ...] = (OperationalError, DisconnectionError, ConnectionError),
    *args: Any,
    **kwargs: Any,
) -> Any:
    """Retry database operation with exponential backoff."""
```

### SQLite Optimizations

```python
async def optimize_sqlite_database() -> None:
    """Apply SQLite optimizations for production use."""
    
    # Enable WAL mode
    await conn.execute(text("PRAGMA journal_mode=WAL;"))
    
    # Optimize cache size (64MB)
    await conn.execute(text("PRAGMA cache_size=-64000;"))
    
    # Set synchronous mode to NORMAL
    await conn.execute(text("PRAGMA synchronous=NORMAL;"))
    
    # Use memory for temp tables
    await conn.execute(text("PRAGMA temp_store=MEMORY;"))
    
    # Optimize page size
    await conn.execute(text("PRAGMA page_size=4096;"))
    
    # Enable foreign key constraints
    await conn.execute(text("PRAGMA foreign_keys=ON;"))
    
    # Memory mapping
    await conn.execute(text("PRAGMA mmap_size=268435456;"))  # 256MB
```

## 📈 Performance Metrics

### Available Metrics
- **Total queries** - Number of queries executed
- **Failed queries** - Number of failed queries
- **Connection errors** - Number of connection errors
- **Retry attempts** - Number of retry attempts
- **Success rate** - Query success rate percentage
- **Slow queries count** - Number of queries >1 second
- **Query types** - Per-query-type statistics
- **Pool stats** - Connection pool statistics

### Accessing Metrics

```python
# Get performance statistics
stats = get_db_performance_stats()

# Get database information
db_info = await get_db_info()
```

## 🛠️ Usage Examples

### Optimized Database Session

```python
# Use optimized session with monitoring
async with get_optimized_db() as session:
    result = await session.execute(query)
    return result.fetchall()

# Standard session with retry
async with get_db() as session:
    result = await session.execute(query)
    return result.fetchall()

# Session with error handling
async with get_db_with_error_handling() as session:
    result = await session.execute(query)
    return result.fetchall()
```

### Database Initialization

```python
# Initialize database with all optimizations
await init_db()

# Check database connection
is_connected = await check_db_connection()

# Get database information
db_info = await get_db_info()
```

## 🔍 Monitoring Endpoints

### Health Check
```bash
curl http://localhost:8000/health
```

### Database Info
```bash
curl http://localhost:8000/api/database/info
```

### Performance Stats
```bash
curl http://localhost:8000/api/database/stats
```

## 📊 Configuration

### Retry Configuration
```python
DB_RETRY_ATTEMPTS = 3
DB_RETRY_DELAY = 1.0
DB_RETRY_BACKOFF = 2.0
DB_RETRY_EXCEPTIONS = (OperationalError, DisconnectionError, ConnectionError)
```

### Connection Pool Configuration
```python
# SQLite (NullPool for better performance)
poolclass=NullPool

# Other databases
pool_pre_ping=True
pool_recycle=3600
pool_size=20
max_overflow=40
pool_timeout=30
pool_reset_on_return="commit"
```

## 🚨 Troubleshooting

### Common Issues

1. **Connection errors**
   - Check database file permissions
   - Verify database URL configuration
   - Check available disk space

2. **Slow queries**
   - Review query execution plans
   - Check if indexes are being used
   - Monitor slow query logs

3. **Pool exhaustion**
   - Increase pool size if needed
   - Check for connection leaks
   - Monitor pool statistics

### Debug Commands

```bash
# Check database connection
python -c "from src.backend.core.database import check_db_connection; import asyncio; print(asyncio.run(check_db_connection()))"

# Get database info
python -c "from src.backend.core.database import get_db_info; import asyncio; print(asyncio.run(get_db_info()))"

# Get performance stats
python -c "from src.backend.core.database import get_db_performance_stats; print(get_db_performance_stats())"
```

## 📚 Related Documentation

- [Architecture Guide](core/ARCHITECTURE.md)
- [API Reference](core/API_REFERENCE.md)
- [Development Strategy](guides/development/DEVELOPMENT_STRATEGY.md)
- [Monitoring Guide](operations/MONITORING.md)

## 🔄 Updates

### 2025-07-27
- ✅ Implemented comprehensive database performance monitoring
- ✅ Added retry mechanism with exponential backoff
- ✅ Applied SQLite-specific optimizations
- ✅ Created automatic database indexes
- ✅ Added connection pool monitoring
- ✅ Implemented query performance tracking

---

**Database optimizations are now active and monitoring performance! 🚀** 