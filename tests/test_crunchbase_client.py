"""Tests for the Crunchbase API client."""
import pytest
import httpx
import respx
from datetime import date
from unittest.mock import patch, MagicMock

from app.services.crunchbase import (
    CrunchbaseClient,
    CrunchbaseConfig,
    CrunchbaseAuthError,
    CrunchbaseNotFoundError,
    Company,
    FundingRound,
    Investor,
)

@pytest.fixture
def mock_config():
    """Create a mock configuration for testing."""
    return CrunchbaseConfig(
        api_key="test_api_key",
        base_url="https://test.api.crunchbase.com/api/v4/",
        requests_per_second=10,  # Higher limit for testing
        max_retries=2,
    )

@pytest.fixture
def mock_company_data():
    """Sample company data for testing."""
    return {
        "uuid": "test-company-uuid",
        "name": "Test Company",
        "permalink": "test-company",
        "description": "A test company",
        "homepage_url": "https://testcompany.com",
        "founded_on": "2020-01-01",
        "total_funding_usd": 1000000,
        "last_funding_type": "seed",
        "last_funding_at": "2023-01-01",
    }

@pytest.fixture
def mock_funding_rounds_data():
    """Sample funding rounds data for testing."""
    return {
        "entities": [
            {
                "uuid": "round-1",
                "name": "Seed Round",
                "announced_on": "2023-01-01",
                "investment_type": "seed",
                "money_raised_usd": 1000000,
                "money_raised_currency": "USD",
                "investor_count": 3,
                "investors": [
                    {
                        "name": "Investor 1",
                        "uuid": "inv-1",
                        "permalink": "investor-1",
                        "type": "financial_investor",
                    }
                ],
                "source_url": "https://example.com/news/seed-round",
            }
        ]
    }

@pytest.mark.asyncio
@respx.mock
async def test_get_company_success(mock_config, mock_company_data):
    """Test successful company lookup."""
    # Mock the API response
    company_uuid = "test-company-uuid"
    mock_response = {"data": mock_company_data}
    
    # Setup the mock route
    route = respx.get(
        f"https://test.api.crunchbase.com/api/v4/entities/organizations/{company_uuid}"
    ).mock(return_value=httpx.Response(200, json=mock_response))
    
    # Test the client
    async with CrunchbaseClient(config=mock_config) as client:
        company = await client.get_company(company_uuid)
        
        # Verify the request was made correctly
        assert route.called
        assert company is not None
        assert company.uuid == company_uuid
        assert company.name == "Test Company"
        assert company.total_funding_usd == 1000000

@pytest.mark.asyncio
@respx.mock
async def test_get_company_not_found(mock_config):
    """Test company not found scenario."""
    # Mock a 404 response
    company_uuid = "non-existent-company"
    route = respx.get(
        f"https://test.api.crunchbase.com/api/v4/entities/organizations/{company_uuid}"
    ).mock(return_value=httpx.Response(404, json={"error": "Not found"}))
    
    # Test the client
    async with CrunchbaseClient(config=mock_config) as client:
        company = await client.get_company(company_uuid)
        assert company is None
        assert route.called

@pytest.mark.asyncio
@respx.mock
async def test_get_company_auth_error(mock_config):
    """Test authentication error handling."""
    # Mock a 401 response
    company_uuid = "test-company"
    route = respx.get(
        f"https://test.api.crunchbase.com/api/v4/entities/organizations/{company_uuid}"
    ).mock(return_value=httpx.Response(401, json={"error": "Unauthorized"}))
    
    # Test the client
    async with CrunchbaseClient(config=mock_config) as client:
        with pytest.raises(CrunchbaseAuthError):
            await client.get_company(company_uuid)
    
    assert route.called

@pytest.mark.asyncio
@respx.mock
async def test_get_company_funding_rounds(mock_config, mock_funding_rounds_data):
    """Test fetching company funding rounds."""
    company_uuid = "test-company-uuid"
    
    # Mock the API response
    route = respx.get(
        f"https://test.api.crunchbase.com/api/v4/entities/organizations/{company_uuid}/cards/funding_rounds"
    ).mock(return_value=httpx.Response(200, json=mock_funding_rounds_data))
    
    # Test the client
    async with CrunchbaseClient(config=mock_config) as client:
        rounds = await client.get_company_funding_rounds(company_uuid)
        
        assert route.called
        assert len(rounds) == 1
        assert rounds[0].uuid == "round-1"
        assert rounds[0].name == "Seed Round"
        assert rounds[0].investor_count == 3
        assert len(rounds[0].investors) == 1
        assert rounds[0].investors[0].name == "Investor 1"

@pytest.mark.asyncio
@respx.mock
async def test_rate_limiting(mock_config):
    """Test that rate limiting is enforced."""
    # Setup a mock that always succeeds
    route = respx.get("https://test.api.crunchbase.com/api/v4/entities/organizations/test")
    route.mock(return_value=httpx.Response(200, json={"data": {"uuid": "test"}}))
    
    # Create a client with a very low rate limit
    config = CrunchbaseConfig(
        api_key="test",
        requests_per_second=1,  # 1 request per second
        max_retries=0,
    )
    
    async with CrunchbaseClient(config=config) as client:
        # Time the execution of multiple requests
        import time
        start_time = time.time()
        
        # Make 3 requests
        for _ in range(3):
            await client.get_company("test")
        
        end_time = time.time()
        
        # Should take at least 2 seconds (1 second between each of 3 requests)
        assert end_time - start_time >= 2.0
        assert route.call_count == 3
