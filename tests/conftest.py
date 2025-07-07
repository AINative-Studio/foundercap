"""Pytest configuration and fixtures."""
import sys
import os
from pathlib import Path
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

# Set up clean test environment BEFORE any imports
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
    "POSTGRES_SERVER": "localhost",
    "POSTGRES_PORT": "5432",
    "POSTGRES_USER": "test_user",
    "POSTGRES_PASSWORD": "test_password", 
    "POSTGRES_DB": "test_foundercap",
    "DATABASE_URL": "postgresql://test_user:test_password@localhost:5432/test_foundercap",
    "REDIS_HOST": "localhost",
    "REDIS_PORT": "6379",
    "AIRTABLE_API_KEY": "test_airtable_key",
    "AIRTABLE_BASE_ID": "test_base_id",
    "AIRTABLE_TABLE_NAME": "TestTable",
    "ZERODB_EMAIL": "test@test.com",
    "ZERODB_PASSWORD": "test_password",
    "ZERODB_API_URL": "http://test.zerodb.com",
    "CRUNCHBASE_API_KEY": "test_crunchbase_key",
    "LINKEDIN_EMAIL": "test@linkedin.com",
    "LINKEDIN_PASSWORD": "test_linkedin_pass"
})

# Add project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Mock external dependencies before importing
def mock_database_connection():
    """Mock database connection to avoid DB issues in tests."""
    mock_engine = MagicMock()
    mock_session = MagicMock()
    mock_base = MagicMock()
    
    with patch('app.db.session.create_engine', return_value=mock_engine):
        with patch('app.db.session.sessionmaker', return_value=mock_session):
            with patch('app.db.session.Base', mock_base):
                yield

@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Set up the test environment with mocked dependencies."""
    # Mock Redis
    mock_redis = AsyncMock()
    mock_redis.ping.return_value = True
    mock_redis.get.return_value = None
    mock_redis.set.return_value = True
    mock_redis.setex.return_value = True
    mock_redis.delete.return_value = 1
    
    with patch('app.core.redis.get_redis', return_value=mock_redis):
        with patch('app.db.session.create_engine'):
            with patch('app.db.session.sessionmaker'):
                yield

# Import after setting up environment
from fastapi.testclient import TestClient

# This will be imported after mocking is set up
@pytest.fixture
def app():
    """Get the FastAPI app for testing."""
    # Import here to ensure mocks are in place
    from app.main import app
    return app

@pytest.fixture
def client(app):
    """Test client for the FastAPI application."""
    with TestClient(app) as test_client:
        yield test_client

@pytest.fixture
def mock_redis():
    """Mock Redis client."""
    mock = AsyncMock()
    mock.ping.return_value = True
    mock.get.return_value = None
    mock.set.return_value = True
    mock.setex.return_value = True
    mock.delete.return_value = 1
    mock.keys.return_value = []
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
def sample_company_data():
    """Sample company data for testing."""
    return {
        "name": "Test Company",
        "domain": "test.com",
        "description": "A test company",
        "website": "https://test.com",
        "linkedin_url": "https://linkedin.com/company/test",
        "industry": "Technology",
        "employee_count": 50,
        "founded_year": 2020,
        "total_funding": 1000000,
        "funding_stage": "series_a",
        "location": {
            "city": "San Francisco",
            "state": "CA", 
            "country": "USA"
        }
    }

@pytest.fixture
def mock_settings():
    """Mock settings for testing."""
    return MagicMock()

@pytest.fixture
def test_client():
    """Test client for the FastAPI application."""
    # Import here to ensure mocks are in place
    from app.main import app
    
    with TestClient(app) as test_client:
        yield test_client
