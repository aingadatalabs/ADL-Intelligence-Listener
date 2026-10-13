import os

from celery import Celery

# Enterprise configuration with strict fallback and environment overrides
DEFAULT_BROKER = "redis://localhost:6379/0"
DEFAULT_BACKEND = "redis://localhost:6379/1"

app = Celery(
    "adl_listener",
    broker=os.getenv("CELERY_BROKER_URL", DEFAULT_BROKER),
    backend=os.getenv("CELERY_RESULT_BACKEND", DEFAULT_BACKEND),
    include=["celery_worker.tasks"],
)

app.conf.update(
    task_routes={
        "celery_worker.tasks.*": {"queue": "scrapes"},
    },
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    broker_connection_retry_on_startup=True,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,
    result_expires=3600,
)