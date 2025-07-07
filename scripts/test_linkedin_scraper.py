#!/usr/bin/env python3
"""
Test script for the LinkedIn scraper.

This script demonstrates how to use the LinkedInScraper class to scrape company data.
"""
import asyncio
import json
import logging
import os
from pathlib import Path
from pprint import pprint

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv(override=True)  # Override existing environment variables

# Add project root to path
import sys
sys.path.append(str(Path(__file__).parent.parent))

# Import the scraper after setting up the path
from app.services.scraper.linkedin import LinkedInScraper

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('linkedin_scraper_test.log')
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

# Test companies to scrape
TEST_COMPANIES = [
    "Google",
    "Microsoft",
    "Apple"
]

async def test_scraper():
    """Test the LinkedIn scraper with a list of companies."""
    results = {}
    
    # Initialize the scraper
    async with LinkedInScraper(headless=False) as scraper:
        for company in TEST_COMPANIES:
            try:
                logger.info(f"Scraping data for {company}...")
                result = await scraper.scrape(company)
                results[company] = result
                
                if result["status"] == "success":
                    logger.info(f"Successfully scraped {company}")
                    logger.info(f"Website: {result['data'].get('website')}")
                    logger.info(f"Headcount: {result['data'].get('headcount')}")
                else:
                    logger.error(f"Failed to scrape {company}: {result.get('error')}")
                
                # Be nice to LinkedIn
                await asyncio.sleep(5)
                
            except Exception as e:
                logger.error(f"Error scraping {company}: {str(e)}")
                results[company] = {"status": "error", "error": str(e)}
    
    # Save results to a file
    output_file = Path("linkedin_scraper_results.json")
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Results saved to {output_file}")
    return results

if __name__ == "__main__":
    # Run the test
    results = asyncio.run(test_scraper())
    
    # Print a summary
    print("\n=== Scraping Summary ===")
    for company, result in results.items():
        status = "✓" if result.get("status") == "success" else "✗"
        print(f"{status} {company}")
        if "error" in result:
            print(f"   Error: {result['error']}")
        elif "missing_fields" in result and result["missing_fields"]:
            print(f"   Missing fields: {', '.join(result['missing_fields'])}")
    print("======================")

    # Print the first result for inspection
    first_result = next(iter(results.values()), {})
    if first_result.get("status") == "success":
        print("\nSample data from first result:")
        pprint(first_result["data"])
