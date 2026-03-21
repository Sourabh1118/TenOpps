# Redis Setup and Configuration Guide

## Overview

This document describes the Redis setup for the Job Aggregation Platform. Redis is used for two primary purposes:

1. **Task Queue (Database 0)**: Message broker for Celery background tasks
2. **Caching Layer (Database 1)**: High-performance caching for search results, popular queries, and rate limiting

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Redis Server                          │
│                                                          │
│  ┌──────────────────┐      ┌──────────────────┐        │
│  │   Database 0     │      │   Database 1     │        │
│  │  (Task Queue)    │      │    (Cache)       │        │
│  │                  │      │                  │        │
│  │  - Celery tasks  │      │  - Search cache  │        │
│  │  - Task results  │      │  - Rate limits   │        │
│  │  - Task routing  │      │  - Counters      │        │
│  └──────────────────┘      └──────────────────┘        │
│                                                          │
└─────────────────────────────────────────────────────────┘
         ▲                              ▲
         │                              │
    ┌────┴────┐                    ┌────┴────┐
    │ Celery  │                    │  Cache  │
    │ Workers │                    │ Manager │
    └─────────┘                    └─────────┘
```

## Installation

### Local Development

#### macOS
```bash
brew install redis
brew services start redis
```

#### Ubuntu/Debian
```bash
sudo apt-get update
sudo apt-get install redis-server
sudo systemctl start redis-server
sudo systemctl enable redis-server
```

#### Docker
```bash
docker run -d -p 6379:6379 --name redis redis:7-alpine
```

### Verify Installation
```bash
redis-cli ping
# Should return: PONG
```

## Configuration

### Environment Variables

Add to your `.env` file:

```env
# Redis Configuration
REDIS_URL=redis://localhost:6379/0
REDIS_CACHE_DB=1

# Celery Configuration (uses Redis)
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

### Connection Pooling

The Redis client uses connection pooling for efficient resource management:

- **Max Connections**: 20 per pool
- **Socket Timeout**: 5 seconds
- **Connect Timeout**: 5 seconds
- **Retry on Timeout**: Enabled
- **Decode Responses**: Enabled (automatic UTF-8 decoding)

## Usage

### Basic Cache Operations

```python
from app.core.redis import cache

# Set a value
cache.set("user:123", {"name": "John", "email": "john@example.com"})

# Get a value
user = cache.get("user:123")

# Set with TTL (5 minutes)
cache.set("session:abc", {"user_id": 123}, ttl=300)

# Set with timedelta
from datetime import timedelta
cache.set("temp:data", "value", ttl=timedelta(hours=1))

# Delete a value
cache.delete("user:123")

# Check if key exists
if cache.exists("user:123"):
    print("User exists in cache")
```

### Counter Operations

```python
# Increment a counter
views = cache.increment("job:456:views", amount=1)

# Decrement a counter
cache.decrement("quota:employer:789", amount=1)

# Set initial counter value
cache.set("counter:new", 0)
```

### Batch Operations

```python
# Set multiple values at once
data = {
    "key1": "value1",
    "key2": {"nested": "data"},
    "key3": [1, 2, 3]
}
cache.set_many(data, ttl=300)

# Get multiple values at once
results = cache.get_many(["key1", "key2", "key3"])
```

### Pattern-Based Operations

```python
# Delete all keys matching a pattern
cache.clear_pattern("search:*")
cache.clear_pattern("user:session:*")
```

### Cache Key Generation

```python
from app.core.redis import get_cache_key

# Generate consistent cache keys
key = get_cache_key("search", "python", location="remote", salary=100000)
# Result: "search:python:location=remote:salary=100000"

# Use in caching
cache.set(key, search_results, ttl=300)
```

### Direct Redis Client Access

```python
from app.core.redis import redis_client

# Get broker client (database 0)
broker = redis_client.get_broker_client()
broker.lpush("queue:tasks", "task_data")

# Get cache client (database 1)
cache_client = redis_client.get_cache_client()
cache_client.set("custom:key", "value")
```

