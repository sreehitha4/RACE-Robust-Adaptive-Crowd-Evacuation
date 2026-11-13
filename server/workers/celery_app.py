"""Optional Celery worker for offline preprocessing and evaluation jobs."""
import os
from celery import Celery

broker = os.getenv("RACE_CELERY_BROKER_URL", os.getenv("RACE_REDIS_URL", "redis://redis:6379/1"))
backend = os.getenv("RACE_CELERY_RESULT_BACKEND", os.getenv("RACE_REDIS_URL", "redis://redis:6379/2"))
celery_app = Celery("race_workers", broker=broker, backend=backend, include=["server.workers.tasks"])
celery_app.conf.update(task_track_started=True, task_serializer="json", result_serializer="json",
                       accept_content=["json"], timezone="UTC", enable_utc=True,
                       task_acks_late=True, worker_prefetch_multiplier=1)
