"""Tests for the enhanced Crunchbase service functionality."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import date, datetime
from app.services.crunchbase import (
    CrunchbaseService,
    Company,
    FundingRound,
    Investor,
    CrunchbaseAPIError
)
from app.services.crunchbase.factory import get_crunchbase_service

@pytest.fixture
async def mock_redis():
    with patch('app.core.redis.get_redis') as mock_redis:
        mock_redis.return_value = AsyncMock()
        yield mock_redis.return_value

@pytest.fixture
async def crunchbase_service(mock_redis):
    """Fixture providing a CrunchbaseService instance with mocked dependencies."""
    with patch('app.services.crunchbase.client.CrunchbaseClient') as mock_client:
        mock_client.return_value = AsyncMock()
        service = await get_crunchbase_service()
        service.client = mock_client.return_value
        yield service
        await service.close()

@pytest.mark.asyncio
async def test_get_company_funding_with_detailed_rounds(crunchbase_service):
    """Test getting detailed funding information for a company."""
    # Mock company data
    company = Company(
        uuid="company-123",
        name="Test Company",
        permalink="test-company",
        total_funding_usd=10000000,
        last_funding_type="series_a",
        last_funding_at=date(2023, 1, 1)
    )
    
    # Mock funding rounds
    round1 = FundingRound(
        uuid="round-1",
        name="Series A",
        announced_on=date(2023, 1, 1),
        investment_type="series_a",
        money_raised=5000000,
        money_raised_currency="USD",
        investors=[
            Investor(
                uuid="investor-1",
                name="Investor 1",
                type="financial_investor"
            )
        ]
    )
    
    round2 = FundingRound(
        uuid="round-2",
        name="Seed",
        announced_on=date(2022, 6, 1),
        investment_type="seed",
        money_raised=2000000,
        money_raised_currency="USD",
        investors=[
            Investor(
                uuid="investor-1",
                name="Investor 1",
                type="financial_investor"
            ),
            Investor(
                uuid="investor-2",
                name="Angel Investor",
                type="angel"
            )
        ]
    )
    
    # Set up mocks
    crunchbase_service.client.get_company.return_value = company
    crunchbase_service.client.get_company_funding_rounds.return_value = [round1, round2]
    
    # Mock detailed round information
    detailed_round1 = round1.copy()
    detailed_round1.source_url = "http://example.com/round1"
    detailed_round1.source_description = "Series A Funding"
    
    detailed_round2 = round2.copy()
    detailed_round2.source_url = "http://example.com/round2"
    detailed_round2.source_description = "Seed Funding"
    
    crunchbase_service.client.get_funding_round_details.side_effect = [
        detailed_round1,
        detailed_round2
    ]
    
    # Call the method
    result = await crunchbase_service.get_company_funding("company-123")
    
    # Assertions
    assert result is not None
    assert result["company_id"] == "company-123"
    assert result["company_name"] == "Test Company"
    assert result["total_funding_usd"] == 10000000
    assert len(result["funding_rounds"]) == 2
    assert len(result["investors"]) == 2  # Should have 2 unique investors
    
    # Verify investor data
    investor1 = next(i for i in result["investors"] if i["uuid"] == "investor-1")
    assert investor1["investment_count"] == 2
    assert investor1["total_invested_usd"] == 7000000  # 5M + 2M
    assert investor1["first_investment_date"] == date(2022, 6, 1)
    assert investor1["last_investment_date"] == date(2023, 1, 1)
    
    # Verify rounds are sorted by date (newest first)
    assert result["funding_rounds"][0]["uuid"] == "round-1"
    assert result["funding_rounds"][1]["uuid"] == "round-2"
    
    # Verify detailed round information
    assert result["funding_rounds"][0]["source_url"] == "http://example.com/round1"
    assert result["funding_rounds"][1]["source_description"] == "Seed Funding"

@pytest.mark.asyncio
async def test_get_investor_portfolio(crunchbase_service):
    """Test getting an investor's portfolio."""
    # Mock investor data
    mock_investor = {
        "uuid": "investor-1",
        "name": "Test Investor",
        "type": "venture_capital",
        "website": "https://testinvestor.com",
        "description": "A test venture capital firm"
    }
    
    # Set up mocks
    crunchbase_service.client.get_investor_details.return_value = mock_investor
    
    # Call the method
    result = await crunchbase_service.get_investor_portfolio("investor-1")
    
    # Assertions
    assert result is not None
    assert result["investor_id"] == "investor-1"
    assert result["investor_name"] == "Test Investor"
    assert result["investor_type"] == "venture_capital"
    assert result["website"] == "https://testinvestor.com"
    assert result["description"] == "A test venture capital firm"
    assert result["total_investments"] == 0  # No investments in this mock
    
    # Verify cache was set
    assert await crunchbase_service._get_cached("investor:portfolio:investor-1") is not None

@pytest.mark.asyncio
async def test_get_company_funding_api_error(crunchbase_service):
    """Test error handling when fetching company funding fails."""
    # Mock API error
    crunchbase_service.client.get_company.side_effect = Exception("API Error")
    
    # Call the method and expect an exception
    with pytest.raises(CrunchbaseAPIError):
        await crunchbase_service.get_company_funding("company-123")
    
    # Verify error was logged
    assert "Error fetching funding data for company company-123" in str(crunchbase_service._logger.error.call_args)