## Common Use Cases

### 1. Search Result Caching

```python
from app.core.redis import cache, get_cache_key

def search_jobs(query: str, filters: dict):
    # Generate cache key from search parameters
    cache_key = get_cache_key("search", query, **filters)
    
    # Try to get from cache
    cached_results = cache.get(cache_key)
    if cached_results:
        return cached_results
    
    # Perform search
    results = perform_database_search(query, filters)
    
    # Cache for 5 minutes
    cache.set(cache_key, results, ttl=300)
    
    return results
```

### 2. Rate Limiting

```python
from app.core.redis import cache
from datetime import timedelta

def check_rate_limit(user_id: str, limit: int = 100) -> bool:
    """Check if user has exceeded rate limit."""
    key = f"rate_limit:{user_id}"
    
    # Get current count
    count = cache.get(key) or 0
    
    if count >= limit:
        return False  # Rate limit exceeded
    
    # Increment counter
    new_count = cache.increment(key)
    
    # Set expiry on first request (1 minute window)
    if new_count == 1:
        cache.client.expire(key, 60)
    
    return True
```

### 3. View Counter

```python
from app.core.redis import cache

def increment_job_views(job_id: str):
    """Increment job view counter."""
    key = f"job:{job_id}:views"
    views = cache.increment(key)
    
    # Batch update database every 10 views
    if views % 10 == 0:
        update_database_view_count(job_id, views)
```

### 4. Popular Searches Tracking

```python
from app.core.redis import cache

def track_search(query: str):
    """Track popular search queries."""
    key = f"popular:search:{query.lower()}"
    cache.increment(key)
    
    # Set 7-day expiry
    cache.client.expire(key, 604800)

def get_popular_searches(limit: int = 10) -> list:
    """Get most popular search queries."""
    pattern = "popular:search:*"
    keys = cache.client.keys(pattern)
    
    # Get counts for all keys
    searches = []
    for key in keys:
        query = key.replace("popular:search:", "")
        count = int(cache.get(key) or 0)
        searches.append((query, count))
    
    # Sort by count and return top N
    searches.sort(key=lambda x: x[1], reverse=True)
    return [query for query, _ in searches[:limit]]
```

### 5. Session Management

```python
from app.core.redis import cache
from datetime import timedelta

def create_session(user_id: str, session_data: dict) -> str:
    """Create a user session."""
    import uuid
    session_id = str(uuid.uuid4())
    
    key = f"session:{session_id}"
    cache.set(key, {
        "user_id": user_id,
        **session_data
    }, ttl=timedelta(hours=24))
    
    return session_id

def get_session(session_id: str) -> dict:
    """Get session data."""
    key = f"session:{session_id}"
    return cache.get(key)

def delete_session(session_id: str):
    """Delete a session."""
    key = f"session:{session_id}"
    cache.delete(key)
```

## Health Checks

### Programmatic Health Check

```python
from app.core.redis import redis_client

async def check_redis_health():
    """Check Redis health status."""
    health = await redis_client.health_check()
    
    if health['broker']['status'] == 'healthy' and \
       health['cache']['status'] == 'healthy':
        return {"status": "healthy", "details": health}
    else:
        return {"status": "unhealthy", "details": health}
```

### CLI Health Check

```bash
# Run the test script
python scripts/test_redis_connection.py

# Or use redis-cli
redis-cli ping
redis-cli info
redis-cli dbsize
```

## Monitoring

### Key Metrics to Monitor

1. **Memory Usage**
   ```bash
   redis-cli info memory
   ```

2. **Connected Clients**
   ```bash
   redis-cli info clients
   ```

3. **Operations Per Second**
   ```bash
   redis-cli info stats
   ```

4. **Keyspace Statistics**
   ```bash
   redis-cli info keyspace
   ```

### Monitoring Commands

```bash
# Monitor all commands in real-time
redis-cli monitor

# Get slow queries
redis-cli slowlog get 10

# Check specific database size
redis-cli -n 0 dbsize  # Task queue
redis-cli -n 1 dbsize  # Cache
```

