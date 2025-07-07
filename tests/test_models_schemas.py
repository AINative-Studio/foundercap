#!/usr/bin/env python3
"""Test database models and schemas."""

import pytest
import os
import sys
from pathlib import Path
from datetime import datetime, date
from unittest.mock import patch, MagicMock

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


def test_crunchbase_model_company_validation():
    """Test Crunchbase Company model validation."""
    from app.services.crunchbase.models import Company
    
    # Test with all valid data
    company = Company(
        uuid="test-uuid-123",
        name="Test Company Inc",
        description="A comprehensive test company",
        founded_on="2020-01-15",
        total_funding_usd=5000000,
        employee_count=150,
        website="https://testcompany.com",
        linkedin_url="https://linkedin.com/company/test-company",
        crunchbase_url="https://crunchbase.com/organization/test-company"
    )
    
    assert company.uuid == "test-uuid-123"
    assert company.name == "Test Company Inc"
    assert company.description == "A comprehensive test company"
    assert company.founded_on == date(2020, 1, 15)
    assert company.total_funding_usd == 5000000
    assert company.employee_count == 150
    assert company.website == "https://testcompany.com"


def test_crunchbase_model_funding_round_validation():
    """Test Crunchbase FundingRound model validation."""
    from app.services.crunchbase.models import FundingRound, Investor
    
    # Create investors
    investor1 = Investor(uuid="inv-1", name="VC Fund 1", type="venture_capital")
    investor2 = Investor(uuid="inv-2", name="Angel Investor", type="angel_individual")
    
    # Test funding round with investors
    funding_round = FundingRound(
        uuid="round-uuid-123",
        name="Series A",
        announced_on="2021-06-15",
        money_raised=2000000,
        round_type="series_a",
        investors=[investor1, investor2]
    )
    
    assert funding_round.uuid == "round-uuid-123"
    assert funding_round.name == "Series A"
    assert funding_round.announced_on == date(2021, 6, 15)
    assert funding_round.money_raised == 2000000
    assert funding_round.round_type == "series_a"
    assert len(funding_round.investors) == 2
    assert funding_round.investors[0].name == "VC Fund 1"
    assert funding_round.investors[1].name == "Angel Investor"


def test_crunchbase_model_investor_types():
    """Test Crunchbase Investor model with different types."""
    from app.services.crunchbase.models import Investor
    
    # Test different investor types
    investor_types = [
        ("vc-fund-uuid", "Sequoia Capital", "venture_capital"),
        ("angel-uuid", "Reid Hoffman", "angel_individual"),
        ("pe-uuid", "KKR", "private_equity"),
        ("accelerator-uuid", "Y Combinator", "accelerator"),
        ("corp-uuid", "Google Ventures", "corporate_venture_capital")
    ]
    
    for uuid, name, investor_type in investor_types:
        investor = Investor(uuid=uuid, name=name, type=investor_type)
        assert investor.uuid == uuid
        assert investor.name == name
        assert investor.type == investor_type


def test_crunchbase_model_date_string_parsing():
    """Test date string parsing in Crunchbase models."""
    from app.services.crunchbase.models import Company, FundingRound
    
    # Test various date formats
    date_formats = [
        "2021-06-15",
        "2021-06-15T00:00:00Z",
        "2021-06-15T10:30:45.123Z",
        date(2021, 6, 15),
        datetime(2021, 6, 15, 10, 30, 45)
    ]
    
    for date_input in date_formats:
        company = Company(uuid="test", name="Test", founded_on=date_input)
        assert company.founded_on == date(2021, 6, 15)
        
        funding_round = FundingRound(uuid="test", name="Test", announced_on=date_input)
        assert funding_round.announced_on == date(2021, 6, 15)


def test_crunchbase_model_edge_cases():
    """Test Crunchbase model edge cases."""
    from app.services.crunchbase.models import Company, FundingRound, Investor
    
    # Test with None/empty values
    company = Company(uuid="test", name="")
    assert company.name == ""
    assert company.description is None
    assert company.total_funding_usd is None
    
    # Test with zero funding
    company_zero = Company(uuid="test2", name="Zero Funding", total_funding_usd=0)
    assert company_zero.total_funding_usd == 0
    
    # Test funding round with no money raised
    round_no_money = FundingRound(uuid="test-round", name="Bootstrap")
    assert round_no_money.money_raised is None
    assert round_no_money.investors == []
    
    # Test investor with minimal data
    minimal_investor = Investor(uuid="minimal", name="Minimal Investor")
    assert minimal_investor.type is None


