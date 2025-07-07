"""Tests for the data pipeline service."""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from app.services.pipeline import DataPipelineService


@pytest.fixture
def mock_snapshot_service():
    """Mock snapshot service."""
    mock = AsyncMock()
    mock.get_latest_snapshot.return_value = None
    mock.save_snapshot.return_value = None
    mock.health_check.return_value = {"status": "healthy"}
    return mock


@pytest.fixture
def mock_linkedin_service():
    """Mock LinkedIn service."""
    mock = AsyncMock()
    mock.get_company_info.return_value = {
        "name": "Test Company",
        "description": "A test company",
        "website": "https://test.com",
        "linkedin_url": "https://linkedin.com/company/test",
        "industry": "Technology",
        "company_size": "11-50 employees",
        "headquarters": "San Francisco, CA"
    }
    return mock


@pytest.fixture
def mock_crunchbase_service():
    """Mock Crunchbase service."""
    mock = AsyncMock()
    mock.get_company_by_domain.return_value = {
        "company": {
            "name": "Test Company",
            "description": "A test company",
            "website": "https://test.com",
            "total_funding_usd": 1000000,
            "founded_year": 2020
        },
        "funding_rounds": [
            {
                "round_type": "series_a",
                "announced_date": "2021-06-01",
                "raised_amount": 1000000
            }
        ]
    }
    mock.search_companies.return_value = {"results": []}
    mock.close.return_value = None
    return mock


@pytest.fixture
def mock_airtable_updater():
    """Mock Airtable updater."""
    mock = AsyncMock()
    mock.update.return_value = {"id": "airtable-record-id"}
    mock._initialize.return_value = None
    mock._shutdown.return_value = None
    return mock


@pytest.fixture
def mock_zerodb_updater():
    """Mock ZeroDB updater."""
    mock = AsyncMock()
    mock.update.return_value = {"id": "zerodb-record-id"}
    mock._initialize.return_value = None
    mock._shutdown.return_value = None
    return mock


@pytest.fixture
def pipeline_service(
    mock_snapshot_service,
    mock_airtable_updater,
    mock_zerodb_updater
):
    """Create a pipeline service with mocked dependencies."""
    service = DataPipelineService()
    service.snapshot_service = mock_snapshot_service
    service.airtable_updater = mock_airtable_updater
    service.zerodb_updater = mock_zerodb_updater
    return service


