"""Redis client and cache utilities."""
import json
import logging
from functools import wraps
from typing import Any, Callable, Optional, TypeVar, cast

import redis.asyncio as redis
from fastapi import Request
from pydantic import BaseModel

from app.core.config import settings

logger = logging.getLogger(__name__)

# Type variable for generic function return type
T = TypeVar('T')

# Global Redis connection pool
_redis_pool: Optional[redis.Redis] = None


def get_redis() -> redis.Redis:
    """Get Redis client instance.
    
    Returns:
        redis.Redis: Redis client instance
    """
    global _redis_pool
    if _redis_pool is None:
        raise RuntimeError("Redis client not initialized. Call init_redis() first.")
    return _redis_pool


async def init_redis() -> None:
    """Initialize Redis connection pool."""
    global _redis_pool
    if _redis_pool is not None:
        return
    
    # Convert Redis URL to string if it's a Pydantic model
    redis_url = str(settings.REDIS_URI)
    
    logger.info(f"Initializing Redis connection to {redis_url}")
    _redis_pool = redis.from_url(
        redis_url,
        encoding="utf-8",
        decode_responses=True,
        socket_connect_timeout=5,
        socket_keepalive=True,
        retry_on_timeout=True,
    )
    
    # Test the connection
    try:
        await _redis_pool.ping()
        logger.info("Successfully connected to Redis")
    except Exception as e:
        logger.error(f"Failed to connect to Redis: {e}")
        _redis_pool = None
        raise


async def close_redis() -> None:
    """Close Redis connection pool."""
    global _redis_pool
    if _redis_pool is not None:
        await _redis_pool.close()
        await _redis_pool.connection_pool.disconnect()
        _redis_pool = None
        logger.info("Redis connection closed")


def cache_key_builder(
    func: Callable[..., Any],
    *args: Any,
    prefix: str = "",
    **kwargs: Any
) -> str:
    """Generate a cache key for a function call.
    
    Args:
        func: The function being cached
        prefix: Optional prefix for the cache key
        *args: Positional arguments to the function
        **kwargs: Keyword arguments to the function
        
    Returns:
        str: Cache key string
    """
    # Convert args and kwargs to a stable string representation
    args_str = ":".join(str(arg) for arg in args if not isinstance(arg, (Request, BaseModel)))
    kwargs_str = ":".join(f"{k}={v}" for k, v in sorted(kwargs.items()) 
                          if not isinstance(v, (Request, BaseModel)))
    
    # Combine components
    key_parts = [
        prefix or "",
        func.__module__ or "",
        func.__qualname__,
        args_str,
        kwargs_str,
    ]
    
    # Remove empty parts and join with colons
    key = ":".join(part for part in key_parts if part)
    
    # Ensure key is not too long (Redis max key length is 512MB, but we'll be conservative)
    if len(key) > 200:
        import hashlib
        key = hashlib.sha256(key.encode()).hexdigest()
    
    return key


def cached(
    ttl: int = 300,
    key_prefix: str = "cache:",
    exclude_args: Optional[list[str]] = None,
):
    """Decorator to cache function results in Redis.
    
    Args:
        ttl: Time to live in seconds
        key_prefix: Prefix for cache keys
        exclude_args: List of argument names to exclude from cache key
        
    Returns:
        Decorator function
    """
    if exclude_args is None:
        exclude_args = []
    
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            # Skip caching if Redis is not available
            if _redis_pool is None:
                return await func(*args, **kwargs)
            
            # Filter out excluded arguments
            filtered_kwargs = {
                k: v for k, v in kwargs.items() 
                if k not in exclude_args
            }
            
            # Generate cache key
            key = cache_key_builder(
                func, 
                *args, 
                prefix=key_prefix,
                **filtered_kwargs
            )
            
            try:
                # Try to get from cache
                cached_result = await _redis_pool.get(key)
                if cached_result is not None:
                    logger.debug(f"Cache hit for key: {key}")
                    return json.loads(cached_result)
                
                # Cache miss, call the function
                logger.debug(f"Cache miss for key: {key}")
                result = await func(*args, **kwargs)
                
                # Cache the result
                if result is not None:
                    await _redis_pool.set(
                        key, 
                        json.dumps(result, default=str), 
                        ex=ttl
                    )
                
                return result
                
            except Exception as e:
                logger.error(f"Cache error for key {key}: {e}")
                # If there's an error with Redis, just call the function
                return await func(*args, **kwargs)
        
        return wrapper
    
    return decorator


