"""LinkedIn scraping configuration."""

import os
from typing import Optional
from pydantic import BaseModel


class LinkedInConfig(BaseModel):
    """Configuration for LinkedIn scraping."""
    
    # LinkedIn credentials
    email: Optional[str] = None
    password: Optional[str] = None
    
    # Browser settings
    headless: bool = True
    timeout: int = 30000  # milliseconds
    slow_mo: int = 100  # milliseconds between actions
    
    # Scraping settings
    skip_login: bool = False
    cache_ttl: int = 86400  # 24 hours
    max_retries: int = 3
    retry_delay: int = 5  # seconds
    
    def __init__(self, **kwargs):
        """Initialize LinkedIn configuration from environment variables."""
        # Load from environment
        env_config = {
            "email": os.getenv("LINKEDIN_EMAIL"),
            "password": os.getenv("LINKEDIN_PASSWORD"),
            "headless": os.getenv("LINKEDIN_HEADLESS", "True").lower() == "true",
            "timeout": int(os.getenv("LINKEDIN_TIMEOUT", "30000")),
            "slow_mo": int(os.getenv("LINKEDIN_SLOW_MO", "100")),
            "skip_login": os.getenv("LINKEDIN_SKIP_LOGIN", "False").lower() == "true",
            "cache_ttl": int(os.getenv("LINKEDIN_CACHE_TTL", "86400")),
            "max_retries": int(os.getenv("LINKEDIN_MAX_RETRIES", "3")),
            "retry_delay": int(os.getenv("LINKEDIN_RETRY_DELAY", "5")),
        }
        
        # Override with any provided kwargs
        env_config.update(kwargs)
        
        super().__init__(**env_config)
    
    @property
    def has_credentials(self) -> bool:
        """Check if LinkedIn credentials are configured."""
        return bool(self.email and self.password)
    
    @property
    def browser_options(self) -> dict:
        """Get browser options for Playwright."""
        return {
            "headless": self.headless,
            "timeout": self.timeout,
            "slow_mo": self.slow_mo,
        }