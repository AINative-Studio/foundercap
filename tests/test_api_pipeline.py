"""Tests for the pipeline API endpoints."""
import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def mock_pipeline():
    """Mock pipeline service."""
    mock = AsyncMock()
    mock.initialize.return_value = None
    mock.shutdown.return_value = None
    mock.process_company.return_value = {
        "status": "success",
        "company": "Test Company",
        "changes_count": 2,
        "changes": {"employees": (100, 150)},
        "data": {"name": "Test Company", "employees": 150}
    }
    mock.process_companies_batch.return_value = [
        {
            "status": "success",
            "company": "Company 1",
            "changes_count": 1
        },
        {
            "status": "error",
            "company": "Company 2",
            "error": "API error"
        }
    ]
    mock.get_pipeline_status.return_value = {
        "pipeline_status": "active",
        "active_processes": 0,
        "services": {"snapshot_service": {"status": "healthy"}}
    }
    return mock


class TestPipelineAPI:
    """Test the pipeline API endpoints."""
    
    def test_process_company_success(self, client, mock_pipeline):
        """Test successful company processing."""
        with patch('app.api.endpoints.pipeline.get_pipeline', return_value=mock_pipeline):
            response = client.post(
                "/api/v1/pipeline/process-company",
                json={
                    "name": "Test Company",
                    "domain": "test.com",
                    "force_update": False
                }
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "Test Company" in data["message"]
        assert data["result"]["status"] == "success"
        assert data["result"]["changes_count"] == 2
        
        # Verify pipeline was called correctly
        mock_pipeline.initialize.assert_called_once()
        mock_pipeline.process_company.assert_called_once_with(
            company_name="Test Company",
            company_domain="test.com",
            force_update=False
        )
    
    def test_process_company_minimal_request(self, client, mock_pipeline):
        """Test company processing with minimal request data."""
        with patch('app.api.endpoints.pipeline.get_pipeline', return_value=mock_pipeline):
            response = client.post(
                "/api/v1/pipeline/process-company",
                json={"name": "Test Company"}
            )
        
        assert response.status_code == 200
        
        # Verify default values were used
        mock_pipeline.process_company.assert_called_once_with(
            company_name="Test Company",
            company_domain=None,
            force_update=False
        )
    
    def test_process_company_validation_error(self, client):
        """Test validation error for invalid request."""
        response = client.post(
            "/api/v1/pipeline/process-company",
            json={}  # Missing required 'name' field
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_process_company_pipeline_error(self, client, mock_pipeline):
        """Test handling of pipeline errors."""
        mock_pipeline.process_company.side_effect = Exception("Pipeline error")
        
        with patch('app.api.endpoints.pipeline.get_pipeline', return_value=mock_pipeline):
            response = client.post(
                "/api/v1/pipeline/process-company",
                json={"name": "Test Company"}
            )
        
        assert response.status_code == 500
        data = response.json()
        assert "Pipeline error" in data["detail"]
    
    def test_process_batch_success(self, client, mock_pipeline):
        """Test successful batch processing."""
        with patch('app.api.endpoints.pipeline.get_pipeline', return_value=mock_pipeline):
            response = client.post(
                "/api/v1/pipeline/process-batch",
                json={
                    "companies": [
                        {"name": "Company 1", "domain": "company1.com"},
                        {"name": "Company 2"}
                    ],
                    "max_concurrent": 2
                }
            )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["summary"]["total_companies"] == 2
        assert data["summary"]["successful"] == 1
        assert data["summary"]["failed"] == 1
        assert len(data["results"]) == 2
        
        # Verify pipeline was called correctly
        mock_pipeline.initialize.assert_called_once()
        mock_pipeline.process_companies_batch.assert_called_once_with(
            companies=[
                {"name": "Company 1", "domain": "company1.com"},
                {"name": "Company 2"}
            ],
            max_concurrent=2
        )
    
    def test_process_batch_validation_error(self, client):
        """Test validation error for batch request."""
        response = client.post(
            "/api/v1/pipeline/process-batch",
            json={
                "companies": [],  # Empty list
                "max_concurrent": 15  # Exceeds maximum
            }
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_get_pipeline_status(self, client, mock_pipeline):
        """Test getting pipeline status."""
        with patch('app.api.endpoints.pipeline.get_pipeline', return_value=mock_pipeline):
            response = client.get("/api/v1/pipeline/status")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["status"]["pipeline_status"] == "active"
        assert "services" in data["status"]
        
        mock_pipeline.get_pipeline_status.assert_called_once()
    
    def test_initialize_pipeline(self, client, mock_pipeline):
        """Test pipeline initialization endpoint."""
        with patch('app.api.endpoints.pipeline.get_pipeline', return_value=mock_pipeline):
            response = client.post("/api/v1/pipeline/initialize")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "initialized successfully" in data["message"]
        
        mock_pipeline.initialize.assert_called_once()
    
    def test_shutdown_pipeline(self, client, mock_pipeline):
        """Test pipeline shutdown endpoint."""
        with patch('app.api.endpoints.pipeline.get_pipeline', return_value=mock_pipeline):
            response = client.post("/api/v1/pipeline/shutdown")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "shut down successfully" in data["message"]
        
        mock_pipeline.shutdown.assert_called_once()
    
    def test_force_update_parameter(self, client, mock_pipeline):
        """Test force_update parameter is passed correctly."""
        with patch('app.api.endpoints.pipeline.get_pipeline', return_value=mock_pipeline):
            response = client.post(
                "/api/v1/pipeline/process-company",
                json={
                    "name": "Test Company",
                    "force_update": True
                }
            )
        
        assert response.status_code == 200
        
        mock_pipeline.process_company.assert_called_once_with(
            company_name="Test Company",
            company_domain=None,
            force_update=True
        )
    
    def test_max_concurrent_limits(self, client, mock_pipeline):
        """Test max_concurrent parameter validation."""
        # Test minimum limit
        response = client.post(
            "/api/v1/pipeline/process-batch",
            json={
                "companies": [{"name": "Test"}],
                "max_concurrent": 0  # Below minimum
            }
        )
        assert response.status_code == 422
        
        # Test maximum limit  
        response = client.post(
            "/api/v1/pipeline/process-batch",
            json={
                "companies": [{"name": "Test"}],
                "max_concurrent": 15  # Above maximum
            }
        )
        assert response.status_code == 422
        
        # Test valid value
        with patch('app.api.endpoints.pipeline.get_pipeline', return_value=mock_pipeline):
            response = client.post(
                "/api/v1/pipeline/process-batch",
                json={
                    "companies": [{"name": "Test"}],
                    "max_concurrent": 5  # Valid
                }
            )
        assert response.status_code == 200