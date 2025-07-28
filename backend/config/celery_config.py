"""
Konfiguracja Celery dla zadań w tle
"""

import os

from celery import Celery

# Ustawienia Celery
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "rpc://")

# Konfiguracja Celery
celery_config = {
    "broker_url": CELERY_BROKER_URL,
    "result_backend": CELERY_RESULT_BACKEND,
    "task_serializer": "json",
    "accept_content": ["json"],
    "result_serializer": "json",
    "timezone": "Europe/Warsaw",
    "enable_utc": True,
    "task_track_started": True,
    "task_time_limit": 30 * 60,  # 30 minut
    "task_soft_time_limit": 25 * 60,  # 25 minut
    "worker_prefetch_multiplier": 1,
    "worker_max_tasks_per_child": 1000,
    "broker_connection_retry_on_startup": True,
    "broker_connection_retry": True,
    # Dodatkowe ustawienia dla poprawy serializacji
    "result_expires": 3600,  # 1 godzina
    "result_persistent": False,  # Nie zapisuj wyników na dysku
    "task_ignore_result": False,
    "task_store_errors_even_if_ignored": True,
    "worker_disable_rate_limits": False,
    "worker_send_task_events": True,
    "task_send_sent_event": True,
    # Ustawienia dla lepszej obsługi wyjątków
    "task_remote_tracebacks": True,
    "worker_redirect_stdouts": False,
    "worker_redirect_stdouts_level": "WARNING",
}

# Inicjalizacja aplikacji Celery
celery_app = Celery("foodsave_ai")

# Ładowanie konfiguracji
celery_app.conf.update(celery_config)

# Auto-discovery zadań - poprawione ścieżki
celery_app.autodiscover_tasks(
    ["src.backend.tasks", "src.tasks", "backend.tasks", "tasks"]
)

# Konfiguracja tasków
celery_app.conf.task_routes = {
    "src.backend.tasks.conversation_tasks.*": {"queue": "conversation"},
    "src.backend.tasks.notification_tasks.*": {"queue": "notifications"},
    "src.backend.tasks.receipt_tasks.*": {"queue": "receipts"},
    "src.tasks.conversation_tasks.*": {"queue": "conversation"},
    "src.tasks.notification_tasks.*": {"queue": "notifications"},
    "src.tasks.receipt_tasks.*": {"queue": "receipts"},
    "backend.tasks.conversation_tasks.*": {"queue": "conversation"},
    "backend.tasks.notification_tasks.*": {"queue": "notifications"},
    "backend.tasks.receipt_tasks.*": {"queue": "receipts"},
    "tasks.conversation_tasks.*": {"queue": "conversation"},
    "tasks.notification_tasks.*": {"queue": "notifications"},
    "tasks.receipt_tasks.*": {"queue": "receipts"},
}

# Konfiguracja kolejek
celery_app.conf.update(
    {
        "task_default_queue": "default",
        "task_default_exchange": "default",
        "task_default_routing_key": "default",
    }
)
