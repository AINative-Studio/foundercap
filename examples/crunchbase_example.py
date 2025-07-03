#!/usr/bin/env python3
"""Example usage of the Crunchbase scraper."""

import asyncio
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

from unittest.mock import patch, Mock

# Mock the app.core.config import before importing the scraper
import types
app_module = types.ModuleType('app')
core_module = types.ModuleType('core')
config_module = types.ModuleType('config')

class MockSettings:
    CRUNCHBASE_API_KEY = "mock-key"

config_module.settings = MockSettings()
core_module.config = config_module
app_module.core = core_module
sys.modules['app'] = app_module
sys.modules['app.core'] = core_module
sys.modules['app.core.config'] = config_module

from services.scraper.crunchbase import CrunchbaseScraper


async def example_usage():
    """Demonstrate Crunchbase scraper usage."""
    print("🚀 Crunchbase Scraper Example")
    print("=" * 40)
    
    # Create scraper instance
    scraper = CrunchbaseScraper()
    print(f"📊 Scraper name: {scraper.name}")
    
    # Mock the settings to avoid needing real API key
    with patch("services.scraper.crunchbase.settings") as mock_settings:
        mock_settings.CRUNCHBASE_API_KEY = "mock-api-key"
        
        # Initialize the scraper
        await scraper.initialize()
        print("✅ Scraper initialized")
        
        # Mock a successful API response
        mock_response_data = {
            "properties": {
                "funding_total": {"value": 157000000},
                "funding_stage": {"value": "Series D"},
                "investors": [
                    {"name": "Andreessen Horowitz"},
                    {"name": "Tiger Global Management"},
                    {"identifier": {"value": "Sequoia Capital"}}
                ]
            }
        }
        
        with patch.object(scraper._client, "get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_response_data
            mock_get.return_value = mock_response
            
            # Fetch data for a company
            company_data = await scraper.fetch_crunchbase("stripe")
            
            print("\n📈 Company Data Retrieved:")
            print(f"   💰 Total Funding: ${company_data.total_funding:,}")
            print(f"   🎯 Funding Stage: {company_data.funding_stage}")
            print(f"   🏦 Investors: {', '.join(company_data.investors)}")
            
            # Test the scrape method (higher level interface)
            scrape_result = await scraper.scrape("Stripe Inc", permalink="stripe")
            
            print("\n🔍 Scrape Result:")
            print(f"   📊 Source: {scrape_result['source']}")
            print(f"   🏢 Company: {scrape_result['company_name']}")
            print(f"   💰 Funding: ${scrape_result['data']['total_funding']:,}")
            
            # Test caching
            print(f"\n💾 Cache size: {scraper.get_cache_size()}")
            
            # Second call should use cache
            cached_data = await scraper.fetch_crunchbase("stripe")
            print("✅ Second call completed (from cache)")
            
            # Verify cache was used (no additional API call)
            assert mock_get.call_count == 1, "Expected only one API call due to caching"
            print("✅ Caching verified")
        
        # Clean up
        await scraper.shutdown()
        print("🔧 Scraper shut down")
    
    print("\n🎉 Example completed successfully!")


if __name__ == "__main__":
    asyncio.run(example_usage())