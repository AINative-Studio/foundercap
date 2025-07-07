"""Application configuration management."""
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from pydantic import AnyHttpUrl, EmailStr, HttpUrl, field_validator, Field, PostgresDsn, RedisDsn
from pydantic_settings import BaseSettings
from pydantic_core import Url


class Settings(BaseSettings):
    """Application settings."""

    # Application
    PROJECT_NAME: str = "FounderCap"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() in ("true", "1", "t")
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    TIMEZONE: str = os.getenv("TZ", "UTC")
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8
    
    # CORS
    BACKEND_CORS_ORIGINS: str = "http://localhost:3000,http://localhost:8000"

    # Database
    POSTGRES_SERVER: str = os.getenv("POSTGRES_SERVER", "localhost")
    POSTGRES_PORT: str = os.getenv("POSTGRES_PORT", "5432")
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "postgres")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "foundercap")
    DATABASE_URI: Optional[PostgresDsn] = None

    # Database connection pool settings
    DATABASE_POOL_SIZE: int = int(os.getenv("DATABASE_POOL_SIZE", "5"))
    DATABASE_MAX_OVERFLOW: int = int(os.getenv("DATABASE_MAX_OVERFLOW", "10"))
    DATABASE_POOL_RECYCLE: int = int(os.getenv("DATABASE_POOL_RECYCLE", "3600"))

    @field_validator("DATABASE_URI", mode="before")
    @classmethod
    def assemble_db_connection(cls, v: Optional[str], info) -> Any:
        """Assemble database connection string."""
        if isinstance(v, str):
            return v
        values = info.data if hasattr(info, 'data') else {}
        return str(Url.build(
            scheme="postgresql",
            username=values.get("POSTGRES_USER"),
            password=values.get("POSTGRES_PASSWORD"),
            host=values.get("POSTGRES_SERVER"),
            port=int(values.get("POSTGRES_PORT")),
            path=f"/{values.get('POSTGRES_DB') or ''}",
        ))

    # Redis
    REDIS_URL: RedisDsn = Field(
        default_factory=lambda: RedisDsn(
            f"redis://{os.getenv('REDIS_HOST', 'localhost')}:{os.getenv('REDIS_PORT', '6379')}/0"
        )
    )
    REDIS_CACHE_TTL: int = 3600
    USE_REDIS_CACHE: bool = True
    
    # LinkedIn
    LINKEDIN_EMAIL: Optional[str] = os.getenv("LINKEDIN_EMAIL")
    LINKEDIN_PASSWORD: Optional[str] = os.getenv("LINKEDIN_PASSWORD")
    LINKEDIN_HEADLESS: bool = os.getenv("LINKEDIN_HEADLESS", "true").lower() == "true"
    LINKEDIN_SKIP_LOGIN: bool = os.getenv("LINKEDIN_SKIP_LOGIN", "false").lower() == "true"
    LINKEDIN_TIMEOUT: int = int(os.getenv("LINKEDIN_TIMEOUT", "30000"))
    LINKEDIN_SLOW_MO: int = int(os.getenv("LINKEDIN_SLOW_MO", "100"))
    LINKEDIN_CACHE_TTL: int = int(os.getenv("LINKEDIN_CACHE_TTL", "86400"))

    # Celery
    CELERY_BROKER_URL: str = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/1")
    CELERY_RESULT_BACKEND: str = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/2")
    CELERY_TASK_SERIALIZER: str = "json"
    CELERY_RESULT_SERIALIZER: str = "json"
    CELERY_ACCEPT_CONTENT: List[str] = ["json"]
    CELERY_TIMEZONE: str = os.getenv("TZ", "UTC")
    CELERY_ENABLE_UTC: bool = True
    CELERY_TASK_TRACK_STARTED: bool = True
    CELERY_TASK_TIME_LIMIT: int = 30 * 60
    CELERY_TASK_SOFT_TIME_LIMIT: int = 25 * 60

    # Rate Limiting
    RATE_LIMIT: str = os.getenv("RATE_LIMIT", "100/minute")
    
    # External APIs
    CRUNCHBASE_API_KEY: str = os.getenv("CRUNCHBASE_API_KEY", "")
    CRUNCHBASE_API_URL: str = os.getenv("CRUNCHBASE_API_URL", "https://api.crunchbase.com/api/v4")
    CRUNCHBASE_RATE_LIMIT_DELAY: float = float(os.getenv("CRUNCHBASE_RATE_LIMIT_DELAY", "1.0"))
    CRUNCHBASE_MAX_RETRIES: int = int(os.getenv("CRUNCHBASE_MAX_RETRIES", "3"))
    CRUNCHBASE_BACKOFF_FACTOR: float = float(os.getenv("CRUNCHBASE_BACKOFF_FACTOR", "2.0"))

    AIRTABLE_API_KEY: str = os.getenv("AIRTABLE_API_KEY", "")
    AIRTABLE_BASE_ID: str = os.getenv("AIRTABLE_BASE_ID", "")
    AIRTABLE_TABLE_NAME: str = os.getenv("AIRTABLE_TABLE_NAME", "Companies")

    ZERODB_EMAIL: str = os.getenv("ZERODB_EMAIL", "")
    ZERODB_PASSWORD: str = os.getenv("ZERODB_PASSWORD", "")
    ZERODB_API_URL: str = os.getenv("ZERODB_API_URL", "https://api.ainative.studio/api/v1")
    
    LINKEDIN_EMAIL: str = os.getenv("LINKEDIN_EMAIL", "")
    LINKEDIN_PASSWORD: str = os.getenv("LINKEDIN_PASSWORD", "")
    
    # Web Scraping
    REQUEST_TIMEOUT: int = int(os.getenv("REQUEST_TIMEOUT", "30"))
    MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", "3"))
    RETRY_DELAY: int = int(os.getenv("RETRY_DELAY", "5"))
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = os.getenv(
        "LOG_FORMAT",
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # API Documentation
    API_DOCS_URL: str = os.getenv("API_DOCS_URL", "/docs")
    API_REDOC_URL: str = os.getenv("API_REDOC_URL", "/redoc")
    
    # Feature Flags
    ENABLE_SWAGGER_UI: bool = os.getenv("ENABLE_SWAGGER_UI", "True").lower() in ("true", "1", "t")
    ENABLE_REDOC: bool = os.getenv("ENABLE_REDOC", "False").lower() in ("true", "1", "t")
    
    model_config = {
        "case_sensitive": True,
    }


settings = Settings()
