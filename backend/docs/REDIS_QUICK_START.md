# Redis Quick Start Guide

## 1. Install Redis

### macOS
```bash
brew install redis
brew services start redis
```

### Ubuntu/Debian
```bash
sudo apt-get install redis-server
sudo systemctl start redis-server
```

### Docker
```bash
docker run -d -p 6379:6379 --name redis redis:7-alpine
```

## 2. Verify Installation

```bash
redis-cli ping
# Expected output: PONG
```

## 3. Configure Environment

Ensure your `.env` file has:

```env
REDIS_URL=redis://localhost:6379/0
REDIS_CACHE_DB=1
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

## 4. Test Connection

```bash
python scripts/test_redis_connection.py
```

Expected output:
```
=== Testing Redis Broker Connection ===
✓ Broker connection successful: True
✓ Broker set/get test: hello

=== Testing Redis Cache Connection ===
✓ Cache connection successful: True
✓ Cache set/get test: world

=== Testing Cache Operations ===
✓ Simple set/get works
✓ JSON serialization works
✓ TTL set correctly: 2 seconds remaining
✓ Timedelta TTL works: 300 seconds
✓ Delete works
✓ Increment works
✓ Decrement works
✓ get_many/set_many works
✓ Pattern deletion works
✓ Cache key generation works

=== Testing Health Check ===
Broker status: healthy
Cache status: healthy
✓ Health check passed

=== Testing Connection Pooling ===
✓ Connection pooling works (singleton pattern)
✓ Concurrent operations work

Total: 5/5 tests passed
```

## 5. Basic Usage Examples

### Cache a Value

```python
from app.core.redis import cache

# Simple value
cache.set("key", "value", ttl=300)  # 5 minutes

# JSON data
cache.set("user:123", {"name": "John", "email": "john@example.com"})

# Get value
user = cache.get("user:123")
```

### Search Result Caching

```python
from app.core.redis import cache, get_cache_key

# Generate cache key
key = get_cache_key("search", "python", location="remote")

# Check cache first
results = cache.get(key)
if not results:
    results = search_database()
    cache.set(key, results, ttl=300)
```

### Counter Operations

```python
from app.core.redis import cache

# Increment view count
views = cache.increment("job:456:views")

# Decrement quota
remaining = cache.decrement("quota:employer:789")
```

## 6. Run Tests

```bash
# All tests
pytest tests/test_redis.py -v

# Unit tests only (no Redis needed)
pytest tests/test_redis.py -v -m "not integration"

# Integration tests (requires Redis)
pytest tests/test_redis.py -v -m integration
```

## 7. Monitor Redis

```bash
# Check status
redis-cli ping

# View info
redis-cli info

# Monitor commands
redis-cli monitor

# Check database size
redis-cli dbsize
```

## Common Issues

### Redis Not Running
```bash
# macOS
brew services start redis

# Linux
sudo systemctl start redis-server

# Docker
docker start redis
```

### Connection Refused
Check if Redis is listening on the correct port:
```bash
redis-cli -h localhost -p 6379 ping
```

### Memory Issues
Clear cache if needed:
```bash
redis-cli -n 1 flushdb  # Clear cache database only
```

## Next Steps

- Read [REDIS_SETUP.md](./REDIS_SETUP.md) for detailed configuration
- Implement caching in your API endpoints
- Set up Celery workers (Task 1.5)
- Configure rate limiting using Redis

## Key Features

✅ Separate databases for task queue (0) and cache (1)  
✅ Connection pooling (max 20 connections)  
✅ Automatic JSON serialization  
✅ TTL support with seconds or timedelta  
✅ Batch operations (get_many, set_many)  
✅ Pattern-based deletion  
✅ Counter operations  
✅ Health check functionality
