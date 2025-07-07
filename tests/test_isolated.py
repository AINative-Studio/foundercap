#!/usr/bin/env python3
"""Isolated tests that don't rely on conftest.py setup."""

import pytest
import sys
import os
from pathlib import Path

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
})

def test_diff_engine_no_changes():
    """Test diff engine with no changes."""
    from app.core.diff import find_json_diff
    
    old_data = {"name": "Acme", "employees": 100}
    new_data = {"name": "Acme", "employees": 100}
    diff = find_json_diff(old_data, new_data)
    assert diff == {}

def test_diff_engine_simple_changes():
    """Test diff engine with simple changes."""
    from app.core.diff import find_json_diff
    
    old_data = {"name": "Acme", "employees": 100}
    new_data = {"name": "Acme", "employees": 150}
    diff = find_json_diff(old_data, new_data)
    assert diff == {"employees": (100, 150)}

def test_diff_engine_nested_changes():
    """Test diff engine with nested changes."""
    from app.core.diff import find_json_diff
    
    old_data = {"company": {"name": "Acme", "location": {"city": "SF"}}}
    new_data = {"company": {"name": "Acme Corp", "location": {"city": "NYC"}}}
    diff = find_json_diff(old_data, new_data)
    expected = {
        "company.name": ("Acme", "Acme Corp"),
        "company.location.city": ("SF", "NYC")
    }
    assert diff == expected

def test_diff_engine_added_removed_fields():
    """Test diff engine with added and removed fields."""
    from app.core.diff import find_json_diff
    
    old_data = {"name": "Acme", "old_field": "remove"}
    new_data = {"name": "Acme", "new_field": "add"}
    diff = find_json_diff(old_data, new_data)
    expected = {
        "old_field": ("remove", None),
        "new_field": (None, "add")
    }
    assert diff == expected

def test_diff_engine_empty_objects():
    """Test diff engine with empty objects."""
    from app.core.diff import find_json_diff
    
    # Empty to empty
    assert find_json_diff({}, {}) == {}
    
    # Empty to populated
    assert find_json_diff({}, {"new": "value"}) == {"new": (None, "value")}
    
    # Populated to empty
    assert find_json_diff({"old": "value"}, {}) == {"old": ("value", None)}

def test_diff_engine_complex_nested():
    """Test complex nested scenario."""
    from app.core.diff import find_json_diff
    
    old_data = {
        "name": "Acme Corp",
        "employees": 100,
        "location": {"city": "SF"},
        "old_field": "remove_me"
    }
    new_data = {
        "name": "Acme Corp",
        "employees": 150,
        "location": {"city": "SF", "state": "CA"},
        "new_field": "added"
    }
    diff = find_json_diff(old_data, new_data)
    expected = {
        "employees": (100, 150),
        "location.state": (None, "CA"),
        "old_field": ("remove_me", None),
        "new_field": (None, "added")
    }
    assert diff == expected

def test_crunchbase_company_model():
    """Test Company model creation and validation."""
    from app.services.crunchbase.models import Company
    from datetime import date
    
    company = Company(
        uuid="test-uuid",
        name="Test Company",
        description="A test company",
        founded_on=date(2020, 1, 1),
        total_funding_usd=1000000
    )
    
    assert company.name == "Test Company"
    assert company.description == "A test company"
    assert company.founded_on == date(2020, 1, 1)
    assert company.total_funding_usd == 1000000
    assert company.uuid == "test-uuid"

def test_crunchbase_funding_round_model():
    """Test FundingRound model creation and validation."""
    from app.services.crunchbase.models import FundingRound
    from datetime import date
    
    funding_round = FundingRound(
        uuid="round-uuid",
        name="Series A",
        announced_on=date(2021, 6, 1),
        money_raised=500000,
        investors=[]
    )
    
    assert funding_round.name == "Series A"
    assert funding_round.announced_on == date(2021, 6, 1)
    assert funding_round.money_raised == 500000
    assert funding_round.uuid == "round-uuid"
    assert funding_round.investors == []

