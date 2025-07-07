#!/usr/bin/env python3
"""
Integration test for the LinkedIn scraper and service.

This script tests the LinkedIn scraper and service together.
"""
import asyncio
import json
import logging
import os
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

async def test_linkedin_service():
    """Test the LinkedIn service with a real Redis connection."""
    from app.core.redis import init_redis, close_redis
    from app.services.linkedin import LinkedInService
    
    # Initialize Redis
    redis = await init_redis()
    
    try:
        # Test with a real service instance
        async with LinkedInService() as service:
            # Test getting company info
            company_name = "Google"
            logger.info(f"Testing get_company_info for {company_name}")
            
            # First call - should hit the API
            company_info = await service.get_company_info(company_name)
            logger.info(f"Company info: {json.dumps(company_info, indent=2)}")
            
            # Second call - should hit the cache
            logger.info("Testing cache...")
            cached_info = await service.get_company_info(company_name)
            assert company_info == cached_info, "Cached info should match original"
            
            # Test batch processing
            companies = ["Microsoft", "Apple", "Amazon"]
            logger.info(f"Testing batch processing for {companies}")
            
            async for name, info in service.batch_get_company_info(companies):
                if info:
                    logger.info(f"Found: {name} - {info.get('website')}")
                else:
                    logger.warning(f"No info found for {name}")
                    
    finally:
        # Clean up
        await close_redis()

if __name__ == "__main__":
    # Check if LinkedIn credentials are provided
    if not os.getenv("LINKEDIN_EMAIL") or not os.getenv("LINKEDIN_PASSWORD"):
        logger.warning(
            "LINKEDIN_EMAIL and/or LINKEDIN_PASSWORD environment variables not set. "
            "Some features may be limited."
        )
    
    # Run the test
    asyncio.run(test_linkedin_service())
