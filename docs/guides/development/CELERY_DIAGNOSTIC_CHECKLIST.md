# Celery Serialization Diagnostic Checklist

## Problem Description
**Error**: `Exception information must include the exception type`

This error occurs when Celery cannot properly serialize exception information for task results stored in Redis.

## Quick Diagnostic Steps

### 1. Environment Check
- [ ] Verify Celery version: `pip show celery`
- [ ] Verify Redis version: `docker exec redis redis-server --version`
- [ ] Check Python version: `python --version`
- [ ] Verify all dependencies are up to date

### 2. Minimal Test
- [ ] Run minimal Celery test: `./run_celery_test.sh`
- [ ] Check if issue reproduces in isolated environment
- [ ] Compare results with main project

### 3. Redis Cleanup
```bash
# Clear all Redis data
docker exec redis redis-cli FLUSHALL

# Or restart Redis container
docker restart redis
```

### 4. Celery Configuration Check
- [ ] Verify `task_serializer='json'`
- [ ] Verify `result_serializer='json'`
- [ ] Check `accept_content=['json']`
- [ ] Ensure `task_store_errors_even_if_ignored=True`

## Detailed Investigation

### 5. Task Exception Analysis
- [ ] Check if tasks raise custom exceptions
- [ ] Convert custom exceptions to standard Python exceptions
- [ ] Ensure all exceptions are JSON-serializable

### 6. Result Object Analysis
- [ ] Check if task results contain non-serializable objects
- [ ] Look for datetime, custom classes, or complex nested structures
- [ ] Convert to simple JSON-serializable objects

### 7. Celery Worker Debug
```bash
# Start worker with debug logging
celery -A your_app worker --loglevel=debug

# Check worker logs for serialization errors
docker logs celery-worker
```

### 8. Alternative Result Backends
- [ ] Try RPC backend: `result_backend='rpc://'`
- [ ] Try database backend: `result_backend='db+postgresql://...'`
- [ ] Compare behavior across different backends

## Code Fixes

### 9. Exception Handling
```python
@app.task
def your_task():
    try:
        # Your task logic
        return result
    except CustomError as e:
        # Convert to standard exception
        raise RuntimeError(f"Custom error occurred: {str(e)}")
    except Exception as e:
        # Ensure all exceptions are standard Python exceptions
        raise RuntimeError(f"Task failed: {str(e)}")
```

### 10. Result Serialization
```python
@app.task
def your_task():
    result = complex_object()
    
    # Convert to JSON-serializable format
    return {
        "status": "success",
        "data": {
            "simple_value": str(result.complex_attribute),
            "timestamp": result.timestamp.isoformat() if result.timestamp else None
        }
    }
```

## Advanced Debugging

### 11. Custom Serializer
```python
import json
from datetime import datetime

class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

app.conf.update(
    result_serializer='json',
    json_encoder=CustomJSONEncoder
)
```

### 12. Task Result Inspection
```python
# Inspect task result structure
result = your_task.delay()
print(f"Result ID: {result.id}")
print(f"Result Status: {result.status}")
print(f"Result Info: {result.info}")
print(f"Result Traceback: {result.traceback}")
```

## Prevention

### 13. Best Practices
- [ ] Always use standard Python exceptions
- [ ] Return simple JSON-serializable objects
- [ ] Test task serialization in isolation
- [ ] Use type hints to catch serialization issues early
- [ ] Implement proper error handling in all tasks

### 14. Monitoring
- [ ] Set up Celery monitoring (Flower)
- [ ] Monitor task failure rates
- [ ] Log serialization errors
- [ ] Set up alerts for task failures

## Common Solutions

### 15. Version Compatibility
```bash
# Update to compatible versions
pip install "celery>=5.3.0" "redis>=4.0.0"
```

### 16. Configuration Override
```python
# Force JSON serialization
app.conf.update(
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    task_ignore_result=False,
    task_store_errors_even_if_ignored=True,
    task_remote_tracebacks=True
)
```

### 17. Environment Variables
```bash
# Set environment variables
export CELERY_TASK_SERIALIZER=json
export CELERY_RESULT_SERIALIZER=json
export CELERY_ACCEPT_CONTENT=json
```

## Final Verification

### 18. Test All Task Types
- [ ] Success tasks
- [ ] Exception tasks
- [ ] Long-running tasks
- [ ] Tasks with complex results

### 19. Integration Testing
- [ ] Test with full application stack
- [ ] Verify API endpoints work correctly
- [ ] Check task status endpoints
- [ ] Monitor system performance

### 20. Documentation
- [ ] Update task documentation
- [ ] Document exception handling patterns
- [ ] Create troubleshooting guide
- [ ] Update deployment procedures

---

**Note**: This checklist should be followed in order. Each step builds on the previous ones to systematically identify and resolve Celery serialization issues. 