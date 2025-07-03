import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from app.main import app

client = TestClient(app)

@pytest.fixture
def mock_process_company_data():
    with patch("app.api.companies.process_company_data") as mock_task:
        mock_task.apply_async.return_value = MagicMock(id="test_task_id")
        yield mock_task

def test_trigger_process_company_data_success(mock_process_company_data):
    company_id = "test_company_id"
    permalink = "test-permalink"
    
    response = client.post(
        "/api/v1/companies/process-data",
        json={
            "company_id": company_id,
            "permalink": permalink
        }
    )
    
    assert response.status_code == 202
    assert response.json()["message"] == "Company data processing task initiated."
    assert response.json()["task_id"] == "test_task_id"
    mock_process_company_data.apply_async.assert_called_once_with(args=(company_id, permalink))

def test_trigger_process_company_data_missing_company_id():
    response = client.post(
        "/api/v1/companies/process-data",
        json={
            "permalink": "test-permalink"
        }
    )
    
    assert response.status_code == 422  # Unprocessable Entity
    assert "company_id" in response.json()["detail"][0]["loc"]

def test_trigger_process_company_data_no_permalink(mock_process_company_data):
    company_id = "test_company_id"
    
    response = client.post(
        "/api/v1/companies/process-data",
        json={
            "company_id": company_id
        }
    )
    
    assert response.status_code == 202
    assert response.json()["message"] == "Company data processing task initiated."
    assert response.json()["task_id"] == "test_task_id"
    # Ensure permalink is passed as None when not provided
    mock_process_company_data.apply_async.assert_called_once_with(args=(company_id, None))