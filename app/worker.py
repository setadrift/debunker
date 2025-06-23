import os

from celery import Celery

BROKER_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
celery_app = Celery("ii_tasks", broker=BROKER_URL, backend=BROKER_URL)
celery_app.conf.task_routes = {"app.tasks.*": {"queue": "default"}}
