#!/usr/bin/env python3
"""
Minimal Celery test project to isolate serialization issues.
Run this to test if the problem is with the main project or Celery/Redis configuration.
"""

import contextlib
import os
import time

from celery import Celery
import pytest

# Celery configuration
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")

# Create Celery app
app = Celery("test_celery_minimal")

# Configure Celery
app.conf.update(
    broker_url=CELERY_BROKER_URL,
    result_backend=CELERY_RESULT_BACKEND,
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Europe/Warsaw",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,
    task_soft_time_limit=25 * 60,
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    broker_connection_retry_on_startup=True,
    result_expires=3600,
    result_persistent=False,
    task_ignore_result=False,
    task_store_errors_even_if_ignored=True,
    worker_disable_rate_limits=False,
    worker_send_task_events=True,
    task_send_sent_event=True,
    task_remote_tracebacks=True,
    worker_redirect_stdouts=False,
    worker_redirect_stdouts_level="WARNING",
)


@app.task
def test_success_task():
    """Task that returns a successful result."""
    return {
        "status": "SUCCESS",
        "message": "Task completed successfully",
        "data": {"test": True},
    }


@app.task
def test_exception_task():
    """Task that raises a standard Python exception."""
    raise RuntimeError("Test exception for Celery serialization")


@app.task
def test_custom_exception_task():
    """Task that raises a custom exception (this should fail)."""

    class CustomError(Exception):
        pass

    raise CustomError("Custom exception test")


@app.task
def test_complex_return_task():
    """Task that returns a complex object (this might fail)."""
    from datetime import datetime

    return {
        "status": "SUCCESS",
        "timestamp": datetime.now(),
        "data": {"nested": {"deep": "value"}},
    }


def test_celery_serialization():
    """Test all task types to identify serialization issues."""

    # Test 1: Success task
    try:
        result = test_success_task.delay()
        time.sleep(2)
    except Exception:
        pass

    # Test 2: Standard exception task
    try:
        result = test_exception_task.delay()
        time.sleep(2)
        with contextlib.suppress(Exception):
            result.get()
    except Exception:
        pass

    # Test 3: Custom exception task
    try:
        result = test_custom_exception_task.delay()
        time.sleep(2)
        with contextlib.suppress(Exception):
            result.get()
    except Exception:
        pass

    # Test 4: Complex return task
    try:
        result = test_complex_return_task.delay()
        time.sleep(2)
    except Exception:
        pass


def test_celery_exception_handling():
    """Test that test_exception_task raises RuntimeError via Celery."""
    result = test_exception_task.delay()
    with pytest.raises(Exception):
        result.get(timeout=5)


if __name__ == "__main__":
    test_celery_serialization()
