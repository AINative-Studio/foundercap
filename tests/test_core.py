#!/usr/bin/env python3
"""Test core functionality."""

import pytest
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime, timedelta

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Set environment variables before any imports
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
    "REDIS_HOST": "localhost",
    "REDIS_PORT": "6379",
    "REDIS_PASSWORD": "",
    "REDIS_DB": "0"
})


def test_config_initialization():
    """Test configuration initialization."""
    from app.core.config import Settings
    
    settings = Settings()
    
    assert settings.ENVIRONMENT == "testing"
    assert settings.DEBUG is True
    assert settings.DATABASE_POOL_RECYCLE == 3600
    assert settings.ACCESS_TOKEN_EXPIRE_MINUTES == 11520


def test_config_cors_origins():
    """Test CORS origins configuration."""
    from app.core.config import Settings
    
    # Test with default CORS origins
    with patch.dict(os.environ, {"BACKEND_CORS_ORIGINS": "http://localhost:3000,http://localhost:8000"}):
        settings = Settings()
        assert "http://localhost:3000" in settings.BACKEND_CORS_ORIGINS
        assert "http://localhost:8000" in settings.BACKEND_CORS_ORIGINS


def test_config_api_settings():
    """Test API configuration settings."""
    from app.core.config import Settings
    
    settings = Settings()
    
    assert settings.API_V1_STR == "/api/v1"
    assert hasattr(settings, 'PROJECT_NAME')
    assert hasattr(settings, 'VERSION')


def test_config_security_settings():
    """Test security configuration settings."""
    from app.core.config import Settings
    
    settings = Settings()
    
    assert hasattr(settings, 'SECRET_KEY')
    assert settings.ACCESS_TOKEN_EXPIRE_MINUTES == 11520


def test_config_linkedin_settings():
    """Test LinkedIn configuration settings."""
    from app.core.config import Settings
    
    settings = Settings()
    
    assert settings.LINKEDIN_HEADLESS is True
    assert settings.LINKEDIN_TIMEOUT == 30000
    assert settings.LINKEDIN_SLOW_MO == 100
    assert settings.LINKEDIN_CACHE_TTL == 86400


def test_config_celery_settings():
    """Test Celery configuration settings."""
    from app.core.config import Settings
    
    settings = Settings()
    
    assert settings.CELERY_TASK_TIME_LIMIT == 1800
    assert settings.CELERY_TASK_SOFT_TIME_LIMIT == 1500


def test_config_retry_settings():
    """Test retry configuration settings."""
    from app.core.config import Settings
    
    settings = Settings()
    
    assert settings.REQUEST_TIMEOUT == 30
    assert settings.RETRY_DELAY == 5


@pytest.mark.asyncio
async def test_redis_connection_init():
    """Test Redis connection initialization."""
    from app.core.redis import init_redis, close_redis
    
    with patch('app.core.redis.aioredis.from_url') as mock_from_url:
        mock_redis = AsyncMock()
        mock_redis.ping.return_value = True
        mock_from_url.return_value = mock_redis
        
        # Test initialization
        await init_redis()
        mock_from_url.assert_called_once()
        
        # Test closing
        await close_redis()


@pytest.mark.asyncio
async def test_redis_health_check():
    """Test Redis health check."""
    from app.core.redis import health_check
    
    with patch('app.core.redis.redis_client') as mock_client:
        mock_client.ping.return_value = True
        
        result = await health_check()
        assert result["status"] == "healthy"
        assert result["redis"] is True
        mock_client.ping.assert_called_once()


@pytest.mark.asyncio
async def test_redis_health_check_failure():
    """Test Redis health check failure."""
    from app.core.redis import health_check
    
    with patch('app.core.redis.redis_client') as mock_client:
        mock_client.ping.side_effect = Exception("Connection failed")
        
        result = await health_check()
        assert result["status"] == "unhealthy"
        assert result["redis"] is False
        assert "error" in result


@pytest.mark.asyncio
async def test_redis_set_get_operations():
    """Test Redis set and get operations."""
    from app.core.redis import set_key, get_key
    
    with patch('app.core.redis.redis_client') as mock_client:
        mock_client.set.return_value = True
        mock_client.get.return_value = b'"test_value"'
        
        # Test set operation
        result = await set_key("test_key", "test_value")
        assert result is True
        mock_client.set.assert_called_once()
        
        # Test get operation
        result = await get_key("test_key")
        assert result == "test_value"
        mock_client.get.assert_called_once_with("test_key")


@pytest.mark.asyncio
async def test_redis_set_with_ttl():
    """Test Redis set operation with TTL."""
    from app.core.redis import set_key_with_ttl
    
    with patch('app.core.redis.redis_client') as mock_client:
        mock_client.setex.return_value = True
        
        result = await set_key_with_ttl("test_key", "test_value", 3600)
        assert result is True
        mock_client.setex.assert_called_once_with("test_key", 3600, '"test_value"')


