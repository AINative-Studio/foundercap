"""Dependencies for Crunchbase API endpoints."""
from typing import Generator, AsyncGenerator
from fastapi import Depends, HTTPException, status

from app.services.crunchbase import (
    CrunchbaseService,
    get_crunchbase_service,
    close_crunchbase_service,
    CrunchbaseConfig
)
from app.core.config import settings

async def get_crunchbase() -> AsyncGenerator[CrunchbaseService, None]:
    """Dependency that provides a Crunchbase service instance.
    
    Yields:
        CrunchbaseService: An instance of CrunchbaseService
    """
    if not settings.CRUNCHBASE_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Crunchbase integration is not configured"
        )
    
    config = CrunchbaseConfig(
        api_key=settings.CRUNCHBASE_API_KEY,
        requests_per_second=settings.CRUNCHBASE_REQUESTS_PER_SECOND,
        max_retries=settings.CRUNCHBASE_MAX_RETRIES,
        request_timeout=settings.CRUNCHBASE_REQUEST_TIMEOUT,
        connect_timeout=settings.CRUNCHBASE_CONNECT_TIMEOUT,
    )
    
    service = get_crunchbase_service(config=config)
    try:
        yield service
    finally:
        await service.close()

# Common dependency for all Crunchbase endpoints
CrunchbaseDep = Depends(get_crunchbase)
