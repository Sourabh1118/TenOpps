"""
Redis connection management and caching utilities.

This module provides Redis connection pooling for both the Celery task queue
and the caching layer, along with utility functions for cache operations.
"""
import json
from typing import Any, Optional, Union
from datetime import timedelta
import redis
from redis.connection import ConnectionPool
from app.core.config import settings
from app.core.logging import logger


class RedisClient:
    """Redis client with connection pooling and caching utilities."""
    
    def __init__(self):
        """Initialize Redis connection pools."""
        self._broker_pool: Optional[ConnectionPool] = None
        self._cache_pool: Optional[ConnectionPool] = None
        self._broker_client: Optional[redis.Redis] = None
        self._cache_client: Optional[redis.Redis] = None
    
    def _create_pool(self, db: int) -> ConnectionPool:
        """
        Create a Redis connection pool.
        
        Args:
            db: Redis database number
            
        Returns:
            ConnectionPool instance
        """
        return ConnectionPool.from_url(
            settings.REDIS_URL,
            db=db,
            max_connections=20,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5,
            retry_on_timeout=True
        )
    
    def get_broker_client(self) -> redis.Redis:
        """
        Get Redis client for Celery broker (database 0).
        
        Returns:
            Redis client instance for task queue
        """
        if self._broker_client is None:
            if self._broker_pool is None:
                self._broker_pool = self._create_pool(db=0)
            self._broker_client = redis.Redis(connection_pool=self._broker_pool)
            logger.info("Redis broker client initialized")
        return self._broker_client
    
    def get_cache_client(self) -> redis.Redis:
        """
        Get Redis client for caching (database 1).
        
        Returns:
            Redis client instance for caching
        """
        if self._cache_client is None:
            if self._cache_pool is None:
                self._cache_pool = self._create_pool(db=settings.REDIS_CACHE_DB)
            self._cache_client = redis.Redis(connection_pool=self._cache_pool)
            logger.info("Redis cache client initialized")
        return self._cache_client
    
    def close(self):
        """Close all Redis connections and pools."""
        if self._broker_client:
            self._broker_client.close()
            self._broker_client = None
        if self._cache_client:
            self._cache_client.close()
            self._cache_client = None
        if self._broker_pool:
            self._broker_pool.disconnect()
            self._broker_pool = None
        if self._cache_pool:
            self._cache_pool.disconnect()
            self._cache_pool = None
        logger.info("Redis connections closed")
    
    async def health_check(self) -> dict:
        """
        Check health of Redis connections.
        
        Returns:
            Dictionary with health status for broker and cache
        """
        health = {
            "broker": {"status": "unhealthy", "error": None},
            "cache": {"status": "unhealthy", "error": None}
        }
        
        # Check broker connection
        try:
            broker = self.get_broker_client()
            broker.ping()
            health["broker"]["status"] = "healthy"
        except Exception as e:
            health["broker"]["error"] = str(e)
            logger.error(f"Redis broker health check failed: {e}")
        
        # Check cache connection
        try:
            cache = self.get_cache_client()
            cache.ping()
            health["cache"]["status"] = "healthy"
        except Exception as e:
            health["cache"]["error"] = str(e)
            logger.error(f"Redis cache health check failed: {e}")
        
        return health


# Global Redis client instance
redis_client = RedisClient()