async def invalidate_cache(prefix: str) -> int:
    """Invalidate all cache keys with the given prefix.
    
    Args:
        prefix: The prefix to match for invalidation
        
    Returns:
        int: Number of keys deleted
    """
    if _redis_pool is None:
        return 0
    
    try:
        # Find all keys matching the prefix
        keys = []
        cursor = "0"
        while cursor != 0:
            cursor, found_keys = await _redis_pool.scan(
                cursor=cursor, 
                match=f"{prefix}*"
            )
            keys.extend(found_keys)
        
        # Delete all matching keys
        if keys:
            return await _redis_pool.delete(*keys)
        return 0
    except Exception as e:
        logger.error(f"Error invalidating cache with prefix {prefix}: {e}")
        return 0


class RedisCache:
    """High-level Redis cache interface."""
    
    def __init__(self, prefix: str = "cache:", ttl: int = 300):
        """Initialize with a key prefix and default TTL.
        
        Args:
            prefix: Prefix for all cache keys
            ttl: Default TTL in seconds
        """
        self.prefix = prefix
        self.ttl = ttl
    
    async def get(self, key: str) -> Any:
        """Get a value from the cache.
        
        Args:
            key: Cache key (without prefix)
            
        Returns:
            The cached value or None
        """
        if _redis_pool is None:
            return None
            
        full_key = f"{self.prefix}{key}"
        value = await _redis_pool.get(full_key)
        if value is not None:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        return None
    
    async def set(
        self, 
        key: str, 
        value: Any, 
        ttl: Optional[int] = None
    ) -> bool:
        """Set a value in the cache.
        
        Args:
            key: Cache key (without prefix)
            value: Value to cache (must be JSON serializable)
            ttl: Optional TTL in seconds (overrides default)
            
        Returns:
            bool: True if successful
        """
        if _redis_pool is None:
            return False
            
        full_key = f"{self.prefix}{key}"
        ttl = ttl if ttl is not None else self.ttl
        
        try:
            serialized = json.dumps(value, default=str)
            return await _redis_pool.set(full_key, serialized, ex=ttl)
        except (TypeError, OverflowError) as e:
            logger.error(f"Error serializing value for cache: {e}")
            return False
    
    async def delete(self, key: str) -> int:
        """Delete a key from the cache.
        
        Args:
            key: Cache key (without prefix)
            
        Returns:
            int: Number of keys deleted
        """
        if _redis_pool is None:
            return 0
            
        full_key = f"{self.prefix}{key}"
        return await _redis_pool.delete(full_key)
    
    async def clear_prefix(self, prefix: str) -> int:
        """Clear all keys with the given prefix.
        
        Args:
            prefix: Prefix to match
            
        Returns:
            int: Number of keys deleted
        """
        return await invalidate_cache(f"{self.prefix}{prefix}")
    
    async def get_metrics(self) -> dict[str, Any]:
        """Get cache metrics.
        
        Returns:
            dict: Cache metrics including key count and memory usage
        """
        if _redis_pool is None:
            return {"status": "redis_not_initialized"}
            
        try:
            # Get all keys with our prefix
            keys = []
            cursor = "0"
            while cursor != 0:
                cursor, found_keys = await _redis_pool.scan(
                    cursor=cursor, 
                    match=f"{self.prefix}*"
                )
                keys.extend(found_keys)
            
            # Get memory usage for each key
            memory_usage = 0
            if keys:
                memory_usage = sum(
                    await _redis_pool.memory_usage(key) or 0 
                    for key in keys
                )
            
            return {
                "status": "ok",
                "key_count": len(keys),
                "memory_usage_bytes": memory_usage,
                "prefix": self.prefix,
            }
            
        except Exception as e:
            logger.error(f"Error getting cache metrics: {e}")
            return {"status": f"error: {str(e)}"}


# Global cache instance with default settings
cache = RedisCache()
