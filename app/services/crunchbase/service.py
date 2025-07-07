"""Service layer for Crunchbase integration."""
from typing import Dict, Any, List, Optional, AsyncGenerator
import logging
from datetime import datetime, timedelta

from app.core.redis import get_redis
from app.core.config import settings
from .client import CrunchbaseClient
from .models import Company, FundingRound, Investor
from .exceptions import CrunchbaseAPIError
from .utils import normalize_company_data, normalize_funding_rounds

logger = logging.getLogger(__name__)

class CrunchbaseService:
    """Service for interacting with the Crunchbase API."""
    
    CACHE_PREFIX = "crunchbase:"
    CACHE_TTL = 86400  # 24 hours
    
    def __init__(self, client: Optional[CrunchbaseClient] = None):
        """Initialize the Crunchbase service.
        
        Args:
            client: Optional Crunchbase client. If not provided, a new one will be created.
        """
        self.client = client or CrunchbaseClient()
        self.redis = get_redis()
    
    async def _get_cached(self, key: str) -> Optional[Dict[str, Any]]:
        """Get a value from the cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found
        """
        if not settings.USE_REDIS_CACHE:
            return None
            
        cache_key = f"{self.CACHE_PREFIX}{key}"
        try:
            cached = await self.redis.get(cache_key)
            if cached:
                return cached
        except Exception as e:
            logger.warning(f"Error reading from cache: {e}")
        return None
    
    async def _set_cached(
        self, 
        key: str, 
        value: Any, 
        ttl: Optional[int] = None
    ) -> None:
        """Set a value in the cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds. If None, uses default TTL.
        """
        if not settings.USE_REDIS_CACHE:
            return
            
        cache_key = f"{self.CACHE_PREFIX}{key}"
        ttl = ttl or self.CACHE_TTL
        
        try:
            await self.redis.set(cache_key, value, ex=ttl)
        except Exception as e:
            logger.warning(f"Error writing to cache: {e}")
    
    async def get_company_by_domain(
        self, 
        domain: str,
        use_cache: bool = True
    ) -> Optional[Dict[str, Any]]:
        """Get company data by domain.
        
        Args:
            domain: Company domain (e.g., 'airbnb.com')
            use_cache: Whether to use cached data if available
            
        Returns:
            Company data or None if not found
        """
        cache_key = f"company:domain:{domain}"
        
        # Try to get from cache
        if use_cache:
            cached = await self._get_cached(cache_key)
            if cached:
                return cached
        
        # Fetch from API
        try:
            company = await self.client.get_company_by_domain(domain)
            if not company:
                return None
                
            # Get funding rounds
            rounds = await self.client.get_company_funding_rounds(company.uuid)
            
            # Normalize data
            result = {
                "company": await normalize_company_data(company.dict()),
                "funding_rounds": await normalize_funding_rounds([r.dict() for r in rounds]),
                "last_updated": datetime.utcnow().isoformat()
            }
            
            # Cache the result
            await self._set_cached(cache_key, result)
            
            return result
            
        except Exception as e:
            logger.error(f"Error fetching company data: {e}", exc_info=True)
            raise CrunchbaseAPIError(f"Failed to fetch company data: {e}")
    
    async def get_company_funding(self, company_id: str, use_cache: bool = True) -> Optional[Dict[str, Any]]:
        """Get detailed funding information for a company.
        
        Args:
            company_id: Crunchbase company ID or permalink
            use_cache: Whether to use cached data if available
            
        Returns:
            Dictionary containing detailed funding information or None if not found
            
        Raises:
            CrunchbaseAPIError: If there's an error fetching the data
        """
        cache_key = f"company:funding:{company_id}"
        
        # Try to get from cache if enabled
        if use_cache:
            cached = await self._get_cached(cache_key)
            if cached:
                return cached
        
        try:
            # Get company details
            company = await self.client.get_company(company_id)
            if not company:
                return None
            
            # Get all funding rounds with detailed information
            funding_rounds = []
            for round_data in await self.client.get_company_funding_rounds(company_id):
                # Get detailed information for each funding round
                detailed_round = await self.client.get_funding_round_details(round_data.uuid)
                if detailed_round:
                    funding_rounds.append(detailed_round)
            
            # Calculate aggregate metrics
            total_funding = company.total_funding_usd or sum(
                r.money_raised or 0 
                for r in funding_rounds 
                if r.money_raised_currency == "USD"
            )
            
            # Get unique investors and their investment amounts
            unique_investors = {}
            for round_data in funding_rounds:
                for investor in round_data.investors:
                    if investor.uuid not in unique_investors:
                        unique_investors[investor.uuid] = {
                            **investor.dict(),
                            "total_invested_usd": 0,
                            "investment_count": 0,
                            "first_investment_date": None,
                            "last_investment_date": None
                        }
                    
                    # Track investment amounts and dates
                    if round_data.money_raised and round_data.money_raised_currency == "USD":
                        unique_investors[investor.uuid]["total_invested_usd"] += round_data.money_raised
                    
                    unique_investors[investor.uuid]["investment_count"] += 1
                    
                    if round_data.announced_on:
                        if (not unique_investors[investor.uuid]["first_investment_date"] or 
                            round_data.announced_on < unique_investors[investor.uuid]["first_investment_date"]):
                            unique_investors[investor.uuid]["first_investment_date"] = round_data.announced_on
                        
                        if (not unique_investors[investor.uuid]["last_investment_date"] or 
                            round_data.announced_on > unique_investors[investor.uuid]["last_investment_date"]):
                            unique_investors[investor.uuid]["last_investment_date"] = round_data.announced_on
            
            # Sort funding rounds by date (newest first)
            sorted_rounds = sorted(
                [r.dict() for r in funding_rounds], 
                key=lambda x: x.get("announced_on") or "", 
                reverse=True
            )
            
            # Prepare response
            result = {
                "company_id": company_id,
                "company_name": company.name,
                "company_permalink": company.permalink,
                "total_funding_usd": total_funding,
                "funding_rounds": sorted_rounds,
                "round_count": len(funding_rounds),
                "investor_count": len(unique_investors),
                "investors": list(unique_investors.values()),
                "last_funding_round": sorted_rounds[0] if sorted_rounds else None,
                "first_funding_round": sorted_rounds[-1] if sorted_rounds else None,
                "last_updated": datetime.utcnow().isoformat()
            }
            
            # Cache the result (1 hour TTL for funding data)
            await self._set_cached(cache_key, result, ttl=3600)
            
            return result
            
        except Exception as e:
            logger.error(f"Error fetching funding data for company {company_id}: {e}", 
                       exc_info=True)
            raise CrunchbaseAPIError(f"Failed to fetch company funding: {e}")
            
    async def get_investor_portfolio(self, investor_id: str, use_cache: bool = True) -> Optional[Dict[str, Any]]:
        """Get investment portfolio for an investor.
        
        Args:
            investor_id: Investor UUID or permalink
            use_cache: Whether to use cached data if available
            
        Returns:
            Dictionary containing investor's portfolio or None if not found
            
        Raises:
            CrunchbaseAPIError: If there's an error fetching the data
        """
        cache_key = f"investor:portfolio:{investor_id}"
        
        # Try to get from cache if enabled
        if use_cache:
            cached = await self._get_cached(cache_key)
            if cached:
                return cached
            
        try:
            # Get investor details
            investor = await self.client.get_investor_details(investor_id)
            if not investor:
                return None
            
            # Get all investments for this investor
            # Note: This is a simplified implementation - in a real scenario, you would
            # need to handle pagination and potentially multiple API calls
            
            # For now, we'll return a basic portfolio structure
            portfolio = {
                "investor_id": investor_id,
                "investor_name": investor.get("name"),
                "investor_type": investor.get("type"),
                "website": investor.get("website"),
                "description": investor.get("description") or investor.get("short_description"),
                "investments": [],
                "total_investments": 0,
                "total_funding_usd": 0,
                "last_updated": datetime.utcnow().isoformat()
            }
            
            # In a real implementation, you would fetch the investor's portfolio
            # using the appropriate API endpoints and populate the investments list
            
            # Cache the result (24 hours TTL for investor data)
            await self._set_cached(cache_key, portfolio, ttl=86400)
            
            return portfolio
            
        except Exception as e:
            logger.error(f"Error fetching portfolio for investor {investor_id}: {e}", 
                       exc_info=True)
            raise CrunchbaseAPIError(f"Failed to fetch investor portfolio: {e}")
    
    async def search_companies(
        self, 
        query: str,
        limit: int = 10,
        page: int = 1,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """Search for companies on Crunchbase.
        
        Args:
            query: Search query
            limit: Maximum number of results per page
            page: Page number (1-based)
            use_cache: Whether to use cached data if available
            
        Returns:
            Search results
        """
        cache_key = f"search:companies:{query}:{limit}:{page}"
        
        # Try to get from cache
        if use_cache:
            cached = await self._get_cached(cache_key)
            if cached:
                return cached
        
        # TODO: Implement search functionality using the Crunchbase API
        # This is a placeholder implementation
        result = {
            "query": query,
            "page": page,
            "limit": limit,
            "total_results": 0,
            "results": [],
            "last_updated": datetime.utcnow().isoformat()
        }
        
        # Cache the result
        await self._set_cached(cache_key, result, ttl=3600)  # 1 hour TTL
        
        return result
    
    async def refresh_company_cache(self, company_id: str) -> Dict[str, Any]:
        """Refresh cached data for a company.
        
        Args:
            company_id: Crunchbase company ID
            
        Returns:
            Refreshed company data
        """
        # Clear cache
        cache_key = f"company:funding:{company_id}"
        await self.redis.delete(f"{self.CACHE_PREFIX}{cache_key}")
        
        # Fetch fresh data
        return await self.get_company_funding(company_id, use_cache=False)
    
    async def close(self):
        """Close the underlying client connection."""
        await self.client.close()
        
    async def __aenter__(self):
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
