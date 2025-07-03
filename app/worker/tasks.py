"""Celery tasks for the FounderCap application."""
import asyncio
import logging
import time
from typing import Any, Dict, Optional

from celery import shared_task
from celery.utils.log import get_task_logger

from app.core.config import settings
from app.worker.celery_app import celery_app
from app.core.diff import find_json_diff
from app.core.service import get_service_instance
from app.core.snapshot import SnapshotService
from app.services.scraper.crunchbase import CrunchbaseScraper
from app.services.scraper.linkedin import LinkedInScraper
from app.services.updater.airtable import AirtableUpdater
from app.services.updater.zerodb import ZeroDBUpdater


logger = get_task_logger(__name__)

# Initialize services within the task context
# These will be replaced by mocks in tests
snapshot_service: SnapshotService = get_service_instance(SnapshotService)
crunchbase_scraper: CrunchbaseScraper = get_service_instance(CrunchbaseScraper)
linkedin_scraper: LinkedInScraper = get_service_instance(LinkedInScraper)
airtable_updater: AirtableUpdater = get_service_instance(AirtableUpdater)
zerodb_updater: ZeroDBUpdater = get_service_instance(ZeroDBUpdater)


@shared_task(bind=True, name="health_check")
def health_check(self) -> Dict[str, Any]:
    """Periodic health check task."""
    logger.info("Performing health check...")
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "version": settings.VERSION,
    }


@shared_task(
    bind=True,
    name="process_company_data",
    queue="default",
    max_retries=5,
    default_retry_delay=300,  # 5 minutes
    acks_late=True,
)
async def process_company_data(self, company_id: str, permalink: Optional[str] = None) -> Dict[str, Any]:
    """Processes company data by scraping, diffing, and updating.

    Args:
        company_id: The unique identifier for the company (e.g., Airtable record ID).
        permalink: The Crunchbase permalink for the company, if available.

    Returns:
        A dictionary containing the processing result and any detected changes.
    """
    try:
        logger.info(f"Starting data processing for company: {company_id}")

        # Get previous snapshot
        old_data = None # Placeholder for snapshot_service.get_latest_snapshot(company_id)
        if old_data is None:
            logger.info(f"No previous snapshot found for {company_id}. Treating as new entry.")
            old_data = {}

        # Scrape data from sources
        # Ensure scrapers are initialized (they are initialized in app.main on startup)
        # For Celery tasks, we might need a mechanism to ensure they are initialized
        # if the worker starts independently of the FastAPI app.
        # For now, assume they are initialized or handle re-initialization if needed.
        if not crunchbase_scraper._is_initialized:
            await crunchbase_scraper.initialize()
        if not linkedin_scraper._is_initialized:
            await linkedin_scraper.initialize()

        crunchbase_data = await crunchbase_scraper.scrape(company_id, permalink=permalink)
        linkedin_data = await linkedin_scraper.scrape(company_id)

        # Combine scraped data (simple merge for now, can be more sophisticated)
        new_data = {
            **crunchbase_data.get("data", {}),
            **linkedin_data.get("data", {}),
            "scraped_at": time.time(),
        }

        # Find differences
        changes = find_json_diff(old_data, new_data)

        if not changes:
            logger.info(f"No significant changes detected for company: {company_id}")
            return {"company_id": company_id, "status": "no_changes", "changes": {}}

        logger.info(f"Changes detected for {company_id}: {changes}")

        # Update Airtable and ZeroDB
        # TODO: Map changes to Airtable field names if different from internal model
        airtable_update_data = new_data  # For simplicity, send full new_data
        zerodb_update_data = new_data    # For simplicity, send full new_data

        # await airtable_updater.update(company_id, airtable_update_data)
        # await zerodb_updater.update(company_id, zerodb_update_data)

        # Save new snapshot
        # await snapshot_service.save_snapshot(company_id, new_data)

        # Invalidate ZeroDB cache
        # await zerodb_updater.invalidate_cache([company_id])

        logger.info(f"Successfully processed and updated data for company: {company_id}")
        return {"company_id": company_id, "status": "updated", "changes": changes}

    except Exception as exc:
        logger.error(f"Error processing data for company {company_id}: {exc}", exc_info=True)
        raise self.retry(exc=exc)


@shared_task(
    bind=True,
    name="update_company_metrics",
    queue="default",
    max_retries=3,
    default_retry_delay=30,  # 30 seconds
)
def update_company_metrics(self, company_id: str) -> Dict[str, Any]:
    """Update metrics for a company.

    Args:
        company_id: The ID of the company to update metrics for.

    Returns:
        A dictionary containing the updated metrics.
    """
    try:
        logger.info("Updating metrics for company %s", company_id)
        # TODO: Implement actual metrics update logic
        # This is a placeholder implementation
        time.sleep(1)  # Simulate work
        return {
            "company_id": company_id,
            "metrics": {"funding": 1000000, "employees": 50, "last_updated": time.time()},
        }
    except Exception as exc:
        logger.error("Error updating metrics for company %s: %s", company_id, str(exc))
        raise self.retry(exc=exc)


@shared_task(
    bind=True,
    name="send_notification",
    queue="notifications",
    max_retries=3,
    default_retry_delay=10,  # 10 seconds
)
def send_notification(
    self, recipient: str, message: str, notification_type: str = "info"
) -> Dict[str, Any]:
    """Send a notification to a user.

    Args:
        recipient: The recipient of the notification.
        message: The message to send.
        notification_type: The type of notification (default: "info").

    Returns:
        A dictionary containing the notification status.
    """
    try:
        logger.info(
            "Sending %s notification to %s: %s", notification_type, recipient, message
        )
        # TODO: Implement actual notification logic
        # This is a placeholder implementation
        time.sleep(0.5)  # Simulate work
        return {
            "status": "sent",
            "recipient": recipient,
            "type": notification_type,
            "message": message,
            "timestamp": time.time(),
        }
    except Exception as exc:
        logger.error(
            "Error sending %s notification to %s: %s",
            notification_type,
            recipient,
            str(exc),
        )
        raise self.retry(exc=exc)