## Performance Optimization

### Best Practices

1. **Use Appropriate TTLs**
   - Search results: 5 minutes
   - User sessions: 24 hours
   - Rate limits: 1 minute
   - Popular queries: 7 days

2. **Batch Operations**
   - Use `set_many` and `get_many` for multiple keys
   - Reduces network round trips

3. **Key Naming Conventions**
   - Use colons for hierarchy: `entity:id:attribute`
   - Examples: `user:123:profile`, `job:456:views`

4. **Avoid Large Values**
   - Keep cached values under 1MB
   - Use compression for large data

5. **Pattern Matching**
   - Use specific patterns to avoid scanning all keys
   - `cache.clear_pattern("search:python:*")` is better than `cache.clear_pattern("*")`

### Memory Management

```python
# Set max memory policy in redis.conf
maxmemory 256mb
maxmemory-policy allkeys-lru

# Or via redis-cli
redis-cli config set maxmemory 256mb
redis-cli config set maxmemory-policy allkeys-lru
```

## Troubleshooting

### Connection Issues

**Problem**: Cannot connect to Redis

**Solutions**:
```bash
# Check if Redis is running
redis-cli ping

# Check Redis logs
tail -f /var/log/redis/redis-server.log

# Restart Redis
sudo systemctl restart redis-server

# Check firewall
sudo ufw allow 6379
```

### Memory Issues

**Problem**: Redis running out of memory

**Solutions**:
```bash
# Check memory usage
redis-cli info memory

# Clear specific patterns
redis-cli --scan --pattern "temp:*" | xargs redis-cli del

# Flush specific database
redis-cli -n 1 flushdb

# Increase max memory
redis-cli config set maxmemory 512mb
```

### Performance Issues

**Problem**: Slow cache operations

**Solutions**:
1. Check for slow queries: `redis-cli slowlog get 10`
2. Avoid using `keys` command in production
3. Use pipelining for multiple operations
4. Monitor connection pool exhaustion

## Testing

### Run Unit Tests

```bash
# Run all Redis tests
pytest tests/test_redis.py -v

# Run only unit tests (no Redis required)
pytest tests/test_redis.py -v -m "not integration"

# Run integration tests (requires Redis)
pytest tests/test_redis.py -v -m integration
```

### Run Connection Test Script

```bash
# Make script executable
chmod +x scripts/test_redis_connection.py

# Run test
python scripts/test_redis_connection.py
```

## Production Deployment

### Redis Configuration for Production

```conf
# /etc/redis/redis.conf

# Bind to specific interface
bind 127.0.0.1

# Require password
requirepass your-strong-password-here

# Enable persistence
save 900 1
save 300 10
save 60 10000

# AOF persistence
appendonly yes
appendfsync everysec

# Max memory
maxmemory 1gb
maxmemory-policy allkeys-lru

# Logging
loglevel notice
logfile /var/log/redis/redis-server.log
```

### Environment Variables for Production

```env
REDIS_URL=redis://:password@redis-host:6379/0
REDIS_CACHE_DB=1
```

### Security Considerations

1. **Use Password Authentication**
   ```env
   REDIS_URL=redis://:strong-password@localhost:6379/0
   ```

2. **Bind to Localhost** (if on same server)
   ```conf
   bind 127.0.0.1
   ```

3. **Use TLS** (for remote connections)
   ```env
   REDIS_URL=rediss://:password@host:6380/0
   ```

4. **Disable Dangerous Commands**
   ```conf
   rename-command FLUSHDB ""
   rename-command FLUSHALL ""
   rename-command CONFIG ""
   ```

## References

- [Redis Documentation](https://redis.io/documentation)
- [redis-py Documentation](https://redis-py.readthedocs.io/)
- [Celery with Redis](https://docs.celeryproject.org/en/stable/getting-started/backends-and-brokers/redis.html)

## Requirements Satisfied

✅ **Requirement 6.14**: Popular searches cached for 5 minutes  
✅ **Requirement 16.8**: Redis connection pooling configured with max 20 connections per pool
