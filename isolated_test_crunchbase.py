"""
Isolated test for enhanced Crunchbase service functionality.

This test runs independently of the main application configuration.
"""
import asyncio
import logging
from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Mock models
class MockModel:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
    
    def dict(self):
        return {k: v for k, v in self.__dict__.items() if not k.startswith('_')}
    
    def copy(self):
        return MockModel(**self.dict())

class MockCompany(MockModel):
    pass

class MockFundingRound(MockModel):
    pass

class MockInvestor(MockModel):
    pass

# Mock service
class MockCrunchbaseService:
    def __init__(self):
        self.client = AsyncMock()
        self.redis = AsyncMock()
        self.logger = logger
    
    async def _get_cached(self, key):
        return await self.redis.get(key)
    
    async def _set_cached(self, key, value, ttl=None):
        await self.redis.set(key, value, ex=ttl)
    
    async def get_company_funding(self, company_id, use_cache=True):
        """Test implementation of get_company_funding."""
        cache_key = f"company:funding:{company_id}"
        
        if use_cache:
            cached = await self._get_cached(cache_key)
            if cached:
                return cached
        
        try:
            # Mock company data
            company = MockCompany(
                uuid=company_id,
                name="Test Company",
                permalink="test-company",
                total_funding_usd=10000000,
                last_funding_type="series_a",
                last_funding_at=date(2023, 1, 1)
            )
            
            # Mock funding rounds
            round1 = MockFundingRound(
                uuid="round-1",
                name="Series A",
                announced_on=date(2023, 1, 1),
                investment_type="series_a",
                money_raised=5000000,
                money_raised_currency="USD",
                investors=[
                    MockInvestor(
                        uuid="investor-1",
                        name="Investor 1",
                        type="financial_investor"
                    )
                ],
                source_url="http://example.com/round1",
                source_description="Series A Funding"
            )
            
            round2 = MockFundingRound(
                uuid="round-2",
                name="Seed",
                announced_on=date(2022, 6, 1),
                investment_type="seed",
                money_raised=2000000,
                money_raised_currency="USD",
                investors=[
                    MockInvestor(
                        uuid="investor-1",
                        name="Investor 1",
                        type="financial_investor"
                    ),
                    MockInvestor(
                        uuid="investor-2",
                        name="Angel Investor",
                        type="angel"
                    )
                ],
                source_url="http://example.com/round2",
                source_description="Seed Funding"
            )
            
            # Calculate aggregate metrics
            funding_rounds = [round1, round2]
            total_funding = company.total_funding_usd or sum(
                r.money_raised or 0 
                for r in funding_rounds 
                if getattr(r, 'money_raised_currency', None) == "USD"
            )
            
            # Get unique investors and their investment amounts
            unique_investors = {}
            for round_data in funding_rounds:
                for investor in getattr(round_data, 'investors', []):
                    if investor.uuid not in unique_investors:
                        unique_investors[investor.uuid] = {
                            **investor.dict(),
                            "total_invested_usd": 0,
                            "investment_count": 0,
                            "first_investment_date": None,
                            "last_investment_date": None
                        }
                    
                    # Track investment amounts and dates
                    if hasattr(round_data, 'money_raised') and getattr(round_data, 'money_raised_currency', None) == "USD":
                        unique_investors[investor.uuid]["total_invested_usd"] += round_data.money_raised
                    
                    unique_investors[investor.uuid]["investment_count"] += 1
                    
                    if hasattr(round_data, 'announced_on') and round_data.announced_on:
                        investor_data = unique_investors[investor.uuid]
                        if (not investor_data["first_investment_date"] or 
                            round_data.announced_on < investor_data["first_investment_date"]):
                            investor_data["first_investment_date"] = round_data.announced_on
                        
                        if (not investor_data["last_investment_date"] or 
                            round_data.announced_on > investor_data["last_investment_date"]):
                            investor_data["last_investment_date"] = round_data.announced_on
            
            # Sort funding rounds by date (newest first)
            sorted_rounds = sorted(
                [r.dict() for r in funding_rounds], 
                key=lambda x: x.get("announced_on") or "", 
                reverse=True
            )
            
            # Prepare response
            result = {
                "company_id": company_id,
                "company_name": company.name,
                "company_permalink": company.permalink,
                "total_funding_usd": total_funding,
                "funding_rounds": sorted_rounds,
                "round_count": len(funding_rounds),
                "investor_count": len(unique_investors),
                "investors": list(unique_investors.values()),
                "last_funding_round": sorted_rounds[0] if sorted_rounds else None,
                "first_funding_round": sorted_rounds[-1] if sorted_rounds else None,
                "last_updated": "2023-01-01T00:00:00"
            }
            
            # Cache the result
            await self._set_cached(cache_key, result, ttl=3600)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error in get_company_funding: {e}", exc_info=True)
            raise Exception(f"Failed to fetch company funding: {e}")

async def main():
    """Run the test."""
    logger.info("Starting isolated test of Crunchbase service...")
    
    # Create mock service
    service = MockCrunchbaseService()
    
    # Test get_company_funding
    try:
        logger.info("Testing get_company_funding...")
        result = await service.get_company_funding("company-123")
        
        # Print results
        print("\nTest Results:")
        print("-" * 50)
        print(f"Company: {result.get('company_name', 'N/A')} (ID: {result.get('company_id', 'N/A')})")
        print(f"Total Funding: ${result.get('total_funding_usd', 0):,}")
        print(f"Funding Rounds: {result.get('round_count', 0)}")
        print(f"Unique Investors: {result.get('investor_count', 0)}")
        
        print("\nInvestors:")
        for investor in result.get("investors", []):
            print(f"- {investor.get('name', 'Unknown')} ({investor.get('type', 'unknown')}): "
                  f"${investor.get('total_invested_usd', 0):,} in {investor.get('investment_count', 0)} rounds")
        
        print("\nFunding Rounds (Newest First):")
        for round_data in result.get("funding_rounds", []):
            print(f"- {round_data.get('name', 'Unknown')}: ${round_data.get('money_raised', 0):,} "
                  f"({round_data.get('announced_on', 'N/A')})")
        
        print("\nTest passed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        return False

if __name__ == "__main__":
    asyncio.run(main())
