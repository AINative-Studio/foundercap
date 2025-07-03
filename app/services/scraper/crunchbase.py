"""Crunchbase scraper implementation."""
import asyncio
import time
from typing import Any, Dict, List, Optional
import logging

import httpx
from pydantic import BaseModel

from app.core.config import settings
from app.services.scraper.base import BaseScraper


logger = logging.getLogger(__name__)


class CrunchbaseCompanyData(BaseModel):
    """Crunchbase company data model."""
    total_funding: Optional[int] = None
    funding_stage: Optional[str] = None
    investors: List[str] = []
    website: Optional[str] = None
    description: Optional[str] = None
    linkedin_url: Optional[str] = None
    logo_url: Optional[str] = None


class CrunchbaseScraper(BaseScraper):
    """Scraper for Crunchbase company data."""

    def __init__(self):
        """Initialize the Crunchbase scraper."""
        super().__init__()
        self._client: Optional[httpx.AsyncClient] = None
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._last_request_time = 0
        self._rate_limit_delay = settings.CRUNCHBASE_RATE_LIMIT_DELAY
        self._max_retries = settings.CRUNCHBASE_MAX_RETRIES
        self._backoff_factor = settings.CRUNCHBASE_BACKOFF_FACTOR

    @property
    def name(self) -> str:
        """Return the name of the scraper."""
        return "crunchbase"

    async def _initialize(self) -> None:
        """Initialize the Crunchbase scraper."""
        if not settings.CRUNCHBASE_API_KEY:
            raise ValueError("CRUNCHBASE_API_KEY is required")
        
        self._client = httpx.AsyncClient(
            base_url="https://api.crunchbase.com/api/v4",
            headers={
                "X-cb-user-key": settings.CRUNCHBASE_API_KEY,
                "Content-Type": "application/json",
            },
            timeout=30.0,
        )
        logger.info("Crunchbase scraper initialized")

    async def _shutdown(self) -> None:
        """Shut down the Crunchbase scraper."""
        if self._client:
            await self._client.aclose()
            self._client = None
        logger.info("Crunchbase scraper shut down")

    async def _rate_limit_wait(self) -> None:
        """Wait for rate limiting."""
        current_time = time.time()
        elapsed = current_time - self._last_request_time
        if elapsed < self._rate_limit_delay:
            wait_time = self._rate_limit_delay - elapsed
            logger.debug(f"Rate limiting: waiting {wait_time:.2f} seconds")
            await asyncio.sleep(wait_time)
        self._last_request_time = time.time()

    async def _handle_rate_limit_error(self, response: httpx.Response) -> None:
        """Handle rate limit errors with exponential backoff."""
        if response.status_code == 429:
            retry_after = response.headers.get("Retry-After")
            if retry_after:
                wait_time = int(retry_after)
            else:
                # Exponential backoff
                self._rate_limit_delay = min(self._rate_limit_delay * 2, 60)
                wait_time = self._rate_limit_delay
            
            logger.warning(f"Rate limited, waiting {wait_time} seconds")
            await asyncio.sleep(wait_time)

    async def fetch_crunchbase(self, permalink: str) -> CrunchbaseCompanyData:
        """Fetch company data from Crunchbase API.
        
        Args:
            permalink: The Crunchbase permalink/identifier for the company
            
        Returns:
            CrunchbaseCompanyData with normalized funding information
            
        Raises:
            ValueError: If permalink is empty or invalid
            httpx.HTTPError: If API request fails
        """
        if not permalink or not permalink.strip():
            raise ValueError("Permalink cannot be empty")
        
        permalink = permalink.strip()
        
        # Check cache first
        if permalink in self._cache:
            cached_data = self._cache[permalink]
            logger.debug(f"Returning cached data for {permalink}")
            return CrunchbaseCompanyData(**cached_data)

        if not self._client:
            raise RuntimeError("Scraper not initialized")

        # Prepare API request
        endpoint = f"/entities/organizations/{permalink}"
        params = {
            "field_ids": [
                "funding_total",
                "funding_stage",
                "investor_identifiers",
                "investors",
                "website_url",
                "short_description",
                "linkedin",
                "profile_image_url",
            ]
        }

        for attempt in range(self._max_retries):
            try:
                await self._rate_limit_wait()
                
                response = await self._client.get(endpoint, params=params)
                
                if response.status_code == 429:
                    await self._handle_rate_limit_error(response)
                    continue
                
                if response.status_code == 404:
                    logger.warning(f"Company not found: {permalink}")
                    return CrunchbaseCompanyData()
                
                response.raise_for_status()
                data = await response.json()
                
                # Parse response and normalize data
                company_data = self._parse_company_data(data)
                
                # Cache the result
                self._cache[permalink] = company_data.model_dump()
                
                logger.info(f"Successfully fetched data for {permalink}")
                return company_data
                
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429 and attempt < self._max_retries - 1:
                    await self._handle_rate_limit_error(e.response)
                    continue
                logger.error(f"HTTP error fetching {permalink}: {e}")
                raise
            except httpx.RequestError as e:
                if attempt < self._max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff for network errors
                    logger.warning(f"Request error, retrying in {wait_time}s: {e}")
                    await asyncio.sleep(wait_time)
                    continue
                logger.error(f"Request error fetching {permalink}: {e}")
                # Do not re-raise here, let the final RuntimeError handle it
            except Exception as e:
                logger.error(f"Unexpected error fetching {permalink}: {e}")
                raise

        raise RuntimeError(f"Failed to fetch data after {self._max_retries} attempts")

    def _parse_company_data(self, data: Dict[str, Any]) -> CrunchbaseCompanyData:
        """Parse Crunchbase API response into normalized data.
        
        Args:
            data: Raw API response data
            
        Returns:
            CrunchbaseCompanyData with normalized fields
        """
        try:
            properties = data.get("properties", {})
            
            # Extract funding total
            total_funding = None
            funding_total = properties.get("funding_total")
            if funding_total and isinstance(funding_total, dict):
                if "value_usd" in funding_total:
                    total_funding = funding_total["value_usd"]
                elif "value" in funding_total:
                    total_funding = funding_total["value"]
            
            # Extract funding stage
            funding_stage = properties.get("funding_stage")
            
            # Extract investors
            investors = []
            investor_data = properties.get("investors", [])
            if isinstance(investor_data, list):
                for investor in investor_data:
                    if isinstance(investor, dict):
                        name = investor.get("name") or investor.get("identifier", {}).get("value")
                        if name:
                            investors.append(name)
            
            # Extract website, description, linkedin, and logo
            website = properties.get("website_url")
            description = properties.get("short_description")
            linkedin_data = properties.get("linkedin")
            linkedin_url = linkedin_data.get("value") if isinstance(linkedin_data, dict) else None
            logo_url = properties.get("profile_image_url")

            return CrunchbaseCompanyData(
                total_funding=total_funding,
                funding_stage=funding_stage,
                investors=investors,
                website=website,
                description=description,
                linkedin_url=linkedin_url,
                logo_url=logo_url,
            )
            
        except Exception as e:
            logger.error(f"Error parsing company data: {e}")
            return CrunchbaseCompanyData()

    async def scrape(self, company_name: str, **kwargs: Any) -> Dict[str, Any]:
        """Scrape data for a company using Crunchbase.
        
        Args:
            company_name: The name of the company (used as permalink if not provided)
            **kwargs: Additional arguments, may include 'permalink'
            
        Returns:
            Dictionary containing scraped company data
        """
        permalink = kwargs.get("permalink", company_name.lower().replace(" ", "-"))
        
        try:
            data = await self.fetch_crunchbase(permalink)
            return {
                "source": "crunchbase",
                "company_name": company_name,
                "permalink": permalink,
                "data": data.model_dump(),
                "scraped_at": time.time(),
            }
        except Exception as e:
            logger.error(f"Failed to scrape {company_name}: {e}")
            return {
                "source": "crunchbase",
                "company_name": company_name,
                "permalink": permalink,
                "data": CrunchbaseCompanyData().model_dump(),
                "error": str(e),
                "scraped_at": time.time(),
            }

    def clear_cache(self) -> None:
        """Clear the local cache."""
        self._cache.clear()
        logger.info("Cache cleared")

    def get_cache_size(self) -> int:
        """Get the current cache size."""
        return len(self._cache)