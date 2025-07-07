#!/usr/bin/env python3
"""
Test script for the LinkedIn scraper.

This script demonstrates how to use the LinkedIn scraper to fetch company information.
"""
import asyncio
import json
import logging
import os
from dotenv import load_dotenv

from app.services.linkedin import LinkedInService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

async def main():
    """Test the LinkedIn scraper."""
    # Check if LinkedIn credentials are provided
    if not os.getenv("LINKEDIN_EMAIL") or not os.getenv("LINKEDIN_PASSWORD"):
        logger.warning(
            "LINKEDIN_EMAIL and/or LINKEDIN_PASSWORD environment variables not set. "
            "Some features may be limited."
        )
    
    # List of companies to look up
    companies = ["Google", "Microsoft", "Apple"]
    
    async with LinkedInService() as service:
        for company in companies:
            try:
                logger.info(f"Fetching information for {company}...")
                company_info = await service.get_company_info(company)
                
                if company_info:
                    print(f"\n=== {company} ===")
                    print(json.dumps(company_info, indent=2, default=str))
                else:
                    logger.warning(f"No information found for {company}")
                    
            except Exception as e:
                logger.error(f"Error processing {company}: {e}")
                
            # Add a small delay between requests
            await asyncio.sleep(2)

if __name__ == "__main__":
    asyncio.run(main())
