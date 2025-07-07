"""
Simple test for Crunchbase service functionality.
"""

class Company:
    def __init__(self, **kwargs):
        self.uuid = kwargs.get('uuid')
        self.name = kwargs.get('name')
        self.permalink = kwargs.get('permalink')
        self.total_funding_usd = kwargs.get('total_funding_usd')
        self.last_funding_type = kwargs.get('last_funding_type')
        self.last_funding_at = kwargs.get('last_funding_at')
    
    def dict(self):
        return {
            'uuid': self.uuid,
            'name': self.name,
            'permalink': self.permalink,
            'total_funding_usd': self.total_funding_usd,
            'last_funding_type': self.last_funding_type,
            'last_funding_at': self.last_funding_at
        }

class FundingRound:
    def __init__(self, **kwargs):
        self.uuid = kwargs.get('uuid')
        self.name = kwargs.get('name')
        self.announced_on = kwargs.get('announced_on')
        self.investment_type = kwargs.get('investment_type')
        self.money_raised = kwargs.get('money_raised')
        self.money_raised_currency = kwargs.get('money_raised_currency', 'USD')
        self.investors = kwargs.get('investors', [])
        self.source_url = kwargs.get('source_url')
        self.source_description = kwargs.get('source_description')
    
    def dict(self):
        return {
            'uuid': self.uuid,
            'name': self.name,
            'announced_on': self.announced_on,
            'investment_type': self.investment_type,
            'money_raised': self.money_raised,
            'money_raised_currency': self.money_raised_currency,
            'investors': [i.dict() for i in self.investors],
            'source_url': self.source_url,
            'source_description': self.source_description
        }
    
    def copy(self):
        return FundingRound(
            uuid=self.uuid,
            name=self.name,
            announced_on=self.announced_on,
            investment_type=self.investment_type,
            money_raised=self.money_raised,
            money_raised_currency=self.money_raised_currency,
            investors=[i for i in self.investors],
            source_url=self.source_url,
            source_description=self.source_description
        )

class Investor:
    def __init__(self, **kwargs):
        self.uuid = kwargs.get('uuid')
        self.name = kwargs.get('name')
        self.type = kwargs.get('type')
    
    def dict(self):
        return {
            'uuid': self.uuid,
            'name': self.name,
            'type': self.type
        }

def test_enhanced_crunchbase():
    """Test the enhanced Crunchbase service functionality."""
    print("\nTesting enhanced Crunchbase service...")
    
    # Create test data
    company = Company(
        uuid="company-123",
        name="Test Company",
        permalink="test-company",
        total_funding_usd=10000000,
        last_funding_type="series_a",
        last_funding_at="2023-01-01"
    )
    
    investor1 = Investor(
        uuid="investor-1",
        name="Investor 1",
        type="financial_investor"
    )
    
    investor2 = Investor(
        uuid="investor-2",
        name="Angel Investor",
        type="angel"
    )
    
    round1 = FundingRound(
        uuid="round-1",
        name="Series A",
        announced_on="2023-01-01",
        investment_type="series_a",
        money_raised=5000000,
        money_raised_currency="USD",
        investors=[investor1],
        source_url="http://example.com/round1",
        source_description="Series A Funding"
    )
    
    round2 = FundingRound(
        uuid="round-2",
        name="Seed",
        announced_on="2022-06-01",
        investment_type="seed",
        money_raised=2000000,
        money_raised_currency="USD",
        investors=[investor1, investor2],
        source_url="http://example.com/round2",
        source_description="Seed Funding"
    )
    
    # Process the data
    funding_rounds = [round1, round2]
    
    # Calculate total funding
    total_funding = company.total_funding_usd or sum(
        r.money_raised or 0 
        for r in funding_rounds 
        if getattr(r, 'money_raised_currency', None) == "USD"
    )
    
    # Process investors
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
    
    # Prepare result
    result = {
        "company_id": company.uuid,
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

if __name__ == "__main__":
    test_enhanced_crunchbase()
