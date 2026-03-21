"""
Unit tests for Redis connection and caching functionality.
"""
import pytest
from datetime import timedelta
from unittest.mock import Mock, patch, MagicMock
from app.core.redis import RedisClient, CacheManager, get_cache_key, redis_client, cache


class TestRedisClient:
    """Test RedisClient class."""
    
    def test_create_pool(self):
        """Test connection pool creation."""
        client = RedisClient()
        pool = client._create_pool(db=0)
        
        assert pool is not None
        assert pool.connection_kwargs['db'] == 0
        assert pool.max_connections == 20
    
    @patch('app.core.redis.redis.Redis')
    @patch('app.core.redis.ConnectionPool')
    def test_get_broker_client(self, mock_pool, mock_redis):
        """Test broker client initialization."""
        client = RedisClient()
        broker = client.get_broker_client()
        
        assert broker is not None
        assert client._broker_client is not None
        
        # Should return same instance on second call
        broker2 = client.get_broker_client()
        assert broker is broker2
    
    @patch('app.core.redis.redis.Redis')
    @patch('app.core.redis.ConnectionPool')
    def test_get_cache_client(self, mock_pool, mock_redis):
        """Test cache client initialization."""
        client = RedisClient()
        cache_client = client.get_cache_client()
        
        assert cache_client is not None
        assert client._cache_client is not None
        
        # Should return same instance on second call
        cache_client2 = client.get_cache_client()
        assert cache_client is cache_client2
    
    def test_close(self):
        """Test closing connections."""
        client = RedisClient()
        client._broker_client = Mock()
        client._cache_client = Mock()
        client._broker_pool = Mock()
        client._cache_pool = Mock()
        
        client.close()
        
        client._broker_client.close.assert_called_once()
        client._cache_client.close.assert_called_once()
        client._broker_pool.disconnect.assert_called_once()
        client._cache_pool.disconnect.assert_called_once()
        
        assert client._broker_client is None
        assert client._cache_client is None
        assert client._broker_pool is None
        assert client._cache_pool is None
    
    @pytest.mark.asyncio
    async def test_health_check_success(self):
        """Test health check with successful connections."""
        client = RedisClient()
        client._broker_client = Mock()
        client._cache_client = Mock()
        client._broker_client.ping.return_value = True
        client._cache_client.ping.return_value = True
        
        health = await client.health_check()
        
        assert health['broker']['status'] == 'healthy'
        assert health['cache']['status'] == 'healthy'
        assert health['broker']['error'] is None
        assert health['cache']['error'] is None
    
    @pytest.mark.asyncio
    async def test_health_check_failure(self):
        """Test health check with failed connections."""
        client = RedisClient()
        client._broker_client = Mock()
        client._cache_client = Mock()
        client._broker_client.ping.side_effect = Exception("Connection failed")
        client._cache_client.ping.side_effect = Exception("Connection failed")
        
        health = await client.health_check()
        
        assert health['broker']['status'] == 'unhealthy'
        assert health['cache']['status'] == 'unhealthy'
        assert 'Connection failed' in health['broker']['error']
        assert 'Connection failed' in health['cache']['error']


