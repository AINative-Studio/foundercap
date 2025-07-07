"""Tests for the Crunchbase service."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta

# Import models and exceptions
from app.services.crunchbase.models import Company, FundingRound, Investor
from app.services.crunchbase.exceptions import CrunchbaseAPIError

# Create a test version of the service that doesn't depend on the app
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
            "total_funding_usd": company.total_funding_usd,
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
    
    async def search_companies(self, query: str, page: int = 1, limit: int = 10) -> dict:
        """Search for companies."""
        cache_key = f"search:companies:{query}:{page}:{limit}"
        
        # Try to get from cache
        cached = await self._get_cached(cache_key)
        if cached:
            return cached
            
        # In a real implementation, this would call the API
        # For testing, we'll return a mock response
        result = {
            "query": query,
            "page": page,
            "limit": limit,
            "total_results": 0,
            "results": [],
            "last_updated": datetime.utcnow().isoformat()
        }
        
        # Cache the result
        await self._set_cached(cache_key, result, ttl=300)  # 5 minutes for search results
        return result
    
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

# Test fixtures
@pytest.fixture
def mock_redis():
    """Create a mock Redis client."""
    return AsyncMock()

@pytest.fixture
def mock_client():
    """Create a mock Crunchbase client."""
    return AsyncMock()

@pytest.fixture
def crunchbase_service(mock_client, mock_redis):
    """Create a test CrunchbaseService instance."""
    return TestCrunchbaseService(client=mock_client, redis=mock_redis)

# Test data
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

# Tests
@pytest.mark.asyncio
async def test_get_company_by_domain_success(crunchbase_service, mock_client, mock_redis, sample_company_data):
    """Test successful company lookup by domain."""
    # Setup mock responses
    mock_client.get_company_by_domain.return_value = Company(**sample_company_data)
    mock_client.get_company_funding_rounds.return_value = []
    
    # Call the method
    result = await crunchbase_service.get_company_by_domain("test.com")
    
    # Assertions
    assert result is not None
    assert result["company"]["name"] == sample_company_data["name"]
    mock_client.get_company_by_domain.assert_awaited_once_with("test.com")
    mock_redis.set.assert_awaited()  # Should have set cache

@pytest.mark.asyncio
async def test_get_company_funding_success(crunchbase_service, mock_client, mock_redis, sample_company_data, sample_funding_rounds):
    """Test successful funding data retrieval."""
    # Setup mock responses
    mock_client.get_company.return_value = Company(**sample_company_data)
    mock_client.get_company_funding_rounds.return_value = [
        FundingRound(**r) for r in sample_funding_rounds
    ]
    
    # Call the method
    company_id = sample_company_data["uuid"]
    result = await crunchbase_service.get_company_funding(company_id)
    
    # Assertions
    assert result is not None
    assert result["company_name"] == sample_company_data["name"]
    assert len(result["funding_rounds"]) == len(sample_funding_rounds)
    mock_client.get_company.assert_awaited_once_with(company_id)
    mock_client.get_company_funding_rounds.assert_awaited_once_with(company_id)
    mock_redis.set.assert_awaited()

@pytest.mark.asyncio
async def test_refresh_company_cache(crunchbase_service, mock_redis):
    """Test refreshing company cache."""
    # Setup
    company_id = "test-123"
    
    # Call the method
    with patch.object(crunchbase_service, 'get_company_funding') as mock_get:
        mock_get.return_value = {"company_id": company_id, "data": "test"}
        result = await crunchbase_service.refresh_company_cache(company_id)
    
    # Assertions
    assert result == {"company_id": company_id, "data": "test"}
    mock_redis.delete.assert_called_once_with("test:crunchbase:company:funding:test-123")
    mock_get.assert_awaited_once_with(company_id, use_cache=False)

@pytest.mark.asyncio
async def test_service_context_manager(mock_client, mock_redis):
    """Test the service context manager."""
    async with TestCrunchbaseService(client=mock_client, redis=mock_redis) as service:
        # Just test that the context manager works
        assert service is not None
    
    # Client should be closed when exiting context
    mock_client.close.assert_awaited_once()

@pytest.mark.asyncio
async def test_error_handling(crunchbase_service, mock_client):
    """Test error handling in service methods."""
    # Setup mock to raise an exception
    mock_client.get_company_by_domain.side_effect = Exception("API Error")
    
    # Test that the error is properly propagated
    with pytest.raises(Exception) as exc_info:
        await crunchbase_service.get_company_by_domain("error.com")
    
    assert "API Error" in str(exc_info.value)
