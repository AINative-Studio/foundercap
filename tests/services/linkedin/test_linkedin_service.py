"""Tests for the LinkedIn service."""
import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock
import pytest

from app.services.linkedin import LinkedInScraper, get_linkedin_service

@pytest.fixture
def mock_redis():
    """Fixture for a mock Redis client."""
    mock = AsyncMock()
    mock.get.return_value = None
    mock.setex.return_value = True
    return mock

@pytest.fixture
def mock_scraper():
    """Fixture for a mock LinkedInScraper."""
    mock = AsyncMock(spec=LinkedInScraper)
    mock.get_company_info.return_value = {
        "name": "Test Company",
        "website": "https://testcompany.com",
        "company_size": "1001-5000 employees",
        "industry": "Information Technology"
    }
    return mock

async def test_get_company_info(mock_redis, mock_scraper):
    """Test getting company info with cache miss."""
    # Setup
    service = get_linkedin_service()
    service.redis = mock_redis
    service.scraper = mock_scraper
    
    # Test
    company_info = await service.get_company_info("Test Company")
    
    # Assertions
    assert company_info is not None
    assert company_info["name"] == "Test Company"
    mock_scraper.get_company_info.assert_called_once_with("Test Company")
    mock_redis.setex.assert_called_once()

async def test_get_company_info_cached(mock_redis, mock_scraper):
    """Test getting company info with cache hit."""
    # Setup
    cached_data = {
        "name": "Cached Company",
        "website": "https://cached.com",
        "company_size": "5001+ employees",
        "industry": "Technology"
    }
    mock_redis.get.return_value = json.dumps(cached_data)
    
    service = get_linkedin_service()
    service.redis = mock_redis
    service.scraper = mock_scraper
    
    # Test
    company_info = await service.get_company_info("Cached Company")
    
    # Assertions
    assert company_info == cached_data
    mock_scraper.get_company_info.assert_not_called()
    mock_redis.setex.assert_not_called()

@pytest.mark.asyncio
@pytest.mark.asyncio
async def test_batch_get_company_info(mock_redis, mock_scraper):
    """Test batch getting company info."""
    # Setup
    service = get_linkedin_service()
    service.redis = mock_redis
    service.scraper = mock_scraper
    
    # Test
    companies = ["Company A", "Company B"]
    results = []
    
    async for company_name, company_info in service.batch_get_company_info(companies):
        results.append((company_name, company_info))
    
    # Assertions
    assert len(results) == 2
    assert results[0][0] == "Company A"
    assert results[1][0] == "Company B"
    assert mock_scraper.get_company_info.call_count == 2