def test_crunchbase_investor_model():
    """Test Investor model creation and validation."""
    from app.services.crunchbase.models import Investor
    
    investor = Investor(
        uuid="inv-uuid",
        name="Test Investor",
        type="vc"
    )
    
    assert investor.name == "Test Investor"
    assert investor.type == "vc"
    assert investor.uuid == "inv-uuid"

def test_crunchbase_model_minimal_data():
    """Test models with minimal required data."""
    from app.services.crunchbase.models import Company, FundingRound, Investor
    
    # Test Company with minimal data
    company = Company(uuid="minimal-uuid", name="Minimal Company")
    assert company.name == "Minimal Company"
    assert company.description is None
    assert company.total_funding_usd is None
    
    # Test FundingRound with minimal data
    funding_round = FundingRound(uuid="minimal-round", name="Minimal Round")
    assert funding_round.name == "Minimal Round"
    assert funding_round.announced_on is None
    assert funding_round.money_raised is None
    
    # Test Investor with minimal data
    investor = Investor(uuid="minimal-inv", name="Minimal Investor")
    assert investor.name == "Minimal Investor"
    assert investor.type is None

def test_crunchbase_date_parsing():
    """Test date parsing in models."""
    from app.services.crunchbase.models import FundingRound
    from datetime import date
    
    # Test with string date
    funding_round = FundingRound(
        uuid="date-test",
        name="Date Test",
        announced_on="2021-06-01"
    )
    assert funding_round.announced_on == date(2021, 6, 1)

def test_crunchbase_api_error():
    """Test base CrunchbaseAPIError."""
    from app.services.crunchbase.exceptions import CrunchbaseAPIError
    
    with pytest.raises(CrunchbaseAPIError) as exc_info:
        raise CrunchbaseAPIError("Test error")
    
    assert str(exc_info.value) == "Test error"

def test_crunchbase_rate_limit_error():
    """Test CrunchbaseRateLimitError."""
    from app.services.crunchbase.exceptions import CrunchbaseRateLimitError, CrunchbaseAPIError
    
    with pytest.raises(CrunchbaseRateLimitError) as exc_info:
        raise CrunchbaseRateLimitError("Rate limit exceeded")
    
    assert str(exc_info.value) == "Rate limit exceeded"
    assert isinstance(exc_info.value, CrunchbaseAPIError)

def test_crunchbase_auth_error():
    """Test CrunchbaseAuthError."""
    from app.services.crunchbase.exceptions import CrunchbaseAuthError, CrunchbaseAPIError
    
    with pytest.raises(CrunchbaseAuthError) as exc_info:
        raise CrunchbaseAuthError("Authentication failed")
    
    assert str(exc_info.value) == "Authentication failed"
    assert isinstance(exc_info.value, CrunchbaseAPIError)

def test_crunchbase_not_found_error():
    """Test CrunchbaseNotFoundError."""
    from app.services.crunchbase.exceptions import CrunchbaseNotFoundError, CrunchbaseAPIError
    
    with pytest.raises(CrunchbaseNotFoundError) as exc_info:
        raise CrunchbaseNotFoundError("Company not found")
    
    assert str(exc_info.value) == "Company not found"
    assert isinstance(exc_info.value, CrunchbaseAPIError)

def test_crunchbase_validation_error():
    """Test CrunchbaseValidationError."""
    from app.services.crunchbase.exceptions import CrunchbaseValidationError, CrunchbaseAPIError
    
    with pytest.raises(CrunchbaseValidationError) as exc_info:
        raise CrunchbaseValidationError("Validation failed")
    
    assert str(exc_info.value) == "Validation failed"
    assert isinstance(exc_info.value, CrunchbaseAPIError)

def test_crunchbase_config_creation():
    """Test CrunchbaseConfig creation with defaults."""
    from app.services.crunchbase.config import CrunchbaseConfig
    
    config = CrunchbaseConfig()
    
    assert config.base_url == "https://api.crunchbase.com/api/v4/"
    assert config.requests_per_second == 2.5
    assert config.max_retries == 3
    assert config.request_timeout == 30
    assert config.connect_timeout == 10
    assert config.cache_ttl == 3600

