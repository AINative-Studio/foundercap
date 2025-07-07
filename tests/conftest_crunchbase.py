"""Pytest configuration for Crunchbase tests."""
import pytest
import asyncio
from typing import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock

from app.services.crunchbase import CrunchbaseClient, CrunchbaseService
from tests.test_config import test_settings

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def mock_redis():
    """Create a mock Redis client."""
    redis = AsyncMock()
    redis.get.return_value = None  # Default to cache miss
    return redis

@pytest.fixture
def mock_crunchbase_client():
    """Create a mock Crunchbase client."""
    client = AsyncMock(spec=CrunchbaseClient)
    return client

@pytest.fixture
def crunchbase_service(mock_crunchbase_client, mock_redis):
    """Create a CrunchbaseService instance with mocked dependencies."""
    service = CrunchbaseService(client=mock_crunchbase_client)
    service.redis = mock_redis
    return service

@pytest.fixture
def sample_company_data():
    """Sample company data for testing."""
    return {
        "uuid": "test-uuid-123",
        "name": "Test Company",
        "short_description": "A test company",
        "website": "https://test.com",
        "total_funding_usd": 1000000,
        "last_funding_type": "series_a",
        "last_funding_at": "2023-01-01"
    }

@pytest.fixture
def sample_funding_rounds():
    """Sample funding rounds data for testing."""
    return [
        {
            "uuid": "round-1",
            "name": "Series A",
            "announced_on": "2023-01-01",
            "money_raised": 1000000,
            "money_raised_currency": "USD"
        }
    ]
