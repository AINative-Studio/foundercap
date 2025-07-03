"""Health check endpoints."""
from typing import Any, Dict, List

from fastapi import APIRouter, Depends

from app.core.scheduler import get_scheduler

router = APIRouter()


@router.get("/health")
async def health_check() -> Dict[str, str]:
    """Basic health check endpoint.

    Returns:
        A simple status message.
    """
    return {"status": "ok"}


@router.get("/health/services")
async def services_health() -> Dict[str, List[Dict[str, Any]] | None]:
    """Check the health of all services.

    Returns:
        A dictionary containing the health status of all services.
    """
    # Get scheduler health
    scheduler = await get_scheduler()
    scheduler_health = {
        "name": "scheduler",
        "status": "running" if scheduler.scheduler and scheduler.scheduler.running else "stopped",
    }

    # TODO: Add health checks for other services as they're implemented
    services = [scheduler_health]

    return {"services": services}
