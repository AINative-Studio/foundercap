"""Celery application configuration and task definitions."""
import logging
import asyncio
from typing import Any, Dict, Optional

from celery import Celery
from celery.signals import after_setup_logger, after_setup_task_logger, worker_process_init, worker_process_shutdown
from kombu import Queue, Exchange

from app.core.config import settings
from app.core.snapshot import SnapshotService
from app.services.updater.airtable import AirtableUpdater
from app.services.updater.zerodb import ZeroDBUpdater

# Configure logging
logger = logging.getLogger(__name__)

# Create Celery application
celery_app = Celery(
    "foundercap",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.worker.tasks"],
)

# Store service instances on the Celery app
celery_app.services = {}

@worker_process_init.connect
def initialize_services(sender, **kwargs):
    """Initialize services when Celery worker process starts."""
    sender.services["snapshot_service"] = SnapshotService()
    sender.services["airtable_updater"] = AirtableUpdater()
    sender.services["zerodb_updater"] = ZeroDBUpdater()

    # Manually run async initialization for services
    loop = asyncio.get_event_loop()
    loop.run_until_complete(sender.services["snapshot_service"].initialize())
    loop.run_until_complete(sender.services["airtable_updater"].initialize())
    loop.run_until_complete(sender.services["zerodb_updater"].initialize())

@worker_process_shutdown.connect
def shutdown_services(sender, **kwargs):
    """Shutdown services when Celery worker process shuts down."""
    loop = asyncio.get_event_loop()
    loop.run_until_complete(sender.services["snapshot_service"].shutdown())
    loop.run_until_complete(sender.services["airtable_updater"].shutdown())
    loop.run_until_complete(sender.services["zerodb_updater"].shutdown())

@celery_app.on_after_configure.connect
def setup_services(sender, **kwargs):
    """Initialize services after Celery app is configured."""
    sender.services["snapshot_service"] = SnapshotService()
    sender.services["airtable_updater"] = AirtableUpdater()
    sender.services["zerodb_updater"] = ZeroDBUpdater()



# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone=settings.TIMEZONE,
    enable_utc=True,
    task_default_queue="default",
    task_queues=(
        Queue(
            "default",
            Exchange("default"),
            routing_key="default",
            queue_arguments={"x-max-priority": 10},
        ),
        Queue(
            "scrapers",
            Exchange("scrapers"),
            routing_key="scrapers",
            queue_arguments={"x-max-priority": 5},
        ),
        Queue(
            "notifications",
            Exchange("notifications"),
            routing_key="notifications",
            queue_arguments={"x-max-priority": 3},
        ),
    ),
    task_default_exchange="default",
    task_default_routing_key="default",
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    broker_connection_retry_on_startup=True,
)

# Configure periodic tasks (Celery Beat)
celery_app.conf.beat_schedule = {
    "health-check-every-5-minutes": {
        "task": "app.worker.tasks.health_check",
        "schedule": 300.0,  # 5 minutes
    },
}


@after_setup_logger.connect
def setup_loggers(logger, *args, **kwargs):
    """Configure logging for Celery."""
    # Configure root logger
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


@after_setup_task_logger.connect
def setup_task_loggers(logger, *args, **kwargs):
    """Configure task logging for Celery."""
    # Configure task logger
    logger.setLevel(logging.INFO)


# Import tasks after Celery app is configured to avoid circular imports
# This must be at the end of the file
from app.worker import tasks  # noqa: E402, F401