class TestCacheManager:
    """Test CacheManager class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_client = Mock()
        self.cache_manager = CacheManager(client=self.mock_client)
    
    def test_get_success(self):
        """Test successful cache get."""
        self.mock_client.get.return_value = '{"key": "value"}'
        
        result = self.cache_manager.get("test:key")
        
        assert result == {"key": "value"}
        self.mock_client.get.assert_called_once_with("test:key")
    
    def test_get_not_found(self):
        """Test cache get with missing key."""
        self.mock_client.get.return_value = None
        
        result = self.cache_manager.get("test:key")
        
        assert result is None
    
    def test_get_raw_value(self):
        """Test cache get with non-JSON value."""
        self.mock_client.get.return_value = "plain text"
        
        result = self.cache_manager.get("test:key")
        
        assert result == "plain text"
    
    def test_set_with_ttl(self):
        """Test cache set with TTL."""
        self.cache_manager.set("test:key", {"data": "value"}, ttl=300)
        
        self.mock_client.setex.assert_called_once()
        args = self.mock_client.setex.call_args[0]
        assert args[0] == "test:key"
        assert args[1] == 300
        assert '{"data": "value"}' in args[2]
    
    def test_set_with_timedelta_ttl(self):
        """Test cache set with timedelta TTL."""
        self.cache_manager.set("test:key", "value", ttl=timedelta(minutes=5))
        
        self.mock_client.setex.assert_called_once()
        args = self.mock_client.setex.call_args[0]
        assert args[1] == 300  # 5 minutes in seconds
    
    def test_set_without_ttl(self):
        """Test cache set without TTL."""
        self.cache_manager.set("test:key", "value")
        
        self.mock_client.set.assert_called_once_with("test:key", "value")
    
    def test_delete(self):
        """Test cache delete."""
        self.mock_client.delete.return_value = 1
        
        result = self.cache_manager.delete("test:key")
        
        assert result is True
        self.mock_client.delete.assert_called_once_with("test:key")
    
    def test_exists(self):
        """Test cache exists check."""
        self.mock_client.exists.return_value = 1
        
        result = self.cache_manager.exists("test:key")
        
        assert result is True
        self.mock_client.exists.assert_called_once_with("test:key")
    
    def test_get_ttl(self):
        """Test getting TTL."""
        self.mock_client.ttl.return_value = 120
        
        result = self.cache_manager.get_ttl("test:key")
        
        assert result == 120
        self.mock_client.ttl.assert_called_once_with("test:key")
    
    def test_increment(self):
        """Test counter increment."""
        self.mock_client.incrby.return_value = 15
        
        result = self.cache_manager.increment("test:counter", 5)
        
        assert result == 15
        self.mock_client.incrby.assert_called_once_with("test:counter", 5)
    
    def test_decrement(self):
        """Test counter decrement."""
        self.mock_client.decrby.return_value = 10
        
        result = self.cache_manager.decrement("test:counter", 5)
        
        assert result == 10
        self.mock_client.decrby.assert_called_once_with("test:counter", 5)
    
    def test_clear_pattern(self):
        """Test clearing keys by pattern."""
        self.mock_client.keys.return_value = ["test:1", "test:2", "test:3"]
        self.mock_client.delete.return_value = 3
        
        result = self.cache_manager.clear_pattern("test:*")
        
        assert result == 3
        self.mock_client.keys.assert_called_once_with("test:*")
        self.mock_client.delete.assert_called_once_with("test:1", "test:2", "test:3")
    
    def test_clear_pattern_no_matches(self):
        """Test clearing pattern with no matches."""
        self.mock_client.keys.return_value = []
        
        result = self.cache_manager.clear_pattern("test:*")
        
        assert result == 0
        self.mock_client.delete.assert_not_called()
    
    def test_get_many(self):
        """Test getting multiple values."""
        self.mock_client.mget.return_value = ['{"a": 1}', '{"b": 2}', None]
        
        result = self.cache_manager.get_many(["key1", "key2", "key3"])
        
        assert result == {"key1": {"a": 1}, "key2": {"b": 2}}
        self.mock_client.mget.assert_called_once_with(["key1", "key2", "key3"])
    
    def test_set_many(self):
        """Test setting multiple values."""
        data = {
            "key1": {"a": 1},
            "key2": {"b": 2},
            "key3": "plain"
        }
        
        result = self.cache_manager.set_many(data)
        
        assert result is True
        self.mock_client.mset.assert_called_once()
    
    def test_set_many_with_ttl(self):
        """Test setting multiple values with TTL."""
        data = {"key1": "value1", "key2": "value2"}
        
        result = self.cache_manager.set_many(data, ttl=300)
        
        assert result is True
        self.mock_client.mset.assert_called_once()
        assert self.mock_client.expire.call_count == 2


class TestCacheKeyGeneration:
    """Test cache key generation utility."""
    
    def test_simple_key(self):
        """Test simple key generation."""
        key = get_cache_key("search")
        assert key == "search"
    
    def test_key_with_args(self):
        """Test key with positional arguments."""
        key = get_cache_key("search", "python", "developer")
        assert key == "search:python:developer"
    
    def test_key_with_kwargs(self):
        """Test key with keyword arguments."""
        key = get_cache_key("search", location="remote", salary=100000)
        assert "search" in key
        assert "location=remote" in key
        assert "salary=100000" in key
    
    def test_key_with_mixed_args(self):
        """Test key with both positional and keyword arguments."""
        key = get_cache_key("search", "python", location="remote", level="senior")
        assert key.startswith("search:python:")
        assert "location=remote" in key
        assert "level=senior" in key
    
    def test_key_sorting(self):
        """Test that kwargs are sorted for consistent keys."""
        key1 = get_cache_key("search", z="last", a="first", m="middle")
        key2 = get_cache_key("search", a="first", m="middle", z="last")
        assert key1 == key2


@pytest.mark.integration
class TestRedisIntegration:
    """Integration tests requiring actual Redis connection."""
    
    @pytest.fixture(autouse=True)
    def cleanup(self):
        """Clean up test keys after each test."""
        yield
        try:
            cache.clear_pattern("test:*")
        except:
            pass
    
    def test_real_cache_operations(self):
        """Test cache operations with real Redis."""
        # Set and get
        cache.set("test:integration", {"data": "value"})
        result = cache.get("test:integration")
        assert result == {"data": "value"}
        
        # TTL
        cache.set("test:ttl", "expires", ttl=10)
        ttl = cache.get_ttl("test:ttl")
        assert 0 < ttl <= 10
        
        # Delete
        cache.delete("test:integration")
        assert cache.get("test:integration") is None
    
    def test_real_counter_operations(self):
        """Test counter operations with real Redis."""
        cache.set("test:counter", 0)
        
        # Increment
        val = cache.increment("test:counter", 5)
        assert val == 5
        
        # Decrement
        val = cache.decrement("test:counter", 2)
        assert val == 3
    
    def test_real_batch_operations(self):
        """Test batch operations with real Redis."""
        data = {
            "test:batch1": "value1",
            "test:batch2": {"key": "value2"},
            "test:batch3": [1, 2, 3]
        }
        
        # Set many
        cache.set_many(data)
        
        # Get many
        result = cache.get_many(list(data.keys()))
        assert result == data
        
        # Clear pattern
        deleted = cache.clear_pattern("test:batch*")
        assert deleted == 3
