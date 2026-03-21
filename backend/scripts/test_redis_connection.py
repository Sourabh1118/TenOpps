#!/usr/bin/env python3
"""
Test script for Redis connection and caching functionality.

This script verifies:
1. Redis broker connection (for Celery)
2. Redis cache connection
3. Basic cache operations (get, set, delete)
4. TTL functionality
5. Connection pooling
"""
import sys
import asyncio
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.redis import redis_client, cache, get_cache_key
from app.core.logging import logger
from datetime import timedelta


def test_broker_connection():
    """Test Redis broker connection."""
    print("\n=== Testing Redis Broker Connection ===")
    try:
        broker = redis_client.get_broker_client()
        result = broker.ping()
        print(f"✓ Broker connection successful: {result}")
        
        # Test basic operations
        broker.set("test:broker", "hello")
        value = broker.get("test:broker")
        print(f"✓ Broker set/get test: {value}")
        broker.delete("test:broker")
        
        return True
    except Exception as e:
        print(f"✗ Broker connection failed: {e}")
        return False


def test_cache_connection():
    """Test Redis cache connection."""
    print("\n=== Testing Redis Cache Connection ===")
    try:
        cache_client = redis_client.get_cache_client()
        result = cache_client.ping()
        print(f"✓ Cache connection successful: {result}")
        
        # Test basic operations
        cache_client.set("test:cache", "world")
        value = cache_client.get("test:cache")
        print(f"✓ Cache set/get test: {value}")
        cache_client.delete("test:cache")
        
        return True
    except Exception as e:
        print(f"✗ Cache connection failed: {e}")
        return False


def test_cache_operations():
    """Test cache utility functions."""
    print("\n=== Testing Cache Operations ===")
    
    try:
        # Test simple set/get
        cache.set("test:simple", "value1")
        value = cache.get("test:simple")
        assert value == "value1", f"Expected 'value1', got {value}"
        print("✓ Simple set/get works")
        
        # Test JSON serialization
        data = {"name": "John", "age": 30, "skills": ["Python", "Redis"]}
        cache.set("test:json", data)
        retrieved = cache.get("test:json")
        assert retrieved == data, f"Expected {data}, got {retrieved}"
        print("✓ JSON serialization works")
        
        # Test TTL
        cache.set("test:ttl", "expires", ttl=2)
        exists = cache.exists("test:ttl")
        assert exists, "Key should exist"
        ttl = cache.get_ttl("test:ttl")
        assert ttl > 0 and ttl <= 2, f"TTL should be 1-2 seconds, got {ttl}"
        print(f"✓ TTL set correctly: {ttl} seconds remaining")
        
        # Test timedelta TTL
        cache.set("test:timedelta", "expires", ttl=timedelta(minutes=5))
        ttl = cache.get_ttl("test:timedelta")
        assert ttl > 290 and ttl <= 300, f"TTL should be ~300 seconds, got {ttl}"
        print(f"✓ Timedelta TTL works: {ttl} seconds")
        
        # Test delete
        cache.delete("test:simple")
        value = cache.get("test:simple")
        assert value is None, "Key should be deleted"
        print("✓ Delete works")
        
        # Test increment/decrement
        cache.set("test:counter", 10)
        new_val = cache.increment("test:counter", 5)
        assert new_val == 15, f"Expected 15, got {new_val}"
        print("✓ Increment works")
        
        new_val = cache.decrement("test:counter", 3)
        assert new_val == 12, f"Expected 12, got {new_val}"
        print("✓ Decrement works")
        
        # Test get_many/set_many
        data_map = {
            "test:multi1": "value1",
            "test:multi2": {"key": "value2"},
            "test:multi3": [1, 2, 3]
        }
        cache.set_many(data_map)
        retrieved = cache.get_many(list(data_map.keys()))
        assert retrieved == data_map, f"Expected {data_map}, got {retrieved}"
        print("✓ get_many/set_many works")
        
        # Test pattern deletion
        cache.set("test:pattern:1", "a")
        cache.set("test:pattern:2", "b")
        cache.set("test:pattern:3", "c")
        deleted = cache.clear_pattern("test:pattern:*")
        assert deleted == 3, f"Expected 3 deletions, got {deleted}"
        print("✓ Pattern deletion works")
        
        # Test cache key generation
        key = get_cache_key("search", "python", location="remote", salary=100000)
        assert "search" in key and "python" in key and "location=remote" in key
        print(f"✓ Cache key generation works: {key}")
        
        # Cleanup
        cache.clear_pattern("test:*")
        
        return True
    except Exception as e:
        print(f"✗ Cache operations failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_health_check():
    """Test Redis health check."""
    print("\n=== Testing Health Check ===")
    try:
        health = await redis_client.health_check()
        print(f"Broker status: {health['broker']['status']}")
        print(f"Cache status: {health['cache']['status']}")
        
        assert health['broker']['status'] == 'healthy', "Broker should be healthy"
        assert health['cache']['status'] == 'healthy', "Cache should be healthy"
        print("✓ Health check passed")
        
        return True
    except Exception as e:
        print(f"✗ Health check failed: {e}")
        return False


def test_connection_pooling():
    """Test connection pooling."""
    print("\n=== Testing Connection Pooling ===")
    try:
        # Get multiple clients - should reuse pools
        client1 = redis_client.get_cache_client()
        client2 = redis_client.get_cache_client()
        
        assert client1 is client2, "Should return same client instance"
        print("✓ Connection pooling works (singleton pattern)")
        
        # Test concurrent operations
        for i in range(10):
            cache.set(f"test:pool:{i}", f"value{i}")
        
        for i in range(10):
            value = cache.get(f"test:pool:{i}")
            assert value == f"value{i}", f"Expected value{i}, got {value}"
        
        print("✓ Concurrent operations work")
        
        # Cleanup
        cache.clear_pattern("test:pool:*")
        
        return True
    except Exception as e:
        print(f"✗ Connection pooling test failed: {e}")
        return False


async def main():
    """Run all tests."""
    print("=" * 60)
    print("Redis Connection and Caching Test Suite")
    print("=" * 60)
    
    results = []
    
    # Run tests
    results.append(("Broker Connection", test_broker_connection()))
    results.append(("Cache Connection", test_cache_connection()))
    results.append(("Cache Operations", test_cache_operations()))
    results.append(("Health Check", await test_health_check()))
    results.append(("Connection Pooling", test_connection_pooling()))
    
    # Print summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    # Cleanup
    redis_client.close()
    
    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
