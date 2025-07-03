"""Background task scheduler for periodic jobs."""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Callable, Coroutine, Dict, Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler

logger = logging.getLogger(__name__)


class Scheduler:
    """Background task scheduler for periodic jobs."""

    def __init__(self):
        """Initialize the scheduler."""
        self.scheduler: Optional[AsyncIOScheduler] = None
        self.jobs: Dict[str, Any] = {}

    async def start(self) -> None:
        """Start the scheduler."""
        if self.scheduler and self.scheduler.running:
            logger.warning("Scheduler is already running")
            return

        logger.info("Starting scheduler...")
        self.scheduler = AsyncIOScheduler()
        self.scheduler.start()
        logger.info("Scheduler started")

    async def stop(self) -> None:
        """Stop the scheduler."""
        if not self.scheduler or not self.scheduler.running:
            logger.warning("Scheduler is not running")
            return

        logger.info("Stopping scheduler...")
        self.scheduler.shutdown()
        self.scheduler = None
        logger.info("Scheduler stopped")

    async def add_job(
        self,
        func: Callable[..., Coroutine[Any, Any, None]],
        job_id: str,
        *,
        seconds: Optional[int] = None,
        minutes: Optional[int] = None,
        hours: Optional[int] = None,
        **kwargs: Any,
    ) -> None:
        """Add a job to the scheduler.

        Args:
            func: The coroutine function to run.
            job_id: Unique identifier for the job.
            seconds: Interval in seconds between job runs.
            minutes: Interval in minutes between job runs.
            hours: Interval in hours between job runs.
            **kwargs: Additional arguments to pass to the job function.
        """
        if not self.scheduler:
            raise RuntimeError("Scheduler is not running")

        if job_id in self.jobs:
            logger.warning("Job %s already exists, removing it first", job_id)
            await self.remove_job(job_id)

        interval = {
            "seconds": seconds or 0,
            "minutes": minutes or 0,
            "hours": hours or 0,
        }

        # Calculate total seconds for logging
        total_seconds = (
            (interval["hours"] * 3600)
            + (interval["minutes"] * 60)
            + interval["seconds"]
        )

        if total_seconds <= 0:
            raise ValueError("At least one time interval must be greater than 0")

        logger.info(
            "Adding job %s to run every %s seconds",
            job_id,
            total_seconds,
        )

        # Schedule the job
        job = self.scheduler.add_job(
            func,
            "interval",
            id=job_id,
            **interval,
            **kwargs,
        )
        self.jobs[job_id] = job
        logger.info("Job %s scheduled successfully", job_id)

    async def remove_job(self, job_id: str) -> None:
        """Remove a job from the scheduler.

        Args:
            job_id: The ID of the job to remove.
        """
        if not self.scheduler:
            raise RuntimeError("Scheduler is not running")

        if job_id not in self.jobs:
            logger.warning("Job %s not found", job_id)
            return

        logger.info("Removing job %s", job_id)
        self.scheduler.remove_job(job_id)
        self.jobs.pop(job_id, None)
        logger.info("Job %s removed", job_id)

    async def get_next_run_time(self, job_id: str) -> Optional[datetime]:
        """Get the next run time for a job.

        Args:
            job_id: The ID of the job.

        Returns:
            The next run time or None if the job is not found.
        """
        if not self.scheduler or job_id not in self.jobs:
            return None

        job = self.jobs[job_id]
        return job.next_run_time

    async def get_jobs(self) -> Dict[str, Any]:
        """Get all scheduled jobs.

        Returns:
            A dictionary of job IDs to job objects.
        """
        return self.jobs.copy()


# Global scheduler instance
scheduler = Scheduler()


async def get_scheduler() -> Scheduler:
    """Get the global scheduler instance.

    Returns:
        The global scheduler instance.
    """
    return scheduler
