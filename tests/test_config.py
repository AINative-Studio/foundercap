"""Test configuration for Crunchbase tests."""
from pydantic import PostgresDsn, RedisDsn
from pydantic_settings import BaseSettings

class TestSettings(BaseSettings):
    """Test settings that don't require environment variables."""
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/test_foundercap"
    TEST_DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/test_foundercap"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/1"
    
    # Crunchbase
    CRUNCHBASE_API_KEY: str = "test_api_key"
    CRUNCHBASE_REQUESTS_PER_SECOND: int = 10
    CRUNCHBASE_MAX_RETRIES: int = 3
    CRUNCHBASE_REQUEST_TIMEOUT: int = 30
    CRUNCHBASE_CONNECT_TIMEOUT: int = 10
    
    # Other settings
    DEBUG: bool = True
    TESTING: bool = True
    
    class Config:
        env_file = ".env.test"
        case_sensitive = True

test_settings = TestSettings()
