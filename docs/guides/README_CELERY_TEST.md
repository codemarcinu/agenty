# Minimal Celery Test Project

This directory contains a minimal Celery test project to isolate and debug serialization issues.

## Files

- `test_celery_minimal.py` - Main test script with various Celery task types
- `run_celery_test.sh` - Automated test runner with setup/cleanup
- `README_CELERY_TEST.md` - This documentation

## Usage

### Quick Test
```bash
./run_celery_test.sh
```

### Manual Test
1. Start Redis:
   ```bash
   docker run -d --name test-redis -p 6379:6379 redis:7-alpine
   ```

2. Start Celery worker:
   ```bash
   celery -A test_celery_minimal worker --loglevel=info
   ```

3. Run test in another terminal:
   ```bash
   python test_celery_minimal.py
   ```

4. Cleanup:
   ```bash
   docker stop test-redis && docker rm test-redis
   ```

## Test Cases

The test script runs 4 different task types:

1. **Success Task** - Returns a simple JSON object
2. **Standard Exception Task** - Raises `RuntimeError`
3. **Custom Exception Task** - Raises a custom exception class
4. **Complex Return Task** - Returns an object with datetime

## Expected Results

- ✅ Success task should work
- ✅ Standard exception task should work (exception properly serialized)
- ❌ Custom exception task might fail (non-serializable)
- ❌ Complex return task might fail (datetime not JSON-serializable)

## Troubleshooting

If you see `Exception information must include the exception type`:

1. Check Celery and Redis versions
2. Ensure all dependencies are up to date
3. Try different result backends (redis://, rpc://)
4. Check for non-serializable objects in task results

## Integration with Main Project

This test helps determine if the serialization issue is:
- **Project-specific** (main project has custom code causing issues)
- **Environment-specific** (Celery/Redis configuration problem)
- **Version-specific** (incompatible library versions)

Run this test first before debugging the main project's Celery issues. 