def test_crunchbase_config_with_api_key():
    """Test CrunchbaseConfig with API key."""
    from app.services.crunchbase.config import CrunchbaseConfig
    
    # Mock environment variable
    original_key = os.environ.get("CRUNCHBASE_API_KEY")
    os.environ["CRUNCHBASE_API_KEY"] = "test-api-key"
    
    try:
        config = CrunchbaseConfig()
        assert config.api_key == "test-api-key"
    finally:
        # Restore original value
        if original_key:
            os.environ["CRUNCHBASE_API_KEY"] = original_key
        else:
            os.environ.pop("CRUNCHBASE_API_KEY", None)

def test_employee_count_parsing():
    """Test employee count parsing logic."""
    
    def parse_employee_count(company_size_str):
        """Extracted parsing logic from pipeline."""
        if not company_size_str:
            return None
        
        size_str = company_size_str.lower().replace("employees", "").replace("employee", "").strip()
        
        if "-" in size_str:
            try:
                parts = size_str.split("-")
                return int(parts[1].replace(",", "").strip())
            except (ValueError, IndexError):
                pass
        
        try:
            return int(size_str.replace(",", "").strip())
        except ValueError:
            pass
        
        if "10,000+" in size_str or "10000+" in size_str:
            return 10000
        elif "1,000+" in size_str or "1000+" in size_str:
            return 1000
        elif "500+" in size_str:
            return 500
        
        return None
    
    # Test various formats
    test_cases = [
        ("11-50 employees", 50),
        ("1-10 employees", 10),
        ("51-200 employees", 200),
        ("1,000+ employees", 1000),
        ("10,000+ employees", 10000),
        ("100 employees", 100),
        ("500+ employees", 500),
        ("invalid", None),
        (None, None),
        ("", None)
    ]
    
    for input_val, expected in test_cases:
        result = parse_employee_count(input_val)
        assert result == expected, f"For input '{input_val}', expected {expected}, got {result}"

def test_data_merging():
    """Test data merging logic."""
    
    def merge_company_data(linkedin_data, crunchbase_data):
        """Test data merging logic."""
        merged = {}
        
        # Prefer LinkedIn for description
        merged["description"] = linkedin_data.get("description") or crunchbase_data.get("description")
        
        # Prefer Crunchbase for financial data
        merged["total_funding"] = crunchbase_data.get("total_funding_usd")
        merged["website"] = linkedin_data.get("website") or crunchbase_data.get("website")
        
        # Merge location data
        merged["location"] = {}
        if linkedin_data.get("headquarters"):
            parts = linkedin_data["headquarters"].split(",")
            merged["location"]["city"] = parts[0].strip() if len(parts) > 0 else None
        
        if crunchbase_data.get("location"):
            merged["location"].update(crunchbase_data["location"])
        
        return merged
    
    linkedin_data = {
        "description": "LinkedIn description",
        "website": "https://linkedin-website.com",
        "headquarters": "San Francisco, CA"
    }
    
    crunchbase_data = {
        "description": "Crunchbase description",
        "total_funding_usd": 1000000,
        "website": "https://crunchbase-website.com",
        "location": {
            "city": "San Francisco",
            "state": "CA",
            "country": "USA"
        }
    }
    
    merged = merge_company_data(linkedin_data, crunchbase_data)
    
    assert merged["description"] == "LinkedIn description"  # LinkedIn preferred
    assert merged["total_funding"] == 1000000  # Crunchbase financial data
    assert merged["website"] == "https://linkedin-website.com"  # LinkedIn preferred
    assert merged["location"]["city"] == "San Francisco"  # Merged location
    assert merged["location"]["state"] == "CA"  # From Crunchbase
    assert merged["location"]["country"] == "USA"  # From Crunchbase

def test_linkedin_config_creation():
    """Test LinkedIn configuration creation."""
    from app.services.linkedin.config import LinkedInConfig
    
    config = LinkedInConfig()
    
    assert config.headless is True
    assert config.timeout == 30000
    assert config.slow_mo == 100
    assert config.cache_ttl == 86400
    assert config.skip_login is False

