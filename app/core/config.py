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
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    
    # CORS
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        """Assemble CORS origins."""
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

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
    DATABASE_POOL_RECYCLE: int = int(os.getenv("DATABASE_POOL_RECYCLE", "3600"))  # 1 hour

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
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_PASSWORD: Optional[str] = os.getenv("REDIS_PASSWORD")
    REDIS_DB: int = int(os.getenv("REDIS_DB", "0"))
    REDIS_URI: Optional[RedisDsn] = None

    @field_validator("REDIS_URI", mode="before")
    @classmethod
    def assemble_redis_connection(cls, v: Optional[str], info) -> Any:
        """Assemble Redis connection string."""
        if isinstance(v, str):
            return v
        values = info.data if hasattr(info, 'data') else {}
        return str(Url.build(
            scheme="redis",
            username=None,
            password=values.get("REDIS_PASSWORD"),
            host=values.get("REDIS_HOST"),
            port=values.get("REDIS_PORT"),
            path=f"/{values.get('REDIS_DB', 0)}",
        ))

    # Celery
    CELERY_BROKER_URL: str = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/1")
    CELERY_RESULT_BACKEND: str = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/2")
    CELERY_TASK_SERIALIZER: str = "json"
    CELERY_RESULT_SERIALIZER: str = "json"
    CELERY_ACCEPT_CONTENT: List[str] = ["json"]
    CELERY_TIMEZONE: str = os.getenv("TZ", "UTC")
    CELERY_ENABLE_UTC: bool = True
    CELERY_TASK_TRACK_STARTED: bool = True
    CELERY_TASK_TIME_LIMIT: int = 30 * 60  # 30 minutes
    CELERY_TASK_SOFT_TIME_LIMIT: int = 25 * 60  # 25 minutes

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

    ZERODB_API_KEY: str = os.getenv("ZERODB_API_KEY", "")
    ZERODB_API_URL: str = os.getenv("ZERODB_API_URL", "https://api.ainative.studio/api/v1")
    
    LINKEDIN_EMAIL: str = os.getenv("LINKEDIN_EMAIL", "")
    LINKEDIN_PASSWORD: str = os.getenv("LINKEDIN_PASSWORD", "")
    
    # Web Scraping
    REQUEST_TIMEOUT: int = int(os.getenv("REQUEST_TIMEOUT", "30"))  # seconds
    MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", "3"))
    RETRY_DELAY: int = int(os.getenv("RETRY_DELAY", "5"))  # seconds
    
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
        "env_file": ".env",
        "env_file_encoding": "utf-8",
    }


settings = Settings()
