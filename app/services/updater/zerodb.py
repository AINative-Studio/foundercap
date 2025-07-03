import logging
from typing import Any, Dict, List, Optional

import httpx

from app.core.config import settings
from app.services.updater.base import BaseUpdater

logger = logging.getLogger(__name__)


class ZeroDBUpdater(BaseUpdater):
    """Updater for ZeroDB company data."""

    def __init__(self):
        """Initialize the ZeroDB updater."""
        super().__init__()
        self._client: Optional[httpx.AsyncClient] = None

    @property
    def name(self) -> str:
        """Return the name of the updater."""
        return "zerodb"

    async def _initialize(self) -> None:
        """Initialize the ZeroDB updater."""
        if not settings.ZERODB_API_KEY or not settings.ZERODB_API_URL:
            raise ValueError("ZERODB_API_KEY and ZERODB_API_URL are required")

        self._client = httpx.AsyncClient(
            base_url=settings.ZERODB_API_URL,
            headers={
                "X-API-Key": settings.ZERODB_API_KEY,
                "Content-Type": "application/json",
            },
            timeout=30.0,
        )
        logger.info("ZeroDB updater initialized")

    async def _shutdown(self) -> None:
        """Shut down the ZeroDB updater."""
        if self._client:
            await self._client.aclose()
            self._client = None
        logger.info("ZeroDB updater shut down")

    async def update(self, company_id: str, data: Dict[str, Any], **kwargs: Any) -> Dict[str, Any]:
        """Upsert data for a company in ZeroDB.

        Args:
            company_id: The ID of the company to update.
            data: The data to upsert. This should be the full enriched company record.
            **kwargs: Additional arguments (not used for ZeroDB upsert).

        Returns:
            A dictionary containing the upsert result.

        Raises:
            httpx.HTTPError: If API request fails.
        """
        if not self._client:
            raise RuntimeError("ZeroDB updater not initialized")

        try:
            payload = {"id": company_id, "data": data}
            response = await self._client.post("/records", json=payload)
            response.raise_for_status()
            logger.info(f"Successfully upserted ZeroDB record {company_id}")
            return await response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error upserting ZeroDB record {company_id}: {e}")
            raise
        except httpx.RequestError as e:
            logger.error(f"Request error upserting ZeroDB record {company_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error upserting ZeroDB record {company_id}: {e}")
            raise

    async def invalidate_cache(self, company_ids: List[str]) -> Dict[str, Any]:
        """Invalidate cached entries for one or more record IDs in ZeroDB.

        Args:
            company_ids: A list of company IDs whose cache entries should be invalidated.

        Returns:
            A dictionary containing the cache invalidation result.

        Raises:
            httpx.HTTPError: If API request fails.
        """
        if not self._client:
            raise RuntimeError("ZeroDB updater not initialized")

        try:
            payload = {"recordIds": company_ids}
            response = await self._client.post("/cache/invalidate", json=payload)
            response.raise_for_status()
            logger.info(f"Successfully invalidated cache for {len(company_ids)} records")
            return await response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error invalidating ZeroDB cache: {e}")
            raise
        except httpx.RequestError as e:
            logger.error(f"Request error invalidating ZeroDB cache: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error invalidating ZeroDB cache: {e}")
            raise