@pytest.mark.asyncio
async def test_redis_delete_operation():
    """Test Redis delete operation."""
    from app.core.redis import delete_key
    
    with patch('app.core.redis.redis_client') as mock_client:
        mock_client.delete.return_value = 1
        
        result = await delete_key("test_key")
        assert result == 1
        mock_client.delete.assert_called_once_with("test_key")


@pytest.mark.asyncio
async def test_redis_exists_operation():
    """Test Redis exists operation."""
    from app.core.redis import key_exists
    
    with patch('app.core.redis.redis_client') as mock_client:
        mock_client.exists.return_value = 1
        
        result = await key_exists("test_key")
        assert result is True
        mock_client.exists.assert_called_once_with("test_key")


@pytest.mark.asyncio
async def test_redis_clear_pattern():
    """Test Redis clear pattern operation."""
    from app.core.redis import clear_pattern
    
    with patch('app.core.redis.redis_client') as mock_client:
        mock_client.keys.return_value = [b"test_key_1", b"test_key_2"]
        mock_client.delete.return_value = 2
        
        result = await clear_pattern("test_key_*")
        assert result == 2
        mock_client.keys.assert_called_once_with("test_key_*")
        mock_client.delete.assert_called_once()


@pytest.mark.asyncio
async def test_redis_get_stats():
    """Test Redis statistics retrieval."""
    from app.core.redis import get_redis_stats
    
    with patch('app.core.redis.redis_client') as mock_client:
        mock_client.info.return_value = {
            "used_memory": 1024000,
            "used_memory_human": "1.02M",
            "connected_clients": 5,
            "total_commands_processed": 1000
        }
        
        result = await get_redis_stats()
        assert result["used_memory"] == 1024000
        assert result["connected_clients"] == 5
        assert result["total_commands_processed"] == 1000
        mock_client.info.assert_called_once()


def test_diff_engine_array_changes():
    """Test diff engine with array changes."""
    from app.core.diff import find_json_diff
    
    old_data = {"tags": ["tag1", "tag2"]}
    new_data = {"tags": ["tag1", "tag3"]}
    diff = find_json_diff(old_data, new_data)
    
    assert "tags" in diff
    assert diff["tags"] == (["tag1", "tag2"], ["tag1", "tag3"])


def test_diff_engine_deeply_nested():
    """Test diff engine with deeply nested changes."""
    from app.core.diff import find_json_diff
    
    old_data = {
        "level1": {
            "level2": {
                "level3": {
                    "value": "old"
                }
            }
        }
    }
    new_data = {
        "level1": {
            "level2": {
                "level3": {
                    "value": "new"
                }
            }
        }
    }
    diff = find_json_diff(old_data, new_data)
    
    assert "level1.level2.level3.value" in diff
    assert diff["level1.level2.level3.value"] == ("old", "new")


def test_diff_engine_mixed_types():
    """Test diff engine with mixed data types."""
    from app.core.diff import find_json_diff
    
    old_data = {
        "string_field": "text",
        "number_field": 42,
        "boolean_field": True,
        "array_field": [1, 2, 3],
        "object_field": {"key": "value"}
    }
    new_data = {
        "string_field": "updated text",
        "number_field": 43,
        "boolean_field": False,
        "array_field": [1, 2, 4],
        "object_field": {"key": "updated value"}
    }
    
    diff = find_json_diff(old_data, new_data)
    
    assert diff["string_field"] == ("text", "updated text")
    assert diff["number_field"] == (42, 43)
    assert diff["boolean_field"] == (True, False)
    assert diff["array_field"] == ([1, 2, 3], [1, 2, 4])
    assert diff["object_field.key"] == ("value", "updated value")


def test_diff_engine_null_values():
    """Test diff engine with null values."""
    from app.core.diff import find_json_diff
    
    old_data = {"field1": "value", "field2": None}
    new_data = {"field1": None, "field2": "value"}
    diff = find_json_diff(old_data, new_data)
    
    assert diff["field1"] == ("value", None)
    assert diff["field2"] == (None, "value")


def test_diff_engine_performance():
    """Test diff engine performance with large objects."""
    from app.core.diff import find_json_diff
    import time
    
    # Create large objects
    old_data = {}
    new_data = {}
    
    for i in range(100):
        old_data[f"field_{i}"] = f"value_{i}"
        new_data[f"field_{i}"] = f"value_{i}" if i % 2 == 0 else f"updated_value_{i}"
    
    start_time = time.time()
    diff = find_json_diff(old_data, new_data)
    end_time = time.time()
    
    # Should complete quickly (under 1 second)
    assert end_time - start_time < 1.0
    
    # Should find all the changed fields
    changed_count = sum(1 for i in range(100) if i % 2 != 0)
    assert len(diff) == changed_count


if __name__ == "__main__":
    pytest.main([__file__, "-v"])