#!/usr/bin/env python3
"""Comprehensive test suite for FounderCap backend."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from datetime import date, datetime
import json
import asyncio


class TestDiffEngine:
    """Test cases for the diff engine."""
    
    def test_no_changes(self):
        """Test diff engine with no changes."""
        from app.core.diff import find_json_diff
        
        old_data = {"name": "Acme", "employees": 100}
        new_data = {"name": "Acme", "employees": 100}
        diff = find_json_diff(old_data, new_data)
        assert diff == {}
    
    def test_simple_changes(self):
        """Test diff engine with simple changes."""
        from app.core.diff import find_json_diff
        
        old_data = {"name": "Acme", "employees": 100}
        new_data = {"name": "Acme", "employees": 150}
        diff = find_json_diff(old_data, new_data)
        assert diff == {"employees": (100, 150)}
    
    def test_nested_changes(self):
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
    
    def test_added_removed_fields(self):
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
    
    def test_empty_objects(self):
        """Test diff engine with empty objects."""
        from app.core.diff import find_json_diff
        
        # Empty to empty
        assert find_json_diff({}, {}) == {}
        
        # Empty to populated
        assert find_json_diff({}, {"new": "value"}) == {"new": (None, "value")}
        
        # Populated to empty
        assert find_json_diff({"old": "value"}, {}) == {"old": ("value", None)}


class TestCrunchbaseModels:
    """Test cases for Crunchbase models."""
    
    def test_company_model(self):
        """Test Company model creation and validation."""
        from app.services.crunchbase.models import Company
        
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
    
    def test_funding_round_model(self):
        """Test FundingRound model creation and validation."""
        from app.services.crunchbase.models import FundingRound
        
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
    
    def test_investor_model(self):
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
    
    def test_model_minimal_data(self):
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
    
    def test_date_parsing(self):
        """Test date parsing in models."""
        from app.services.crunchbase.models import FundingRound
        
        # Test with string date
        funding_round = FundingRound(
            uuid="date-test",
            name="Date Test",
            announced_on="2021-06-01"
        )
        assert funding_round.announced_on == date(2021, 6, 1)


class TestCrunchbaseExceptions:
    """Test cases for Crunchbase exceptions."""
    
    def test_base_exception(self):
        """Test base CrunchbaseAPIError."""
        from app.services.crunchbase.exceptions import CrunchbaseAPIError
        
        with pytest.raises(CrunchbaseAPIError) as exc_info:
            raise CrunchbaseAPIError("Test error")
        
        assert str(exc_info.value) == "Test error"
    
    def test_rate_limit_exception(self):
        """Test CrunchbaseRateLimitError."""
        from app.services.crunchbase.exceptions import CrunchbaseRateLimitError, CrunchbaseAPIError
        
        with pytest.raises(CrunchbaseRateLimitError) as exc_info:
            raise CrunchbaseRateLimitError("Rate limit exceeded")
        
        assert str(exc_info.value) == "Rate limit exceeded"
        assert isinstance(exc_info.value, CrunchbaseAPIError)
    
    def test_auth_exception(self):
        """Test CrunchbaseAuthError."""
        from app.services.crunchbase.exceptions import CrunchbaseAuthError, CrunchbaseAPIError
        
        with pytest.raises(CrunchbaseAuthError) as exc_info:
            raise CrunchbaseAuthError("Authentication failed")
        
        assert str(exc_info.value) == "Authentication failed"
        assert isinstance(exc_info.value, CrunchbaseAPIError)
    
    def test_not_found_exception(self):
        """Test CrunchbaseNotFoundError."""
        from app.services.crunchbase.exceptions import CrunchbaseNotFoundError, CrunchbaseAPIError
        
        with pytest.raises(CrunchbaseNotFoundError) as exc_info:
            raise CrunchbaseNotFoundError("Company not found")
        
        assert str(exc_info.value) == "Company not found"
        assert isinstance(exc_info.value, CrunchbaseAPIError)
    
    def test_validation_exception(self):
        """Test CrunchbaseValidationError."""
        from app.services.crunchbase.exceptions import CrunchbaseValidationError, CrunchbaseAPIError
        
        with pytest.raises(CrunchbaseValidationError) as exc_info:
            raise CrunchbaseValidationError("Validation failed")
        
        assert str(exc_info.value) == "Validation failed"
        assert isinstance(exc_info.value, CrunchbaseAPIError)


class TestCrunchbaseConfig:
    """Test cases for Crunchbase configuration."""
    
    def test_config_creation(self):
        """Test CrunchbaseConfig creation with defaults."""
        from app.services.crunchbase.config import CrunchbaseConfig
        
        config = CrunchbaseConfig()
        
        assert config.base_url == "https://api.crunchbase.com/api/v4/"
        assert config.requests_per_second == 2.5
        assert config.max_retries == 3
        assert config.request_timeout == 30
        assert config.connect_timeout == 10
        assert config.cache_ttl == 3600
    
    def test_config_with_api_key(self):
        """Test CrunchbaseConfig with API key."""
        from app.services.crunchbase.config import CrunchbaseConfig
        import os
        
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


class TestPipelineService:
    """Test cases for the Pipeline service."""
    
    def test_employee_count_parsing(self):
        """Test employee count parsing logic."""
        from app.services.pipeline import DataPipelineService
        
        pipeline = DataPipelineService()
        
        # Test various formats
        assert pipeline._parse_employee_count("11-50 employees") == 50
        assert pipeline._parse_employee_count("1-10 employees") == 10
        assert pipeline._parse_employee_count("51-200 employees") == 200
        assert pipeline._parse_employee_count("1,000+ employees") == 1000
        assert pipeline._parse_employee_count("10,000+ employees") == 10000
        assert pipeline._parse_employee_count("100 employees") == 100
        assert pipeline._parse_employee_count("500+ employees") == 500
        assert pipeline._parse_employee_count("invalid") is None
        assert pipeline._parse_employee_count(None) is None
        assert pipeline._parse_employee_count("") is None
    
    def test_data_normalization(self):
        """Test data normalization logic."""
        from app.services.pipeline import DataPipelineService
        
        pipeline = DataPipelineService()
        
        raw_data = {
            "name": "Test Company",
            "domain": "test.com",
            "sources": ["linkedin", "crunchbase"],
            "linkedin_data": {
                "name": "Test Company",
                "description": "LinkedIn description",
                "company_size": "11-50 employees",
                "industry": "Technology",
                "headquarters": "San Francisco, CA",
                "founded": "2020"
            },
            "crunchbase_data": {
                "company": {
                    "name": "Test Company",
                    "description": "Crunchbase description",
                    "total_funding_usd": 1000000,
                    "location": {
                        "city": "San Francisco",
                        "region": "CA",
                        "country": "USA"
                    }
                },
                "funding_rounds": [
                    {
                        "round_type": "series_a",
                        "announced_date": "2021-06-01",
                        "raised_amount": 1000000
                    }
                ]
            }
        }
        
        normalized = pipeline._normalize_company_data(raw_data)
        
        assert normalized["name"] == "Test Company"
        assert normalized["domain"] == "test.com"
        assert normalized["description"] == "LinkedIn description"
        assert normalized["employee_count"] == 50
        assert normalized["industry"] == "Technology"
        assert normalized["founded_year"] == 2020
        assert normalized["total_funding"] == 1000000
        assert normalized["funding_stage"] == "series_a"
        assert normalized["location"]["city"] == "San Francisco"
        assert normalized["location"]["state"] == "CA"
        assert normalized["location"]["country"] == "USA"
    
    def test_data_merging(self):
        """Test data merging logic."""
        from app.services.pipeline import DataPipelineService
        
        pipeline = DataPipelineService()
        
        linkedin_data = {
            "description": "LinkedIn description",
            "website": "https://linkedin-website.com",
            "headquarters": "San Francisco, CA"
        }
        
        crunchbase_data = {
            "company": {
                "description": "Crunchbase description",
                "total_funding_usd": 1000000,
                "website": "https://crunchbase-website.com",
                "location": {
                    "city": "San Francisco",
                    "state": "CA",
                    "country": "USA"
                }
            }
        }
        
        merged = pipeline._merge_data_sources(linkedin_data, crunchbase_data)
        
        # LinkedIn description should be preferred
        assert merged["description"] == "LinkedIn description"
        # Crunchbase financial data should be used
        assert merged["total_funding"] == 1000000
        # LinkedIn website should be preferred
        assert merged["website"] == "https://linkedin-website.com"


class TestAPIEndpoints:
    """Test cases for API endpoints."""
    
    def test_health_endpoint(self, test_client):
        """Test health check endpoint."""
        response = test_client.get("/api/v1/health/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
    
    def test_health_detailed_endpoint(self, test_client):
        """Test detailed health check endpoint."""
        response = test_client.get("/api/v1/health/detailed")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "services" in data
        assert "timestamp" in data
    
    def test_pipeline_status_endpoint(self, test_client):
        """Test pipeline status endpoint."""
        response = test_client.get("/api/v1/pipeline/status")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "last_run" in data
        assert "stats" in data
    
    def test_pipeline_process_company_endpoint(self, test_client):
        """Test pipeline process company endpoint."""
        company_data = {
            "name": "Test Company",
            "domain": "test.com",
            "linkedin_url": "https://linkedin.com/company/test"
        }
        
        response = test_client.post("/api/v1/pipeline/process/company", json=company_data)
        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data
        assert data["status"] == "queued"
    
    def test_pipeline_process_batch_endpoint(self, test_client):
        """Test pipeline process batch endpoint."""
        batch_data = {
            "companies": [
                {
                    "name": "Test Company 1",
                    "domain": "test1.com",
                    "linkedin_url": "https://linkedin.com/company/test1"
                },
                {
                    "name": "Test Company 2", 
                    "domain": "test2.com",
                    "linkedin_url": "https://linkedin.com/company/test2"
                }
            ]
        }
        
        response = test_client.post("/api/v1/pipeline/process/batch", json=batch_data)
        assert response.status_code == 200
        data = response.json()
        assert "batch_id" in data
        assert data["status"] == "queued"
        assert len(data["job_ids"]) == 2
    
    def test_api_docs_endpoint(self, test_client):
        """Test API documentation endpoint."""
        response = test_client.get("/docs")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
    
    def test_openapi_schema_endpoint(self, test_client):
        """Test OpenAPI schema endpoint."""
        response = test_client.get("/openapi.json")
        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "info" in data
        assert "paths" in data


class TestErrorHandling:
    """Test cases for error handling."""
    
    def test_404_error(self, test_client):
        """Test 404 error handling."""
        response = test_client.get("/nonexistent/endpoint")
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
    
    def test_invalid_json_error(self, test_client):
        """Test invalid JSON error handling."""
        response = test_client.post(
            "/api/v1/pipeline/process/company",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422
    
    def test_missing_required_fields(self, test_client):
        """Test missing required fields error handling."""
        response = test_client.post("/api/v1/pipeline/process/company", json={})
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
    
    def test_validation_errors(self, test_client):
        """Test validation error handling."""
        invalid_data = {
            "name": "",  # Empty name should fail validation
            "domain": "invalid-domain",  # Invalid domain format
            "linkedin_url": "not-a-url"  # Invalid URL format
        }
        
        response = test_client.post("/api/v1/pipeline/process/company", json=invalid_data)
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data


class TestAsyncOperations:
    """Test cases for async operations."""
    
    @pytest.mark.asyncio
    async def test_async_linkedin_service(self, mock_linkedin_service):
        """Test async LinkedIn service operations."""
        result = await mock_linkedin_service.get_company_info("test.com")
        
        assert result["name"] == "Test Company"
        assert result["description"] == "A test company"
        assert result["website"] == "https://test.com"
        mock_linkedin_service.get_company_info.assert_called_once_with("test.com")
    
    @pytest.mark.asyncio
    async def test_async_crunchbase_service(self, mock_crunchbase_service):
        """Test async Crunchbase service operations."""
        result = await mock_crunchbase_service.get_company_by_domain("test.com")
        
        assert result["company"]["name"] == "Test Company"
        assert result["company"]["total_funding_usd"] == 1000000
        assert len(result["funding_rounds"]) == 1
        mock_crunchbase_service.get_company_by_domain.assert_called_once_with("test.com")
    
    @pytest.mark.asyncio
    async def test_async_redis_operations(self, mock_redis):
        """Test async Redis operations."""
        # Test setting and getting data
        await mock_redis.set("test_key", "test_value")
        result = await mock_redis.get("test_key")
        
        mock_redis.set.assert_called_once_with("test_key", "test_value")
        mock_redis.get.assert_called_once_with("test_key")
    
    @pytest.mark.asyncio
    async def test_pipeline_async_processing(self):
        """Test async pipeline processing."""
        from app.services.pipeline import DataPipelineService
        
        pipeline = DataPipelineService()
        
        # Test with mocked services
        with patch.object(pipeline, '_get_linkedin_data') as mock_linkedin, \
             patch.object(pipeline, '_get_crunchbase_data') as mock_crunchbase:
            
            mock_linkedin.return_value = {
                "name": "Test Company",
                "description": "LinkedIn description"
            }
            mock_crunchbase.return_value = {
                "company": {
                    "name": "Test Company",
                    "total_funding_usd": 1000000
                }
            }
            
            result = await pipeline.process_company("test.com")
            
            assert result["name"] == "Test Company"
            assert result["description"] == "LinkedIn description"
            assert result["total_funding"] == 1000000


class TestDataValidation:
    """Test cases for data validation."""
    
    def test_company_data_validation(self):
        """Test company data validation."""
        from app.models.company import Company
        from pydantic import ValidationError
        
        # Valid company data
        valid_data = {
            "name": "Test Company",
            "domain": "test.com",
            "description": "A test company",
            "employee_count": 50,
            "industry": "Technology",
            "founded_year": 2020,
            "total_funding": 1000000
        }
        
        company = Company(**valid_data)
        assert company.name == "Test Company"
        assert company.domain == "test.com"
        assert company.employee_count == 50
        
        # Invalid domain
        invalid_data = valid_data.copy()
        invalid_data["domain"] = "invalid-domain"
        
        with pytest.raises(ValidationError):
            Company(**invalid_data)
        
        # Invalid employee count
        invalid_data = valid_data.copy()
        invalid_data["employee_count"] = -10
        
        with pytest.raises(ValidationError):
            Company(**invalid_data)
    
    def test_founder_data_validation(self):
        """Test founder data validation."""
        from app.models.founder import Founder
        from pydantic import ValidationError
        
        # Valid founder data
        valid_data = {
            "name": "John Doe",
            "email": "john@test.com",
            "linkedin_url": "https://linkedin.com/in/johndoe",
            "role": "CEO",
            "company_domain": "test.com"
        }
        
        founder = Founder(**valid_data)
        assert founder.name == "John Doe"
        assert founder.email == "john@test.com"
        assert founder.role == "CEO"
        
        # Invalid email
        invalid_data = valid_data.copy()
        invalid_data["email"] = "invalid-email"
        
        with pytest.raises(ValidationError):
            Founder(**invalid_data)
        
        # Invalid LinkedIn URL
        invalid_data = valid_data.copy()
        invalid_data["linkedin_url"] = "not-a-url"
        
        with pytest.raises(ValidationError):
            Founder(**invalid_data)
    
    def test_funding_round_validation(self):
        """Test funding round validation."""
        from app.models.funding_round import FundingRound
        from pydantic import ValidationError
        
        # Valid funding round data
        valid_data = {
            "round_type": "series_a",
            "amount": 1000000,
            "announced_date": "2021-06-01",
            "company_domain": "test.com"
        }
        
        funding_round = FundingRound(**valid_data)
        assert funding_round.round_type == "series_a"
        assert funding_round.amount == 1000000
        
        # Invalid amount
        invalid_data = valid_data.copy()
        invalid_data["amount"] = -100000
        
        with pytest.raises(ValidationError):
            FundingRound(**invalid_data)
        
        # Invalid date format
        invalid_data = valid_data.copy()
        invalid_data["announced_date"] = "invalid-date"
        
        with pytest.raises(ValidationError):
            FundingRound(**invalid_data)


class TestServiceIntegration:
    """Test cases for service integration."""
    
    def test_linkedin_service_initialization(self):
        """Test LinkedIn service initialization."""
        from app.services.linkedin.service import LinkedInService
        
        service = LinkedInService()
        assert service.headless is True
        assert service.timeout == 30000
        assert service.slow_mo == 100
    
    def test_crunchbase_service_initialization(self):
        """Test Crunchbase service initialization."""
        from app.services.crunchbase.service import CrunchbaseService
        
        service = CrunchbaseService()
        assert service.config.base_url == "https://api.crunchbase.com/api/v4/"
        assert service.config.max_retries == 3
    
    def test_snapshot_service_initialization(self):
        """Test Snapshot service initialization."""
        from app.core.snapshot import SnapshotService
        
        service = SnapshotService()
        assert service.redis_client is not None
        assert service.memory_snapshots == {}
    
    def test_pipeline_service_initialization(self):
        """Test Pipeline service initialization."""
        from app.services.pipeline import DataPipelineService
        
        service = DataPipelineService()
        assert service.linkedin_service is not None
        assert service.crunchbase_service is not None
        assert service.snapshot_service is not None