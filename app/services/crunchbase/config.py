"""Configuration for the Crunchbase API client."""
from pydantic import Field, validator
from pydantic_settings import BaseSettings
from typing import Optional

class CrunchbaseConfig(BaseSettings):
    """Configuration for Crunchbase API client."""
    
    # API Settings
    api_key: str = Field(..., env="CRUNCHBASE_API_KEY")
    base_url: str = "https://api.crunchbase.com/api/v4/"
    
    # Rate Limiting
    requests_per_second: float = 2.5  # Conservative default (40 requests per 15s window)
    max_retries: int = 3
    
    # Timeouts
    request_timeout: int = 30  # seconds
    connect_timeout: int = 10  # seconds
    
    # Caching
    cache_ttl: int = 3600  # 1 hour in seconds
    
    class Config:
        env_prefix = "CRUNCHBASE_"
        case_sensitive = False
    
    @validator("requests_per_second")
    def validate_requests_per_second(cls, v):
        if v <= 0 or v > 10:  # Enforce reasonable limits
            raise ValueError("requests_per_second must be between 0 and 10")
        return v
    
    @validator("max_retries")
    def validate_max_retries(cls, v):
        if v < 0 or v > 5:  # Enforce reasonable limits
            raise ValueError("max_retries must be between 0 and 5")
        return v

def get_crunchbase_config() -> CrunchbaseConfig:
    """Get the Crunchbase configuration."""
    return CrunchbaseConfig()