def test_linkedin_model_company_validation():
    """Test LinkedIn Company model validation."""
    from app.services.linkedin.models import LinkedInCompany
    
    # Test comprehensive LinkedIn company data
    company = LinkedInCompany(
        name="LinkedIn Test Company",
        linkedin_url="https://linkedin.com/company/linkedin-test",
        website="https://linkedintest.com",
        description="A company for testing LinkedIn integration",
        tagline="Testing LinkedIn everywhere",
        company_size="51-200 employees",
        company_type="Private Company",
        employee_count=125,
        headquarters="San Francisco, CA, US",
        founded_year=2018
    )
    
    assert company.name == "LinkedIn Test Company"
    assert company.website == "https://linkedintest.com"
    assert company.description == "A company for testing LinkedIn integration"
    assert company.tagline == "Testing LinkedIn everywhere"
    assert company.company_size == "51-200 employees"
    assert company.employee_count == 125
    assert company.headquarters == "San Francisco, CA, US"
    assert company.founded_year == 2018


def test_linkedin_model_founded_year_validation():
    """Test LinkedIn model founded year validation."""
    from app.services.linkedin.models import LinkedInCompany
    from pydantic import ValidationError
    
    # Valid founded years
    valid_years = [1800, 1900, 2000, 2023, datetime.now().year]
    for year in valid_years:
        company = LinkedInCompany(
            name="Test Company",
            linkedin_url="https://linkedin.com/company/test",
            founded_year=year
        )
        assert company.founded_year == year
    
    # Invalid founded years should raise ValidationError
    invalid_years = [1799, datetime.now().year + 2, -1, 3000]
    for year in invalid_years:
        with pytest.raises(ValidationError):
            LinkedInCompany(
                name="Test Company",
                linkedin_url="https://linkedin.com/company/test",
                founded_year=year
            )


def test_linkedin_model_url_validation():
    """Test LinkedIn model URL validation."""
    from app.services.linkedin.models import LinkedInCompany
    from pydantic import ValidationError
    
    # Valid LinkedIn URLs
    valid_urls = [
        "https://linkedin.com/company/test",
        "https://www.linkedin.com/company/test-company",
        "https://linkedin.com/company/test-company-123"
    ]
    
    for url in valid_urls:
        company = LinkedInCompany(name="Test", linkedin_url=url)
        assert str(company.linkedin_url) == url
    
    # Invalid URLs should raise ValidationError
    invalid_urls = [
        "not-a-url",
        "https://example.com",
        "linkedin.com/company/test",  # Missing protocol
        ""
    ]
    
    for url in invalid_urls:
        with pytest.raises(ValidationError):
            LinkedInCompany(name="Test", linkedin_url=url)


def test_linkedin_model_minimal_requirements():
    """Test LinkedIn model with minimal required fields."""
    from app.services.linkedin.models import LinkedInCompany
    
    # Only required fields
    minimal_company = LinkedInCompany(
        name="Minimal Company",
        linkedin_url="https://linkedin.com/company/minimal"
    )
    
    assert minimal_company.name == "Minimal Company"
    assert str(minimal_company.linkedin_url) == "https://linkedin.com/company/minimal"
    assert minimal_company.website is None
    assert minimal_company.description is None
    assert minimal_company.employee_count is None
    assert minimal_company.founded_year is None


def test_linkedin_model_automatic_timestamps():
    """Test LinkedIn model automatic timestamp handling."""
    from app.services.linkedin.models import LinkedInCompany
    
    company = LinkedInCompany(
        name="Timestamp Test",
        linkedin_url="https://linkedin.com/company/timestamp-test"
    )
    
    # last_updated should be automatically set
    assert company.last_updated is not None
    assert isinstance(company.last_updated, datetime)
    
    # Should be recent (within last minute)
    time_diff = datetime.now() - company.last_updated
    assert time_diff.total_seconds() < 60


