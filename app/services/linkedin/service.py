"""
LinkedIn Service

This module provides a high-level interface for interacting with LinkedIn data,
handling caching, error handling, and integration with other services.
"""
import json
import logging
from typing import Optional, Dict, Any, AsyncGenerator

from app.core.config import settings
from app.core.redis import get_redis
from app.services.linkedin.scraper import LinkedInScraper

logger = logging.getLogger(__name__)

class LinkedInService:
    """Service for interacting with LinkedIn data."""
    
    def __init__(self):
        """Initialize the LinkedIn service."""
        self.redis = get_redis()
        self.scraper = None
        self.logged_in = False
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self._initialize_scraper()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self._close_scraper()
    
    async def _initialize_scraper(self):
        """Initialize the Playwright scraper."""
        try:
            self.scraper = LinkedInScraper(
                headless=settings.LINKEDIN_HEADLESS,
                slow_mo=settings.LINKEDIN_SLOW_MO,
                timeout=settings.LINKEDIN_TIMEOUT
            )
            await self.scraper.start()
            
            # Login if credentials are provided
            if (settings.LINKEDIN_EMAIL and settings.LINKEDIN_PASSWORD and 
                not settings.LINKEDIN_SKIP_LOGIN):
                logger.info("Attempting to log in to LinkedIn...")
                self.logged_in = await self.scraper.login(
                    settings.LINKEDIN_EMAIL,
                    settings.LINKEDIN_PASSWORD
                )
                if not self.logged_in:
                    logger.warning("Failed to log in to LinkedIn. Continuing without login.")
                
        except Exception as e:
            logger.error(f"Failed to initialize LinkedIn scraper: {e}")
            await self._close_scraper()
            raise
    
    async def _close_scraper(self):
        """Close the Playwright scraper."""
        try:
            if self.scraper:
                await self.scraper.close()
        except Exception as e:
            logger.error(f"Error closing LinkedIn scraper: {e}")
        finally:
            self.scraper = None
            self.logged_in = False
    
    async def get_company_info(self, company_name: str, use_cache: bool = True) -> Optional[Dict[str, Any]]:
        """
        Get company information by name.
        
        Args:
            company_name: Name of the company to look up
            use_cache: Whether to use cached data if available
            
        Returns:
            Dictionary containing company information or None if not found
        """
        if not company_name or not isinstance(company_name, str):
            logger.error("Invalid company name provided")
            return None
            
        cache_key = f"linkedin:company:{company_name.lower().strip()}"
        
        # Try to get from cache
        if use_cache:
            try:
                cached = await self.redis.get(cache_key)
                if cached:
                    logger.debug(f"Cache hit for {company_name}")
                    return json.loads(cached)
            except Exception as e:
                logger.warning(f"Error accessing cache for {company_name}: {e}")
        
        # Scrape the data
        try:
            if not self.scraper:
                await self._initialize_scraper()
            
            if not self.scraper:
                raise RuntimeError("Failed to initialize LinkedIn scraper")
            
            logger.info(f"Scraping LinkedIn for company: {company_name}")
            company_data = await self.scraper.get_company_info(company_name)
            
            if company_data:
                # Cache the result
                try:
                    await self.redis.setex(
                        cache_key,
                        settings.LINKEDIN_CACHE_TTL,
                        json.dumps(company_data)
                    )
                    logger.debug(f"Cached data for {company_name}")
                except Exception as e:
                    logger.warning(f"Failed to cache data for {company_name}: {e}")
                
                return company_data
                
            logger.warning(f"No data found for company: {company_name}")
            return None
            
        except Exception as e:
            logger.error(f"Error getting company info for {company_name}: {e}")
            return None
    
    async def batch_get_company_info(
        self, 
        company_names: list[str],
        use_cache: bool = True
    ) -> AsyncGenerator[tuple[str, Optional[Dict[str, Any]]], None]:
        """
        Get information for multiple companies in batch.
        
        Args:
            company_names: List of company names to look up
            use_cache: Whether to use cached data if available
            
        Yields:
            Tuples of (company_name, company_data) for each company
        """
        if not isinstance(company_names, list):
            raise ValueError("company_names must be a list")
            
        for company_name in company_names:
            if not company_name or not isinstance(company_name, str):
                logger.warning(f"Skipping invalid company name: {company_name}")
                yield company_name, None
                continue
                
            try:
                company_data = await self.get_company_info(company_name, use_cache)
                yield company_name, company_data
            except Exception as e:
                logger.error(f"Error processing company {company_name}: {e}")
                yield company_name, None
                
            # Small delay between requests to avoid rate limiting
            await asyncio.sleep(1)

import asyncio

_linkedin_service_instance = None

def get_linkedin_service():
    """Return a singleton instance of the LinkedInService."""
    global _linkedin_service_instance
    if _linkedin_service_instance is None:
        _linkedin_service_instance = LinkedInService()
    return _linkedin_service_instance

# Example usage:
# async with get_linkedin_service() as service:
#     company_info = await service.get_company_info("Google")
#     print(company_info)
