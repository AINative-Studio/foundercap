"""Pytest configuration and fixtures."""
import sys
from pathlib import Path

# Add project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from fastapi.testclient import TestClient

from app.main import app


from app.core.config import settings

@pytest.fixture
def client():
    """Test client for the FastAPI application."""
    # Mock the settings for updaters to prevent ValueErrors during test setup
    original_airtable_api_key = settings.AIRTABLE_API_KEY
    original_airtable_base_id = settings.AIRTABLE_BASE_ID
    original_airtable_table_name = settings.AIRTABLE_TABLE_NAME
    original_zerodb_api_key = settings.ZERODB_API_KEY
    original_zerodb_api_url = settings.ZERODB_API_URL

    settings.AIRTABLE_API_KEY = "test_airtable_key"
    settings.AIRTABLE_BASE_ID = "test_airtable_base"
    settings.AIRTABLE_TABLE_NAME = "TestTable"
    settings.ZERODB_API_KEY = "test_zerodb_key"
    settings.ZERODB_API_URL = "http://test.zerodb.com"

    with TestClient(app) as test_client:
        yield test_client

    # Restore original settings after tests
    settings.AIRTABLE_API_KEY = original_airtable_api_key
    settings.AIRTABLE_BASE_ID = original_airtable_base_id
    settings.AIRTABLE_TABLE_NAME = original_airtable_table_name
    settings.ZERODB_API_KEY = original_zerodb_api_key
    settings.ZERODB_API_URL = original_zerodb_api_url
