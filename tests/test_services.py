#!/usr/bin/env python3
"""Test service layer components."""

import pytest
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Set environment variables before any imports
os.environ.update({
    "ENVIRONMENT": "testing",
    "DEBUG": "True",
    "DATABASE_POOL_RECYCLE": "3600",
    "ACCESS_TOKEN_EXPIRE_MINUTES": "11520",
    "LINKEDIN_HEADLESS": "True",
    "LINKEDIN_SKIP_LOGIN": "False",
    "LINKEDIN_TIMEOUT": "30000",
    "LINKEDIN_SLOW_MO": "100",
    "LINKEDIN_CACHE_TTL": "86400",
    "CELERY_TASK_TIME_LIMIT": "1800",
    "CELERY_TASK_SOFT_TIME_LIMIT": "1500",
    "REQUEST_TIMEOUT": "30",
    "RETRY_DELAY": "5",
    "CRUNCHBASE_API_KEY": "test_key"
})


def test_crunchbase_client_initialization():
    """Test Crunchbase client initialization."""
    from app.services.crunchbase.client import CrunchbaseClient
    from app.services.crunchbase.config import CrunchbaseConfig
    
    config = CrunchbaseConfig()
    client = CrunchbaseClient(config)
    
    assert client.config == config
    assert client.rate_limiter is not None
    assert client.http_client is None  # Not initialized until first use


def test_crunchbase_client_headers():
    """Test Crunchbase client headers."""
    from app.services.crunchbase.client import CrunchbaseClient
    from app.services.crunchbase.config import CrunchbaseConfig
    
    config = CrunchbaseConfig()
    client = CrunchbaseClient(config)
    headers = client._get_headers()
    
    assert "User-Agent" in headers
    assert "Accept" in headers
    assert "Content-Type" in headers
    assert headers["Accept"] == "application/json"
    assert headers["Content-Type"] == "application/json"


def test_crunchbase_factory_create_service():
    """Test Crunchbase factory service creation."""
    from app.services.crunchbase.factory import CrunchbaseFactory
    
    service = CrunchbaseFactory.create_service()
    
    assert service is not None
    assert hasattr(service, 'config')
    assert hasattr(service, 'client')


def test_crunchbase_factory_create_client():
    """Test Crunchbase factory client creation."""
    from app.services.crunchbase.factory import CrunchbaseFactory
    
    client = CrunchbaseFactory.create_client()
    
    assert client is not None
    assert hasattr(client, 'config')
    assert hasattr(client, 'rate_limiter')


def test_crunchbase_factory_create_config():
    """Test Crunchbase factory config creation."""
    from app.services.crunchbase.factory import CrunchbaseFactory
    
    config = CrunchbaseFactory.create_config()
    
    assert config is not None
    assert config.api_key == "test_key"
    assert config.base_url == "https://api.crunchbase.com/api/v4/"


def test_crunchbase_utils_validate_url():
    """Test Crunchbase utils URL validation."""
    from app.services.crunchbase.utils import validate_crunchbase_url
    
    # Valid URLs
    assert validate_crunchbase_url("https://crunchbase.com/organization/company") is True
    assert validate_crunchbase_url("https://www.crunchbase.com/organization/test-company") is True
    
    # Invalid URLs
    assert validate_crunchbase_url("https://example.com") is False
    assert validate_crunchbase_url("not-a-url") is False
    assert validate_crunchbase_url(None) is False


def test_crunchbase_utils_extract_organization_name():
    """Test Crunchbase utils organization name extraction."""
    from app.services.crunchbase.utils import extract_organization_name
    
    # Valid URLs
    assert extract_organization_name("https://crunchbase.com/organization/test-company") == "test-company"
    assert extract_organization_name("https://www.crunchbase.com/organization/my-startup") == "my-startup"
    
    # Invalid URLs
    assert extract_organization_name("https://example.com") is None
    assert extract_organization_name("not-a-url") is None
    assert extract_organization_name(None) is None


def test_crunchbase_utils_format_currency():
    """Test Crunchbase utils currency formatting."""
    from app.services.crunchbase.utils import format_currency
    
    assert format_currency(1000) == "$1,000"
    assert format_currency(1000000) == "$1,000,000"
    assert format_currency(1500000) == "$1,500,000"
    assert format_currency(None) == "N/A"
    assert format_currency(0) == "$0"


def test_crunchbase_utils_clean_company_name():
    """Test Crunchbase utils company name cleaning."""
    from app.services.crunchbase.utils import clean_company_name
    
    assert clean_company_name("Test Company Inc.") == "Test Company"
    assert clean_company_name("My Startup LLC") == "My Startup"
    assert clean_company_name("Company Corp") == "Company"
    assert clean_company_name("Test Ltd.") == "Test"
    assert clean_company_name("Simple Name") == "Simple Name"
    assert clean_company_name(None) is None


def test_linkedin_service_initialization():
    """Test LinkedIn service initialization."""
    from app.services.linkedin.service import LinkedInService
    
    service = LinkedInService()
    
    assert service.config is not None
    assert service.config.headless is True
    assert service.config.timeout == 30000


