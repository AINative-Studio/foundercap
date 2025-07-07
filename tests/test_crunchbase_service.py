"""Tests for the Crunchbase service functionality."""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, date

from app.services.crunchbase.service import CrunchbaseService
from app.services.crunchbase.models import Company, FundingRound, Investor
from app.services.crunchbase.exceptions import CrunchbaseAPIError


@pytest.fixture
def mock_crunchbase_client():
    """Create a mock Crunchbase client."""
    mock = AsyncMock()
    return mock


@pytest.fixture
def mock_redis():
    """Create a mock Redis client."""
    mock = AsyncMock()
    mock.get.return_value = None
    mock.set.return_value = True
    mock.delete.return_value = 1
    return mock


@pytest.fixture
def crunchbase_service(mock_crunchbase_client, mock_redis):
    """Create a Crunchbase service with mocked dependencies."""
    with patch('app.services.crunchbase.service.get_redis', return_value=mock_redis):
        service = CrunchbaseService(client=mock_crunchbase_client)
        return service


class TestCrunchbaseService:
    """Test the Crunchbase service functionality."""
    
    @pytest.mark.asyncio
    async def test_get_company_by_domain_success(self, crunchbase_service, mock_crunchbase_client):
        """Test successful company lookup by domain."""
        # Mock company data
        mock_company = Company(
            uuid="test-uuid",
            name="Test Company",
            description="A test company",
            homepage_url="https://test.com",
            founded_on=date(2020, 1, 1),
            total_funding_usd=1000000
        )
        
        # Mock funding rounds
        mock_rounds = [
            FundingRound(
                uuid="round-1",
                name="Series A",
                announced_on=date(2021, 6, 1),
                money_raised=500000,
                investors=[]
            )
        ]
        
        mock_crunchbase_client.get_company_by_domain.return_value = mock_company
        mock_crunchbase_client.get_company_funding_rounds.return_value = mock_rounds
        
        result = await crunchbase_service.get_company_by_domain("test.com")
        
        assert result is not None
        assert result["company"]["name"] == "Test Company"
        assert result["company"]["total_funding_usd"] == 1000000
        assert len(result["funding_rounds"]) == 1
        
        # Verify client calls
        mock_crunchbase_client.get_company_by_domain.assert_called_once_with("test.com")
        mock_crunchbase_client.get_company_funding_rounds.assert_called_once_with("test-uuid")
    
    @pytest.mark.asyncio
    async def test_get_company_by_domain_not_found(self, crunchbase_service, mock_crunchbase_client):
        """Test company lookup when company is not found."""
        mock_crunchbase_client.get_company_by_domain.return_value = None
        
        result = await crunchbase_service.get_company_by_domain("nonexistent.com")
        
        assert result is None
        mock_crunchbase_client.get_company_by_domain.assert_called_once_with("nonexistent.com")
    
    @pytest.mark.asyncio
    async def test_search_companies(self, crunchbase_service):
        """Test company search functionality."""
        result = await crunchbase_service.search_companies("AI startup", limit=5)
        
        assert "query" in result
        assert "results" in result
        assert result["query"] == "AI startup"
        assert result["limit"] == 5