def test_linkedin_model_raw_data_handling():
    """Test LinkedIn model raw data handling."""
    from app.services.linkedin.models import LinkedInCompany
    
    raw_data = {
        "scraped_at": "2023-07-07T12:00:00Z",
        "source_url": "https://linkedin.com/company/test",
        "additional_info": {"followers": 1000, "posts": 50}
    }
    
    company = LinkedInCompany(
        name="Raw Data Test",
        linkedin_url="https://linkedin.com/company/raw-test",
        raw_data=raw_data
    )
    
    assert company.raw_data == raw_data
    assert company.raw_data["additional_info"]["followers"] == 1000


def test_linkedin_company_update_model():
    """Test LinkedIn company update model functionality."""
    from app.services.linkedin.models import LinkedInCompany, LinkedInCompanyUpdate
    
    # Create an update with changed fields
    update = LinkedInCompanyUpdate(
        name="Updated Company Name",
        linkedin_url="https://linkedin.com/company/updated",
        description="Updated description",
        changed_fields=["name", "description"]
    )
    
    assert update.name == "Updated Company Name"
    assert update.description == "Updated description"
    assert "name" in update.changed_fields
    assert "description" in update.changed_fields
    assert len(update.changed_fields) == 2


def test_config_model_validation():
    """Test configuration model validation."""
    from app.core.config import Settings
    
    # Test with various environment values
    test_env_vars = {
        "ENVIRONMENT": "testing",
        "DEBUG": "True",
        "DATABASE_POOL_RECYCLE": "7200",
        "ACCESS_TOKEN_EXPIRE_MINUTES": "1440",
        "LINKEDIN_TIMEOUT": "45000",
        "CELERY_TASK_TIME_LIMIT": "3600"
    }
    
    with patch.dict(os.environ, test_env_vars):
        settings = Settings()
        
        assert settings.ENVIRONMENT == "testing"
        assert settings.DEBUG is True
        assert settings.DATABASE_POOL_RECYCLE == 7200
        assert settings.ACCESS_TOKEN_EXPIRE_MINUTES == 1440
        assert settings.LINKEDIN_TIMEOUT == 45000
        assert settings.CELERY_TASK_TIME_LIMIT == 3600


def test_config_cors_origins_parsing():
    """Test CORS origins parsing in configuration."""
    from app.core.config import Settings
    
    # Test comma-separated CORS origins
    cors_origins = "http://localhost:3000,https://app.example.com,http://localhost:8080"
    
    with patch.dict(os.environ, {"BACKEND_CORS_ORIGINS": cors_origins}):
        settings = Settings()
        
        assert len(settings.BACKEND_CORS_ORIGINS) == 3
        assert "http://localhost:3000" in settings.BACKEND_CORS_ORIGINS
        assert "https://app.example.com" in settings.BACKEND_CORS_ORIGINS
        assert "http://localhost:8080" in settings.BACKEND_CORS_ORIGINS


def test_config_boolean_parsing():
    """Test boolean parsing in configuration."""
    from app.core.config import Settings
    
    # Test various boolean representations
    boolean_tests = [
        ("True", True),
        ("true", True),
        ("TRUE", True),
        ("1", True),
        ("False", False),
        ("false", False),
        ("FALSE", False),
        ("0", False),
        ("", False)
    ]
    
    for str_value, expected_bool in boolean_tests:
        with patch.dict(os.environ, {"DEBUG": str_value}):
            settings = Settings()
            assert settings.DEBUG is expected_bool


def test_config_integer_parsing():
    """Test integer parsing in configuration."""
    from app.core.config import Settings
    
    # Test various integer values
    integer_tests = [
        ("3600", 3600),
        ("0", 0),
        ("999999", 999999)
    ]
    
    for str_value, expected_int in integer_tests:
        with patch.dict(os.environ, {"DATABASE_POOL_RECYCLE": str_value}):
            settings = Settings()
            assert settings.DATABASE_POOL_RECYCLE == expected_int


if __name__ == "__main__":
    pytest.main([__file__, "-v"])