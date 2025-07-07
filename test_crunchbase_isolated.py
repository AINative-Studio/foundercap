"""
Completely isolated test for the Crunchbase service.
This test doesn't depend on the application's configuration.
"""
import sys
import os
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta

# Mock the environment before importing any app code
os.environ["TESTING"] = "true"
os.environ["CRUNCHBASE_API_KEY"] = "test_api_key"

# Define minimal models needed for testing
class Company:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
    
    def dict(self):
        return self.__dict__.copy()

class FundingRound:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
    
    def dict(self):
        return self.__dict__.copy()

# Test service implementation
class TestCrunchbaseService:
    """Test version of CrunchbaseService that doesn't depend on the app."""
    
    CACHE_PREFIX = "test:crunchbase:"
    CACHE_TTL = 3600
    
    def __init__(self, client=None, redis=None):
        self.client = client or AsyncMock()
        self.redis = redis or AsyncMock()
        self.redis.get.return_value = None  # Default to cache miss
    
    async def _get_cached(self, key: str) -> dict:
        """Get a value from the cache."""
        cached = await self.redis.get(f"{self.CACHE_PREFIX}{key}")
        return cached if cached else None
    
    async def _set_cached(self, key: str, value: dict, ttl: int = None) -> None:
        """Set a value in the cache."""
        ttl = ttl or self.CACHE_TTL
        await self.redis.set(
            f"{self.CACHE_PREFIX}{key}",
            value,
            ex=ttl
        )
    
    async def get_company_by_domain(self, domain: str) -> dict:
        """Get company data by domain."""
        cache_key = f"company:domain:{domain}"
        
        # Try to get from cache
        cached = await self._get_cached(cache_key)
        if cached:
            return cached
            
        # Fetch from API
        company = await self.client.get_company_by_domain(domain)
        if not company:
            return None
            
        # Get funding rounds
        funding_rounds = await self.client.get_company_funding_rounds(company.uuid)
        
        # Prepare response
        result = {
            "company": company.dict(),
            "funding_rounds": [r.dict() for r in funding_rounds],
            "last_updated": datetime.utcnow().isoformat()
        }
        
        # Cache the result
        await self._set_cached(cache_key, result)
        return result
    
    async def get_company_funding(self, company_id: str, use_cache: bool = True) -> dict:
        """Get funding data for a company."""
        cache_key = f"company:funding:{company_id}"
        
        # Try to get from cache if enabled
        if use_cache:
            cached = await self._get_cached(cache_key)
            if cached:
                return cached
                
        # Fetch from API
        company = await self.client.get_company(company_id)
        if not company:
            return None
            
        funding_rounds = await self.client.get_company_funding_rounds(company_id)
        
        # Prepare response
        result = {
            "company_id": company_id,
            "company_name": company.name,
            "total_funding_usd": getattr(company, 'total_funding_usd', 0),
            "funding_rounds": [r.dict() for r in funding_rounds],
            "last_updated": datetime.utcnow().isoformat()
        }
        
        # Cache the result
        await self._set_cached(cache_key, result)
        return result
    
    async def refresh_company_cache(self, company_id: str) -> dict:
        """Refresh the cache for a company's data."""
        # Clear the cache
        cache_key = f"company:funding:{company_id}"
        await self.redis.delete(f"{self.CACHE_PREFIX}{cache_key}")
        
        # Fetch fresh data
        return await self.get_company_funding(company_id, use_cache=False)
    
    async def close(self):
        """Close the service and its client."""
        if hasattr(self.client, 'close') and callable(self.client.close):
            await self.client.close()
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

# Test data
SAMPLE_COMPANY_DATA = {
    "uuid": "test-uuid-123",
    "name": "Test Company",
    "short_description": "A test company",
    "website": "https://test.com",
    "total_funding_usd": 1000000,
    "last_funding_type": "series_a",
    "last_funding_at": "2023-01-01"
}

SAMPLE_FUNDING_ROUNDS = [
    {
        "uuid": "round-1",
        "name": "Series A",
        "announced_on": "2023-01-01",
        "money_raised": 1000000,
        "money_raised_currency": "USD"
    }
]

