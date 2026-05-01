from __future__ import annotations

from celery import Celery

from config import settings

celery_app = Celery(
    "ai_research",
    broker=settings.celery_broker_url,
    backend=settings.celery_broker_url,
    include=["ingestion.worker"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
)