class CacheManager:
    """Cache management utilities with TTL support."""
    
    def __init__(self, client: Optional[redis.Redis] = None):
        """
        Initialize cache manager.
        
        Args:
            client: Redis client instance (uses global cache client if None)
        """
        self._client = client
    
    @property
    def client(self) -> redis.Redis:
        """Get Redis client for cache operations."""
        if self._client is None:
            return redis_client.get_cache_client()
        return self._client
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found
        """
        try:
            value = self.client.get(key)
            if value is None:
                return None
            return json.loads(value)
        except json.JSONDecodeError:
            # Return raw value if not JSON
            return value
        except Exception as e:
            logger.error(f"Cache get error for key '{key}': {e}")
            return None
    
    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[Union[int, timedelta]] = None
    ) -> bool:
        """
        Set value in cache with optional TTL.
        
        Args:
            key: Cache key
            value: Value to cache (will be JSON serialized)
            ttl: Time to live in seconds or timedelta (None = no expiration)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Convert timedelta to seconds
            if isinstance(ttl, timedelta):
                ttl = int(ttl.total_seconds())
            
            # Serialize value to JSON
            if not isinstance(value, (str, bytes)):
                value = json.dumps(value)
            
            # Set with or without TTL
            if ttl:
                self.client.setex(key, ttl, value)
            else:
                self.client.set(key, value)
            
            return True
        except Exception as e:
            logger.error(f"Cache set error for key '{key}': {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """
        Delete value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if key was deleted, False otherwise
        """
        try:
            return bool(self.client.delete(key))
        except Exception as e:
            logger.error(f"Cache delete error for key '{key}': {e}")
            return False
    
    def exists(self, key: str) -> bool:
        """
        Check if key exists in cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if key exists, False otherwise
        """
        try:
            return bool(self.client.exists(key))
        except Exception as e:
            logger.error(f"Cache exists error for key '{key}': {e}")
            return False
    
    def get_ttl(self, key: str) -> Optional[int]:
        """
        Get remaining TTL for a key.
        
        Args:
            key: Cache key
            
        Returns:
            TTL in seconds, -1 if no expiration, -2 if key doesn't exist, None on error
        """
        try:
            return self.client.ttl(key)
        except Exception as e:
            logger.error(f"Cache TTL error for key '{key}': {e}")
            return None
    
    def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """
        Increment a counter in cache.
        
        Args:
            key: Cache key
            amount: Amount to increment by
            
        Returns:
            New value after increment, None on error
        """
        try:
            return self.client.incrby(key, amount)
        except Exception as e:
            logger.error(f"Cache increment error for key '{key}': {e}")
            return None
    
    def decrement(self, key: str, amount: int = 1) -> Optional[int]:
        """
        Decrement a counter in cache.
        
        Args:
            key: Cache key
            amount: Amount to decrement by
            
        Returns:
            New value after decrement, None on error
        """
        try:
            return self.client.decrby(key, amount)
        except Exception as e:
            logger.error(f"Cache decrement error for key '{key}': {e}")
            return None
    
    def clear_pattern(self, pattern: str) -> int:
        """
        Delete all keys matching a pattern.
        
        Args:
            pattern: Redis key pattern (e.g., "search:*")
            
        Returns:
            Number of keys deleted
        """
        try:
            keys = self.client.keys(pattern)
            if keys:
                return self.client.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Cache clear pattern error for pattern '{pattern}': {e}")
            return 0
    
    def get_many(self, keys: list[str]) -> dict[str, Any]:
        """
        Get multiple values from cache.
        
        Args:
            keys: List of cache keys
            
        Returns:
            Dictionary mapping keys to values (missing keys are omitted)
        """
        try:
            values = self.client.mget(keys)
            result = {}
            for key, value in zip(keys, values):
                if value is not None:
                    try:
                        result[key] = json.loads(value)
                    except json.JSONDecodeError:
                        result[key] = value
            return result
        except Exception as e:
            logger.error(f"Cache get_many error: {e}")
            return {}
    
    def set_many(
        self,
        mapping: dict[str, Any],
        ttl: Optional[Union[int, timedelta]] = None
    ) -> bool:
        """
        Set multiple values in cache.
        
        Args:
            mapping: Dictionary of key-value pairs
            ttl: Time to live in seconds or timedelta (applied to all keys)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Serialize all values
            serialized = {}
            for key, value in mapping.items():
                if not isinstance(value, (str, bytes)):
                    serialized[key] = json.dumps(value)
                else:
                    serialized[key] = value
            
            # Set all values
            self.client.mset(serialized)
            
            # Apply TTL if specified
            if ttl:
                if isinstance(ttl, timedelta):
                    ttl = int(ttl.total_seconds())
                for key in serialized.keys():
                    self.client.expire(key, ttl)
            
            return True
        except Exception as e:
            logger.error(f"Cache set_many error: {e}")
            return False


# Global cache manager instance
cache = CacheManager()


def get_cache_key(prefix: str, *args, **kwargs) -> str:
    """
    Generate a cache key from prefix and arguments.
    
    Args:
        prefix: Key prefix (e.g., "search", "job")
        *args: Positional arguments to include in key
        **kwargs: Keyword arguments to include in key
        
    Returns:
        Cache key string
        
    Example:
        >>> get_cache_key("search", "python", location="remote")
        "search:python:location=remote"
    """
    parts = [prefix]
    parts.extend(str(arg) for arg in args)
    parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
    return ":".join(parts)