class TestDataPipelineService:
    """Test the data pipeline service functionality."""
    
    @pytest.mark.asyncio
    async def test_initialize(self, pipeline_service):
        """Test pipeline initialization."""
        await pipeline_service.initialize()
        
        pipeline_service.snapshot_service._initialize.assert_called_once()
        pipeline_service.airtable_updater._initialize.assert_called_once()
        pipeline_service.zerodb_updater._initialize.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_shutdown(self, pipeline_service):
        """Test pipeline shutdown."""
        await pipeline_service.shutdown()
        
        pipeline_service.snapshot_service._shutdown.assert_called_once()
        pipeline_service.airtable_updater._shutdown.assert_called_once()
        pipeline_service.zerodb_updater._shutdown.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_process_company_new_company(
        self,
        pipeline_service,
        mock_linkedin_service,
        mock_crunchbase_service
    ):
        """Test processing a new company (no existing snapshot)."""
        # Mock services
        pipeline_service.linkedin_service = mock_linkedin_service
        pipeline_service.crunchbase_service = mock_crunchbase_service
        
        # No existing snapshot
        pipeline_service.snapshot_service.get_latest_snapshot.return_value = None
        
        result = await pipeline_service.process_company("Test Company", "test.com")
        
        assert result["status"] == "success"
        assert result["company"] == "Test Company"
        assert result["changes_count"] == 0  # New company, no changes to track
        assert "data" in result
        assert result["data"]["name"] == "Test Company"
        assert result["data"]["domain"] == "test.com"
        assert "linkedin" in result["data"]["sources"]
        assert "crunchbase" in result["data"]["sources"]
        
        # Verify snapshot was saved
        pipeline_service.snapshot_service.save_snapshot.assert_called_once()
        
        # Verify updaters were called
        pipeline_service.airtable_updater.update.assert_called_once()
        pipeline_service.zerodb_updater.update.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_process_company_with_changes(
        self,
        pipeline_service,
        mock_linkedin_service,
        mock_crunchbase_service
    ):
        """Test processing a company with changes from previous snapshot."""
        # Mock services
        pipeline_service.linkedin_service = mock_linkedin_service
        pipeline_service.crunchbase_service = mock_crunchbase_service
        
        # Existing snapshot with different data
        existing_snapshot = {
            "name": "Test Company",
            "domain": "test.com",
            "employee_count": 25,  # Will change to 50
            "total_funding": 500000,  # Will change to 1000000
            "sources": ["linkedin", "crunchbase"]
        }
        pipeline_service.snapshot_service.get_latest_snapshot.return_value = existing_snapshot
        
        result = await pipeline_service.process_company("Test Company", "test.com")
        
        assert result["status"] == "success"
        assert result["changes_count"] > 0
        assert "changes" in result
        
        # Check that changes were detected
        changes = result["changes"]
        assert "employee_count" in changes or "total_funding" in changes
    
    @pytest.mark.asyncio
    async def test_process_company_no_changes(
        self,
        pipeline_service,
        mock_linkedin_service,
        mock_crunchbase_service
    ):
        """Test processing a company with no changes."""
        # Mock services to return exactly the same data as snapshot
        mock_linkedin_service.get_company_info.return_value = {
            "name": "Test Company",
            "description": "A test company",
            "website": "https://test.com",
            "company_size": "11-50 employees"
        }
        mock_crunchbase_service.get_company_by_domain.return_value = {
            "company": {
                "name": "Test Company",
                "total_funding_usd": 1000000
            },
            "funding_rounds": []
        }
        
        pipeline_service.linkedin_service = mock_linkedin_service
        pipeline_service.crunchbase_service = mock_crunchbase_service
        
        # Create snapshot that matches the normalized data exactly
        existing_snapshot = {
            "name": "Test Company",
            "domain": "test.com",
            "description": "A test company",
            "website": "https://test.com",
            "employee_count": 50,
            "total_funding": 1000000,
            "sources": ["linkedin", "crunchbase"],
            "linkedin_data": mock_linkedin_service.get_company_info.return_value,
            "crunchbase_data": mock_crunchbase_service.get_company_by_domain.return_value,
            "collection_timestamp": datetime.utcnow().isoformat()
        }
        pipeline_service.snapshot_service.get_latest_snapshot.return_value = existing_snapshot
        
        result = await pipeline_service.process_company("Test Company", "test.com")
        
        # Should detect no changes and return early
        assert result["status"] == "no_changes"
        assert result["company"] == "Test Company"
        
        # Should not have called updaters since no changes
        pipeline_service.airtable_updater.update.assert_not_called()
        pipeline_service.zerodb_updater.update.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_process_company_no_data_found(
        self,
        pipeline_service,
        mock_linkedin_service,
        mock_crunchbase_service
    ):
        """Test processing a company when no data can be found."""
        # Mock services to return no data
        mock_linkedin_service.get_company_info.return_value = None
        mock_crunchbase_service.get_company_by_domain.return_value = None
        mock_crunchbase_service.search_companies.return_value = {"results": []}
        
        pipeline_service.linkedin_service = mock_linkedin_service
        pipeline_service.crunchbase_service = mock_crunchbase_service
        
        result = await pipeline_service.process_company("Nonexistent Company")
        
        assert result["status"] == "no_data"
        assert result["company"] == "Nonexistent Company"
    
    @pytest.mark.asyncio
    async def test_process_company_already_processing(self, pipeline_service):
        """Test that concurrent processing of same company is prevented."""
        # Add company to active processes
        pipeline_service._active_processes.add("test-company")
        
        result = await pipeline_service.process_company("Test Company")
        
        assert result["status"] == "already_processing"
        assert result["company"] == "Test Company"
    
    @pytest.mark.asyncio
    async def test_process_companies_batch(
        self,
        pipeline_service,
        mock_linkedin_service,
        mock_crunchbase_service
    ):
        """Test batch processing of multiple companies."""
        # Mock services
        pipeline_service.linkedin_service = mock_linkedin_service
        pipeline_service.crunchbase_service = mock_crunchbase_service
        
        companies = [
            {"name": "Company 1", "domain": "company1.com"},
            {"name": "Company 2", "domain": "company2.com"},
            {"name": "Company 3"}  # No domain
        ]
        
        results = await pipeline_service.process_companies_batch(companies, max_concurrent=2)
        
        assert len(results) == 3
        assert all("status" in result for result in results)
        assert all("company" in result for result in results)
    
    @pytest.mark.asyncio
    async def test_get_pipeline_status(self, pipeline_service):
        """Test getting pipeline status."""
        status = await pipeline_service.get_pipeline_status()
        
        assert status["pipeline_status"] == "active"
        assert "active_processes" in status
        assert "services" in status
        assert "timestamp" in status
        
        # Verify health check was called
        pipeline_service.snapshot_service.health_check.assert_called_once()
    
    def test_normalize_company_data(self, pipeline_service):
        """Test data normalization from multiple sources."""
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
        
        normalized = pipeline_service._normalize_company_data(raw_data)
        
        assert normalized["name"] == "Test Company"
        assert normalized["domain"] == "test.com"
        assert normalized["description"] == "LinkedIn description"  # LinkedIn takes precedence
        assert normalized["employee_count"] == 50  # Parsed from "11-50"
        assert normalized["industry"] == "Technology"
        assert normalized["founded_year"] == 2020
        assert normalized["total_funding"] == 1000000
        assert normalized["funding_stage"] == "series_a"
        assert normalized["location"]["city"] == "San Francisco"
        assert normalized["location"]["state"] == "CA"
        assert normalized["location"]["country"] == "USA"
    
    def test_parse_employee_count(self, pipeline_service):
        """Test employee count parsing from various formats."""
        assert pipeline_service._parse_employee_count("11-50 employees") == 50
        assert pipeline_service._parse_employee_count("1-10 employees") == 10
        assert pipeline_service._parse_employee_count("51-200 employees") == 200
        assert pipeline_service._parse_employee_count("1,000+ employees") == 1000
        assert pipeline_service._parse_employee_count("10,000+ employees") == 10000
        assert pipeline_service._parse_employee_count("100 employees") == 100
        assert pipeline_service._parse_employee_count("invalid") is None
        assert pipeline_service._parse_employee_count(None) is None