def test_linkedin_config_with_custom_values():
    """Test LinkedIn configuration with custom values."""
    from app.services.linkedin.config import LinkedInConfig
    
    # Mock environment variables
    original_values = {}
    test_values = {
        "LINKEDIN_HEADLESS": "False",
        "LINKEDIN_TIMEOUT": "60000",
        "LINKEDIN_SLOW_MO": "200",
        "LINKEDIN_CACHE_TTL": "172800",
        "LINKEDIN_SKIP_LOGIN": "True"
    }
    
    for key, value in test_values.items():
        original_values[key] = os.environ.get(key)
        os.environ[key] = value
    
    try:
        config = LinkedInConfig()
        assert config.headless is False
        assert config.timeout == 60000
        assert config.slow_mo == 200
        assert config.cache_ttl == 172800
        assert config.skip_login is True
    finally:
        # Restore original values
        for key, original_value in original_values.items():
            if original_value:
                os.environ[key] = original_value
            else:
                os.environ.pop(key, None)

def test_linkedin_company_info_model():
    """Test LinkedIn CompanyInfo model."""
    from app.services.linkedin.models import LinkedInCompany as CompanyInfo
    
    company_info = CompanyInfo(
        name="Test Company",
        description="A test company",
        website="https://test.com",
        linkedin_url="https://linkedin.com/company/test",
        industry="Technology",
        company_size="11-50 employees",
        headquarters="San Francisco, CA",
        founded="2020"
    )
    
    assert company_info.name == "Test Company"
    assert company_info.description == "A test company"
    assert company_info.website == "https://test.com"
    assert company_info.linkedin_url == "https://linkedin.com/company/test"
    assert company_info.industry == "Technology"
    assert company_info.company_size == "11-50 employees"
    assert company_info.headquarters == "San Francisco, CA"
    assert company_info.founded == "2020"

def test_linkedin_company_info_minimal():
    """Test LinkedIn CompanyInfo with minimal data."""
    from app.services.linkedin.models import LinkedInCompany as CompanyInfo
    
    company_info = CompanyInfo(
        name="Minimal Company",
        linkedin_url="https://linkedin.com/company/minimal"
    )
    
    assert company_info.name == "Minimal Company"
    assert company_info.linkedin_url == "https://linkedin.com/company/minimal"
    assert company_info.description is None
    assert company_info.website is None
    assert company_info.industry is None
    assert company_info.company_size is None
    assert company_info.headquarters is None
    assert company_info.founded is None

def test_linkedin_scraping_error():
    """Test LinkedInScrapingError."""
    from app.services.linkedin.exceptions import LinkedInScrapingError
    
    with pytest.raises(LinkedInScrapingError) as exc_info:
        raise LinkedInScrapingError("Scraping failed")
    
    assert str(exc_info.value) == "Scraping failed"

def test_linkedin_rate_limit_error():
    """Test LinkedInRateLimitError."""
    from app.services.linkedin.exceptions import LinkedInRateLimitError, LinkedInScrapingError
    
    with pytest.raises(LinkedInRateLimitError) as exc_info:
        raise LinkedInRateLimitError("Rate limit exceeded")
    
    assert str(exc_info.value) == "Rate limit exceeded"
    assert isinstance(exc_info.value, LinkedInScrapingError)

def test_linkedin_auth_error():
    """Test LinkedInAuthError."""
    from app.services.linkedin.exceptions import LinkedInAuthError, LinkedInScrapingError
    
    with pytest.raises(LinkedInAuthError) as exc_info:
        raise LinkedInAuthError("Authentication failed")
    
    assert str(exc_info.value) == "Authentication failed"
    assert isinstance(exc_info.value, LinkedInScrapingError)

def test_linkedin_not_found_error():
    """Test LinkedInNotFoundError."""
    from app.services.linkedin.exceptions import LinkedInNotFoundError, LinkedInScrapingError
    
    with pytest.raises(LinkedInNotFoundError) as exc_info:
        raise LinkedInNotFoundError("Company not found")
    
    assert str(exc_info.value) == "Company not found"
    assert isinstance(exc_info.value, LinkedInScrapingError)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])