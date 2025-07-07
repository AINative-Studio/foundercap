"""
LinkedIn API Client for fetching company data.

This module provides an asynchronous client for interacting with the LinkedIn API
to fetch company profile data. It handles authentication, rate limiting, and error handling.
"""
import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Union, Any
from urllib.parse import urljoin, quote_plus

import httpx
from pydantic import HttpUrl, ValidationError

from app.core.config import settings
from app.core.redis import get_redis
from app.services.linkedin.models import LinkedInCompany, CompanySize, CompanyType

logger = logging.getLogger(__name__)

class LinkedInAPIError(Exception):
    """Base exception for LinkedIn API errors."""
    pass

class RateLimitExceeded(LinkedInAPIError):
    """Raised when LinkedIn API rate limits are exceeded."""
    pass

class LinkedInClient:
    """
    Asynchronous client for the LinkedIn API.
    
    Handles authentication, request throttling, and error handling.
    """
    BASE_URL = "https://api.linkedin.com/v2/"
    
    def __init__(
        self, 
        access_token: Optional[str] = None,
        rate_limit_delay: float = 1.0,
        max_retries: int = 3,
        cache_ttl: int = 86400  # 24 hours
    ):
        """
        Initialize the LinkedIn client.
        
        Args:
            access_token: LinkedIn API access token. If not provided, will use settings.
            rate_limit_delay: Delay between API requests in seconds.
            max_retries: Maximum number of retry attempts for failed requests.
            cache_ttl: Time-to-live for cached responses in seconds.
        """
        self.access_token = access_token or settings.LINKEDIN_API_KEY
        self.rate_limit_delay = rate_limit_delay
        self.max_retries = max_retries
        self.cache_ttl = cache_ttl
        self.redis = get_redis()
        self._last_request_time = 0
        
        if not self.access_token:
            logger.warning(
                "No LinkedIn API access token provided. "
                "Set LINKEDIN_API_KEY in your environment variables."
            )
    
    async def _get_headers(self) -> Dict[str, str]:
        """Get headers for API requests."""
        return {
            "Authorization": f"Bearer {self.access_token}",
            "X-Restli-Protocol-Version": "2.0.0",
            "Content-Type": "application/json",
        }
    
    async def _rate_limit(self):
        """Enforce rate limiting between requests."""
        now = datetime.now().timestamp()
        time_since_last = now - self._last_request_time
        
        if time_since_last < self.rate_limit_delay:
            delay = self.rate_limit_delay - time_since_last
            await asyncio.sleep(delay)
        
        self._last_request_time = datetime.now().timestamp()
    
    async def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        params: Optional[Dict] = None,
        data: Optional[Dict] = None,
        use_cache: bool = True
    ) -> Dict:
        """
        Make an HTTP request to the LinkedIn API.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (without base URL)
            params: Query parameters
            data: Request body
            use_cache: Whether to use cached responses if available
            
        Returns:
            Dict containing the JSON response
            
        Raises:
            RateLimitExceeded: If rate limited by the API
            LinkedInAPIError: For other API errors
        """
        url = urljoin(self.BASE_URL, endpoint)
        cache_key = f"linkedin:request:{method}:{endpoint}:{json.dumps(params or {})}"
        
        # Try to get from cache
        if use_cache and method.upper() == "GET":
            cached = await self.redis.get(cache_key)
            if cached:
                try:
                    return json.loads(cached)
                except json.JSONDecodeError:
                    logger.warning(f"Failed to decode cached response for {cache_key}")
        
        # Enforce rate limiting
        await self._rate_limit()
        
        # Prepare request
        headers = await self._get_headers()
        
        for attempt in range(self.max_retries):
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.request(
                        method=method,
                        url=url,
                        params=params,
                        json=data,
                        headers=headers,
                        timeout=30.0
                    )
                
                # Handle rate limiting
                if response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", 60))
                    logger.warning(
                        f"Rate limited. Retrying after {retry_after} seconds. "
                        f"Attempt {attempt + 1}/{self.max_retries}"
                    )
                    await asyncio.sleep(retry_after)
                    continue
                
                response.raise_for_status()
                result = response.json()
                
                # Cache successful responses
                if method.upper() == "GET" and response.status_code == 200:
                    await self.redis.set(
                        cache_key, 
                        json.dumps(result),
                        ex=self.cache_ttl
                    )
                
                return result
                
            except httpx.HTTPError as e:
                logger.error(f"HTTP error: {e}")
                if attempt == self.max_retries - 1:
                    raise LinkedInAPIError(f"API request failed after {self.max_retries} attempts: {e}")
                
                # Exponential backoff
                await asyncio.sleep(2 ** attempt)
        
        raise LinkedInAPIError("Max retries exceeded")
    
    async def get_company_by_domain(self, domain: str) -> Optional[LinkedInCompany]:
        """
        Get company details by domain name.
        
        Args:
            domain: Company domain (e.g., 'google.com')
            
        Returns:
            LinkedInCompany object if found, None otherwise
        """
        try:
            # First try to find by domain
            params = {
                "q": "companySearch",
                "companySearch": {
                    "keyword": domain,
                    "queryContext": {
                        "company": ["universalName", "name", "website", "employeeCountRange", "companyType"]
                    }
                },
                "count": 1
            }
            
            response = await self._make_request(
                "GET", 
                "search",
                params=params
            )
            
            if not response.get("elements"):
                return None
                
            # Get the first result
            company_data = response["elements"][0]
            
            # Get more detailed information
            company_id = company_data.get("targetUrn").split(":")[-1]
            return await self.get_company(company_id)
            
        except Exception as e:
            logger.error(f"Error getting company by domain {domain}: {e}")
            return None
    
    async def get_company(self, company_id: str) -> Optional[LinkedInCompany]:
        """
        Get detailed company information by LinkedIn company ID.
        
        Args:
            company_id: LinkedIn company URN (e.g., '12345')
            
        Returns:
            LinkedInCompany object if found, None otherwise
        """
        try:
            # Get basic company info
            company_info = await self._make_request(
                "GET",
                f"organizations/{company_id}?projection=(
                    id,
                    name,
                    universalName,
                    website,
                    description,
                    tagline,
                    companySize,
                    staffCount,
                    foundedOn,
                    companyType,
                    localizedWebsite,
                    logoV2,
                    group,
                    locations,
                    specialities,
                    industries,
                    employeeCountRange,
                    locationDescription,
                    descriptionLocalized,
                    vanityName
                )"
            )
            
            # Get additional fields
            locations = []
            if company_info.get("locations"):
                locations_data = await self._make_request(
                    "GET",
                    f"organizations/{company_id}/locations?count=100"
                )
                locations = [
                    {
                        "name": loc.get("name"),
                        "city": loc.get("city"),
                        "country": loc.get("country"),
                        "is_headquarters": loc.get("isHeadquarters", False),
                        "address": loc.get("line1"),
                        "postal_code": loc.get("postalCode"),
                        "region": loc.get("geographicArea"),
                        "description": loc.get("description"),
                    }
                    for loc in locations_data.get("elements", [])
                ]
            
            # Find headquarters
            headquarters = next(
                (loc for loc in locations if loc.get("is_headquarters")),
                {}
            )
            
            # Parse employee count range
            employee_count = None
            company_size = None
            if company_info.get("employeeCountRange"):
                employee_count = company_info["employeeCountRange"].get("end")
                company_size = self._map_employee_count_to_size(employee_count)
            
            # Build company object
            company = LinkedInCompany(
                linkedin_id=company_info.get("id"),
                universal_name=company_info.get("vanityName") or company_info.get("universalName"),
                name=company_info.get("name"),
                website=company_info.get("website") or company_info.get("localizedWebsite"),
                description=company_info.get("description") or company_info.get("descriptionLocalized", {}).get("en_US"),
                tagline=company_info.get("tagline"),
                company_size=company_size,
                employee_count=employee_count,
                company_type=company_info.get("companyType"),
                headquarters=(
                    f"{headquarters.get('city', '')}, {headquarters.get('country', '')}".strip(", ") 
                    if headquarters else None
                ),
                locations=locations,
                founded_year=int(company_info.get("foundedOn", {}).get("year")) if company_info.get("foundedOn") else None,
                linkedin_url=f"https://www.linkedin.com/company/{company_info.get('vanityName') or company_info.get('id')}",
                raw_data=company_info
            )
            
            return company
            
        except Exception as e:
            logger.error(f"Error getting company {company_id}: {e}")
            return None
    
    def _map_employee_count_to_size(self, count: Optional[int]) -> str:
        """Map employee count to CompanySize enum."""
        if not count:
            return None
            
        if count == 1:
            return CompanySize.SELF_EMPLOYED
        elif 2 <= count <= 10:
            return CompanySize.ONE_TO_10_EMPLOYEES
        elif 11 <= count <= 50:
            return CompanySize.ELEVEN_TO_50_EMPLOYEES
        elif 51 <= count <= 200:
            return CompanySize.FIFTY_ONE_TO_200_EMPLOYEES
        elif 201 <= count <= 500:
            return CompanySize.TWO_HUNDRED_ONE_TO_500_EMPLOYEES
        elif 501 <= count <= 1000:
            return CompanySize.FIVE_HUNDRED_ONE_TO_1000_EMPLOYEES
        elif 1001 <= count <= 5000:
            return CompanySize.ONE_THOUSAND_ONE_TO_5000_EMPLOYEES
        else:
            return CompanySize.FIVE_THOUSAND_ONE_PLUS_EMPLOYEES
