"""Crunchbase API client with rate limiting and retry logic."""
import time
import asyncio
import logging
from typing import Dict, Any, Optional, List, Union
from datetime import datetime, timedelta

import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)

from .exceptions import (
    CrunchbaseAPIError,
    CrunchbaseRateLimitError,
    CrunchbaseAuthError,
    CrunchbaseNotFoundError,
)
from .models import Company, FundingRound, CrunchbaseResponse
from .config import CrunchbaseConfig

logger = logging.getLogger(__name__)

class CrunchbaseClient:
    """Client for interacting with the Crunchbase API."""
    
    BASE_URL = "https://api.crunchbase.com/api/v4/"
    
    def __init__(self, config: Optional[CrunchbaseConfig] = None):
        """Initialize the Crunchbase API client.
        
        Args:
            config: Crunchbase configuration. If not provided, will be loaded from environment.
        """
        self.config = config or CrunchbaseConfig()
        self._last_request_time = 0
        self._min_request_interval = 1.0 / self.config.requests_per_second
        self._session = self._create_session()
    
    def _create_session(self) -> httpx.AsyncClient:
        """Create an HTTPX client session with default headers."""
        return httpx.AsyncClient(
            base_url=self.config.base_url,
            headers={
                "X-cb-user-key": self.config.api_key,
                "Content-Type": "application/json",
                "User-Agent": "FounderCap/1.0",
            },
            timeout=httpx.Timeout(
                connect=self.config.connect_timeout,
                read=self.config.request_timeout,
                write=None,
                pool=None,
            ),
        )
    
    async def _enforce_rate_limit(self):
        """Enforce rate limiting between requests."""
        now = time.time()
        time_since_last = now - self._last_request_time
        if time_since_last < self._min_request_interval:
            sleep_time = self._min_request_interval - time_since_last
            logger.debug("Rate limiting: sleeping for %.2f seconds", sleep_time)
            await asyncio.sleep(sleep_time)
        self._last_request_time = time.time()
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=(
            retry_if_exception_type((httpx.NetworkError, httpx.TimeoutException)) |
            retry_if_exception_type(CrunchbaseRateLimitError)
        ),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )
    async def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make an HTTP request to the Crunchbase API with rate limiting."""
        await self._enforce_rate_limit()
        
        url = f"{self.BASE_URL.rstrip('/')}/{endpoint.lstrip('/')}"
        logger.debug("Making %s request to %s", method, url)
        
        try:
            response = await self._session.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
                
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                raise CrunchbaseAuthError("Invalid or missing API key") from e
            elif e.response.status_code == 404:
                raise CrunchbaseNotFoundError(f"Resource not found: {url}") from e
            elif e.response.status_code == 429:
                retry_after = int(e.response.headers.get("Retry-After", 5))
                logger.warning("Rate limited. Waiting %s seconds", retry_after)
                time.sleep(retry_after)
                raise CrunchbaseRateLimitError("Rate limit exceeded") from e
            else:
                raise CrunchbaseAPIError(
                    f"API request failed with status {e.response.status_code}: {e.response.text}"
                ) from e
                
        except httpx.RequestError as e:
            raise CrunchbaseAPIError(f"Request failed: {str(e)}") from e
    
    async def get_company(self, identifier: str) -> Optional[Company]:
        """Get company details by permalink or UUID.
        
        Args:
            identifier: Company permalink (e.g., 'company/airbnb') or UUID
            
        Returns:
            Company object if found, None otherwise
        """
        try:
            endpoint = f"entities/organizations/{identifier}"
            params = {
                "field_ids": [
                    "identifier", "name", "short_description", "website", "founded_on",
                    "funding_total_usd", "last_funding_type", "last_funding_at"
                ]
            }
            
            data = await self._request("GET", endpoint, params=params)
            return Company(**data)
            
        except CrunchbaseNotFoundError:
            return None
    
    async def get_company_funding_rounds(self, company_id: str) -> List[FundingRound]:
        """Get all funding rounds for a company.
        
        Args:
            company_id: Crunchbase company UUID or permalink
            
        Returns:
            List of FundingRound objects
            
        Raises:
            CrunchbaseAPIError: If the API request fails
        """
        endpoint = f"entities/organizations/{company_id}/funding_rounds"
        params = {
            "field_ids": ["funding_rounds"]
        }
        
        response = await self._request("POST", endpoint, json=params)
        
        # Extract and normalize funding rounds
        rounds_data = response.get("entities", [])
        return [
            FundingRound(
                uuid=round_data.get("uuid"),
                name=round_data.get("name"),
                announced_on=round_data.get("announced_on"),
                money_raised=round_data.get("money_raised"),
                money_raised_currency=round_data.get("money_raised_currency"),
                investors=[
                    {
                        "uuid": inv.get("uuid"),
                        "name": inv.get("name"),
                        "type": inv.get("type")
                    }
                    for inv in round_data.get("investments", [])
                ]
            )
            for round_data in rounds_data
        ]
        
    async def get_funding_round_details(self, round_id: str) -> Optional[FundingRound]:
        """Get detailed information about a specific funding round.
        
        Args:
            round_id: Crunchbase funding round UUID
            
        Returns:
            FundingRound object with detailed information, or None if not found
            
        Raises:
            CrunchbaseAPIError: If the API request fails
        """
        endpoint = f"entities/funding_rounds/{round_id}"
        
        try:
            round_data = await self._request("GET", endpoint)
            
            return FundingRound(
                uuid=round_data.get("uuid"),
                name=round_data.get("name"),
                announced_on=round_data.get("announced_on"),
                money_raised=round_data.get("money_raised"),
                money_raised_currency=round_data.get("money_raised_currency"),
                investors=[
                    {
                        "uuid": inv.get("uuid"),
                        "name": inv.get("name"),
                        "type": inv.get("type")
                    }
                    for inv in round_data.get("investments", [])
                ],
                source_url=round_data.get("source_url"),
                source_description=round_data.get("source_description"),
                created_at=round_data.get("created_at"),
                updated_at=round_data.get("updated_at")
            )
        except CrunchbaseNotFoundError:
            return None
            
    async def get_investor_details(self, investor_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about an investor.
        
        Args:
            investor_id: Crunchbase investor UUID or permalink
            
        Returns:
            Dictionary with investor details, or None if not found
            
        Raises:
            CrunchbaseAPIError: If the API request fails
        """
        endpoint = f"entities/organizations/{investor_id}"
        
        try:
            return await self._request("GET", endpoint)
        except CrunchbaseNotFoundError:
            return None
    
    async def get_company_by_domain(self, domain: str) -> Optional[Company]:
        """Get company data by domain.
        
        Args:
            domain: Company domain (e.g., 'airbnb.com')
            
        Returns:
            Company object if found, None otherwise
        """
        try:
            # First, search for the company by domain
            search_url = f"{self.BASE_URL}searches/organizations"
            search_params = {
                "field_ids": ["identifier"],
                "query": [
                    {
                        "type": "predicate",
                        "field_id": "domain",
                        "operator_id": "eq",
                        "values": [domain]
                    }
                ]
            }
            
            response = await self._request(
                "POST",
                search_url,
                json=search_params
            )
            
            # Check if we found any results
            if not response.get("entities"):
                return None
                
            # Get the first result's UUID
            company_uuid = response["entities"][0]["identifier"]["uuid"]
            
            # Now get the full company data
            return await self.get_company(company_uuid)
            
        except CrunchbaseNotFoundError:
            return None
        except Exception as e:
            logger.error(f"Error getting company by domain {domain}: {e}")
            raise CrunchbaseAPIError(f"Failed to get company by domain: {e}")
    
    
    async def close(self):
        """Close the HTTP session."""
        if hasattr(self, '_session') and self._session:
            await self._session.aclose()
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
