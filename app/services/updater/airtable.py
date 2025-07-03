import logging
from typing import Any, Dict, Optional

import httpx

from app.core.config import settings
from app.services.updater.base import BaseUpdater

logger = logging.getLogger(__name__)


class AirtableUpdater(BaseUpdater):
    """Updater for Airtable company data."""

    def __init__(self):
        """Initialize the Airtable updater."""
        super().__init__()
        self._client: Optional[httpx.AsyncClient] = None

    @property
    def name(self) -> str:
        """Return the name of the updater."""
        return "airtable"

    async def _initialize(self) -> None:
        """Initialize the Airtable updater."""
        if not settings.AIRTABLE_API_KEY or not settings.AIRTABLE_BASE_ID or not settings.AIRTABLE_TABLE_NAME:
            raise ValueError("AIRTABLE_API_KEY, AIRTABLE_BASE_ID, and AIRTABLE_TABLE_NAME are required")

        self._client = httpx.AsyncClient(
            base_url=f"https://api.airtable.com/v0/{settings.AIRTABLE_BASE_ID}/",
            headers={
                "Authorization": f"Bearer {settings.AIRTABLE_API_KEY}",
                "Content-Type": "application/json",
            },
            timeout=30.0,
        )
        logger.info("Airtable updater initialized")

    async def _shutdown(self) -> None:
        """Shut down the Airtable updater."""
        if self._client:
            await self._client.aclose()
            self._client = None
        logger.info("Airtable updater shut down")

    async def update(self, company_id: str, data: Dict[str, Any], **kwargs: Any) -> Dict[str, Any]:
        """Update data for a company in Airtable.

        Args:
            company_id: The ID of the company to update (Airtable record ID).
            data: The data to update. This should be a dictionary of field_name: value.
            **kwargs: Additional arguments (e.g., `typecast` for Airtable).

        Returns:
            A dictionary containing the update result.

        Raises:
            httpx.HTTPError: If API request fails.
        """
        if not self._client:
            raise RuntimeError("Airtable updater not initialized")

        try:
            # Airtable expects a specific format for PATCH requests
            payload = {
                "records": [
                    {
                        "id": company_id,
                        "fields": data
                    }
                ],
                "typecast": kwargs.get("typecast", False) # Allows updating fields with different types
            }

            response = await self._client.patch(settings.AIRTABLE_TABLE_NAME, json=payload)
            response.raise_for_status()
            logger.info(f"Successfully updated Airtable record {company_id}")
            return await response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error updating Airtable record {company_id}: {e}")
            raise
        except httpx.RequestError as e:
            logger.error(f"Request error updating Airtable record {company_id}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error updating Airtable record {company_id}: {e}")
            raise