# Tests
async def test_get_company_by_domain_success():
    """Test successful company lookup by domain."""
    # Setup mocks
    mock_client = AsyncMock()
    mock_redis = AsyncMock()
    mock_redis.get.return_value = None
    
    # Setup service
    service = TestCrunchbaseService(client=mock_client, redis=mock_redis)
    
    # Setup mock responses
    mock_client.get_company_by_domain.return_value = Company(**SAMPLE_COMPANY_DATA)
    mock_client.get_company_funding_rounds.return_value = [
        FundingRound(**r) for r in SAMPLE_FUNDING_ROUNDS
    ]
    
    # Call the method
    result = await service.get_company_by_domain("test.com")
    
    # Assertions
    assert result is not None
    assert result["company"]["name"] == SAMPLE_COMPANY_DATA["name"]
    assert len(result["funding_rounds"]) == len(SAMPLE_FUNDING_ROUNDS)
    mock_client.get_company_by_domain.assert_awaited_once_with("test.com")
    mock_redis.set.assert_awaited()
    print("✓ test_get_company_by_domain_success passed")

async def test_get_company_funding_success():
    """Test successful funding data retrieval."""
    # Setup mocks
    mock_client = AsyncMock()
    mock_redis = AsyncMock()
    mock_redis.get.return_value = None
    
    # Setup service
    service = TestCrunchbaseService(client=mock_client, redis=mock_redis)
    
    # Setup mock responses
    mock_client.get_company.return_value = Company(**SAMPLE_COMPANY_DATA)
    mock_client.get_company_funding_rounds.return_value = [
        FundingRound(**r) for r in SAMPLE_FUNDING_ROUNDS
    ]
    
    # Call the method
    company_id = SAMPLE_COMPANY_DATA["uuid"]
    result = await service.get_company_funding(company_id)
    
    # Assertions
    assert result is not None
    assert result["company_name"] == SAMPLE_COMPANY_DATA["name"]
    assert len(result["funding_rounds"]) == len(SAMPLE_FUNDING_ROUNDS)
    mock_client.get_company.assert_awaited_once_with(company_id)
    mock_client.get_company_funding_rounds.assert_awaited_once_with(company_id)
    mock_redis.set.assert_awaited()
    print("✓ test_get_company_funding_success passed")

async def test_refresh_company_cache():
    """Test refreshing company cache."""
    # Setup mocks
    mock_client = AsyncMock()
    mock_redis = AsyncMock()
    
    # Setup service
    service = TestCrunchbaseService(client=mock_client, redis=mock_redis)
    
    # Setup test data
    company_id = "test-123"
    expected_result = {"company_id": company_id, "data": "test"}
    
    # Patch the get_company_funding method
    async def mock_get_company_funding(company_id, use_cache=True):
        return expected_result
    
    service.get_company_funding = mock_get_company_funding
    
    # Call the method
    result = await service.refresh_company_cache(company_id)
    
    # Assertions
    assert result == expected_result
    mock_redis.delete.assert_called_once_with("test:crunchbase:company:funding:test-123")
    print("✓ test_refresh_company_cache passed")

async def test_service_context_manager():
    """Test the service context manager."""
    # Setup mocks
    mock_client = AsyncMock()
    mock_redis = AsyncMock()
    
    # Test context manager
    async with TestCrunchbaseService(client=mock_client, redis=mock_redis) as service:
        assert service is not None
    
    # Client should be closed when exiting context
    mock_client.close.assert_awaited_once()
    print("✓ test_service_context_manager passed")

async def test_error_handling():
    """Test error handling in service methods."""
    # Setup mocks
    mock_client = AsyncMock()
    mock_redis = AsyncMock()
    
    # Setup service
    service = TestCrunchbaseService(client=mock_client, redis=mock_redis)
    
    # Setup mock to raise an exception
    error_msg = "API Error"
    mock_client.get_company_by_domain.side_effect = Exception(error_msg)
    
    # Test that the error is propagated
    try:
        await service.get_company_by_domain("error.com")
        assert False, "Expected exception not raised"
    except Exception as e:
        assert error_msg in str(e)
    
    print("✓ test_error_handling passed")

# Run all tests
async def run_tests():
    """Run all tests."""
    print("\nRunning Crunchbase service tests...\n" + "="*50)
    
    tests = [
        test_get_company_by_domain_success,
        test_get_company_funding_success,
        test_refresh_company_cache,
        test_service_context_manager,
        test_error_handling
    ]
    
    for test in tests:
        try:
            await test()
        except Exception as e:
            print(f"✗ {test.__name__} failed: {str(e)}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "="*50)
    print("All tests completed!")

if __name__ == "__main__":
    asyncio.run(run_tests())