@patch('app.services.linkedin.service.LinkedInScraper')
def test_linkedin_service_get_company_info(mock_scraper_class):
    """Test LinkedIn service get company info."""
    from app.services.linkedin.service import LinkedInService
    
    # Mock the scraper
    mock_scraper = MagicMock()
    mock_scraper_class.return_value = mock_scraper
    mock_scraper.get_company_info.return_value = {
        "name": "Test Company",
        "description": "A test company",
        "website": "https://test.com"
    }
    
    service = LinkedInService()
    result = service.get_company_info("https://linkedin.com/company/test")
    
    assert result["name"] == "Test Company"
    assert result["description"] == "A test company"
    assert result["website"] == "https://test.com"
    mock_scraper.get_company_info.assert_called_once()


@patch('app.services.linkedin.service.LinkedInScraper')
def test_linkedin_service_search_companies(mock_scraper_class):
    """Test LinkedIn service search companies."""
    from app.services.linkedin.service import LinkedInService
    
    # Mock the scraper
    mock_scraper = MagicMock()
    mock_scraper_class.return_value = mock_scraper
    mock_scraper.search_companies.return_value = [
        {"name": "Company 1", "url": "https://linkedin.com/company/company1"},
        {"name": "Company 2", "url": "https://linkedin.com/company/company2"}
    ]
    
    service = LinkedInService()
    results = service.search_companies("test query")
    
    assert len(results) == 2
    assert results[0]["name"] == "Company 1"
    assert results[1]["name"] == "Company 2"
    mock_scraper.search_companies.assert_called_once_with("test query")


def test_linkedin_scraper_initialization():
    """Test LinkedIn scraper initialization."""
    from app.services.linkedin.scraper import LinkedInScraper
    from app.services.linkedin.config import LinkedInConfig
    
    config = LinkedInConfig()
    scraper = LinkedInScraper(config)
    
    assert scraper.config == config
    assert scraper.browser is None
    assert scraper.page is None


@pytest.mark.asyncio
async def test_redis_client_operations():
    """Test Redis client operations."""
    from app.core.redis import get_redis, set_key, get_key, delete_key
    
    with patch('app.core.redis.redis_client') as mock_redis:
        mock_redis.ping.return_value = True
        mock_redis.set.return_value = True
        mock_redis.get.return_value = b"test_value"
        mock_redis.delete.return_value = 1
        
        # Test set operation
        result = await set_key("test_key", "test_value")
        assert result is True
        mock_redis.set.assert_called_once()
        
        # Test get operation
        result = await get_key("test_key")
        assert result == "test_value"
        mock_redis.get.assert_called_once()
        
        # Test delete operation
        result = await delete_key("test_key")
        assert result == 1
        mock_redis.delete.assert_called_once()


def test_config_settings_loading():
    """Test configuration settings loading."""
    from app.core.config import settings
    
    # Test that environment variables are loaded
    assert settings.ENVIRONMENT == "testing"
    assert settings.DEBUG is True
    assert settings.DATABASE_POOL_RECYCLE == 3600
    assert settings.ACCESS_TOKEN_EXPIRE_MINUTES == 11520


def test_config_database_url_construction():
    """Test database URL construction."""
    from app.core.config import settings
    
    # Mock the required environment variables
    with patch.dict(os.environ, {
        "POSTGRES_SERVER": "localhost",
        "POSTGRES_PORT": "5432",
        "POSTGRES_USER": "test_user",
        "POSTGRES_PASSWORD": "test_pass",
        "POSTGRES_DB": "test_db"
    }):
        # Reload settings to pick up new environment
        from importlib import reload
        from app.core import config
        reload(config)
        
        # Verify DATABASE_URI construction works
        assert hasattr(config.settings, 'DATABASE_URI')


def test_linkedin_company_update_model():
    """Test LinkedIn company update model."""
    from app.services.linkedin.models import LinkedInCompanyUpdate
    
    update = LinkedInCompanyUpdate(
        name="Updated Company",
        linkedin_url="https://linkedin.com/company/updated",
        changed_fields=["name", "description"]
    )
    
    assert update.name == "Updated Company"
    assert update.linkedin_url == "https://linkedin.com/company/updated"
    assert "name" in update.changed_fields
    assert "description" in update.changed_fields


def test_linkedin_company_update_from_company():
    """Test creating LinkedInCompanyUpdate from LinkedInCompany."""
    from app.services.linkedin.models import LinkedInCompany, LinkedInCompanyUpdate
    
    original = LinkedInCompany(
        name="Original Company",
        linkedin_url="https://linkedin.com/company/original"
    )
    
    updated = LinkedInCompanyUpdate.from_company(
        original,
        {"name": "Updated Company", "description": "New description"},
        ["name", "description"]
    )
    
    assert updated.name == "Updated Company"
    assert updated.description == "New description"
    assert updated.linkedin_url == "https://linkedin.com/company/original"
    assert "name" in updated.changed_fields
    assert "description" in updated.changed_fields


if __name__ == "__main__":
    pytest.main([__file__, "-v"])