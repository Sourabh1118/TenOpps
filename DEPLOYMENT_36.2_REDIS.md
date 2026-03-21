# Task 36.2: Deploy Redis Instance

**Requirement**: 16.8 - Redis deployment with persistence and connection testing

## Overview

This guide covers deploying Redis on Railway or Render's free tier for:
- Caching (search results, session data)
- Celery message broker
- Celery result backend
- Rate limiting

**Comparison**:
- **Railway**: 512MB RAM, persistence supported, better for production
- **Render**: 25MB RAM, NO persistence, good for testing only

**Recommendation**: Use Railway for production deployment.

## Prerequisites

- [ ] Railway account (https://railway.app) OR Render account (https://render.com)
- [ ] GitHub repository with your code
- [ ] Database already deployed (Task 36.1)

---

## Option A: Railway (Recommended)

### Step 1: Create Railway Project

1. **Sign in to Railway**:
   - Go to https://railway.app
   - Click "Login" → "Login with GitHub"
   - Authorize Railway to access your GitHub account

2. **Create New Project**:
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose your `job-aggregation-platform` repository
   - Click "Deploy Now"

3. **Initial Setup**:
   - Railway will create a project
   - Don't worry about the initial deployment - we'll configure services separately

### Step 2: Add Redis Service

1. **Add Database**:
   - In your Railway project dashboard, click "New"
   - Select "Database"
   - Click "Add Redis"

2. **Redis Provisioning**:
   - Railway automatically provisions a Redis instance
   - Takes about 30 seconds
   - You'll see a new "Redis" service in your project

3. **View Redis Details**:
   - Click on the Redis service card
   - You'll see the service dashboard with metrics

### Step 3: Get Redis Connection Details

1. **Navigate to Variables**:
   - Click on Redis service
   - Go to **Variables** tab

2. **Copy Connection Information**:
   
   Railway automatically creates these variables:
   ```bash
   REDIS_URL=redis://default:[PASSWORD]@[HOST]:[PORT]
   REDIS_PRIVATE_URL=redis://default:[PASSWORD]@redis.railway.internal:[PORT]
   ```

3. **Understanding the URLs**:
   - **REDIS_URL**: Public URL (use for external connections)
   - **REDIS_PRIVATE_URL**: Internal URL (use for services within Railway)
   - **Recommendation**: Use `REDIS_PRIVATE_URL` for better performance and security

4. **Save Connection Details**:
   ```bash
   # Railway Redis Connection Details
   
   # Internal URL (use this for Railway services)
   REDIS_URL=redis://default:[PASSWORD]@redis.railway.internal:6379
   
   # Public URL (use for external connections)
   REDIS_PUBLIC_URL=redis://default:[PASSWORD]@[HOST]:[PORT]
   
   # Celery Configuration
   CELERY_BROKER_URL=redis://default:[PASSWORD]@redis.railway.internal:6379/0
   CELERY_RESULT_BACKEND=redis://default:[PASSWORD]@redis.railway.internal:6379/0
   
   # Cache Configuration
   REDIS_CACHE_DB=1
   ```

### Step 4: Configure Redis Persistence

1. **Enable AOF Persistence**:
   - Click on Redis service
   - Go to **Settings** tab
   - Scroll to **Deploy** section
   - Find **Custom Start Command**

2. **Set Start Command**:
   ```bash
   redis-server --appendonly yes --appendfsync everysec --maxmemory 450mb --maxmemory-policy allkeys-lru
   ```
   
   **Explanation**:
   - `--appendonly yes`: Enable AOF (Append-Only File) persistence
   - `--appendfsync everysec`: Sync to disk every second (good balance)
   - `--maxmemory 450mb`: Limit memory to 450MB (leave 62MB for overhead)
   - `--maxmemory-policy allkeys-lru`: Evict least recently used keys when full

3. **Save and Redeploy**:
   - Click "Save"
   - Railway will redeploy Redis with new configuration

### Step 5: Test Redis Connection

1. **Using Railway CLI** (Recommended):
   
   Install Railway CLI:
   ```bash
   # macOS/Linux
   curl -fsSL https://railway.app/install.sh | sh
   
   # Windows (PowerShell)
   iwr https://railway.app/install.ps1 | iex
   ```
   
   Connect to Redis:
   ```bash
   railway link  # Link to your project
   railway run redis-cli -u $REDIS_URL
   ```
   
   Test commands:
   ```redis
   PING
   # Should return: PONG
   
   SET test "Hello Railway"
   GET test
   # Should return: "Hello Railway"
   
   DEL test
   ```

2. **Using Railway Console**:
   - Click on Redis service
   - Click "Connect" → "Redis CLI"
   - Run test commands above

3. **From Application Code**:
   ```python
   # Test script: test_redis.py
   import redis
   import os
   
   redis_url = os.getenv('REDIS_URL')
   client = redis.from_url(redis_url)
   
   # Test connection
   print(f"Ping: {client.ping()}")
   
   # Test set/get
   client.set('test_key', 'test_value')
   print(f"Get: {client.get('test_key')}")
   
   # Test expiry
   client.setex('temp_key', 10, 'expires_in_10s')
   print(f"TTL: {client.ttl('temp_key')}")
   
   # Clean up
   client.delete('test_key', 'temp_key')
   print("Redis connection successful!")
   ```

### Step 6: Configure Redis for Different Use Cases

Railway Redis will be used for multiple purposes. Here's how to configure each:

1. **Cache Configuration** (DB 1):
   ```bash
   REDIS_CACHE_DB=1
   REDIS_CACHE_TTL=300  # 5 minutes default
   ```

2. **Celery Broker** (DB 0):
   ```bash
   CELERY_BROKER_URL=redis://default:[PASSWORD]@redis.railway.internal:6379/0
   CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP=True
   ```

3. **Celery Result Backend** (DB 0):
   ```bash
   CELERY_RESULT_BACKEND=redis://default:[PASSWORD]@redis.railway.internal:6379/0
   CELERY_RESULT_EXPIRES=3600  # 1 hour
   ```

4. **Rate Limiting** (DB 2):
   ```bash
   REDIS_RATE_LIMIT_DB=2
   ```

### Step 7: Monitor Redis Performance

1. **Railway Dashboard**:
   - Click on Redis service
   - View metrics:
     - Memory usage
     - CPU usage
     - Network I/O
     - Request rate

2. **Redis INFO Command**:
   ```bash
   railway run redis-cli -u $REDIS_URL INFO
   ```
   
   Key metrics to watch:
   ```
   used_memory_human: 45.2M
   connected_clients: 5
   total_commands_processed: 12345
   keyspace_hits: 8900
   keyspace_misses: 1200
   ```

3. **Monitor Cache Hit Rate**:
   ```bash
   railway run redis-cli -u $REDIS_URL INFO stats | grep keyspace
   ```
   
   Calculate hit rate:
   ```
   Hit Rate = keyspace_hits / (keyspace_hits + keyspace_misses)
   ```
   
   Good hit rate: > 80%

---

## Option B: Render (Testing Only)

**⚠️ Warning**: Render's free Redis tier has NO persistence and only 25MB RAM. Use only for testing, not production.

### Step 1: Create Redis Instance

1. **Sign in to Render**:
   - Go to https://render.com
   - Sign in with GitHub

2. **Create Redis**:
   - Click "New" → "Redis"
   - Fill in details:
     - **Name**: `job-platform-redis`
     - **Region**: Oregon (US West) or Frankfurt (Europe)
     - **Plan**: Free (25MB, no persistence)
   - Click "Create Redis"

### Step 2: Get Connection Details

1. **View Redis Dashboard**:
   - Click on your Redis instance
   - Copy connection details:
     - **Internal Redis URL**: `redis://red-xxxxxxxxxxxxx:6379`
     - **External Redis URL**: `redis://red-xxxxxxxxxxxxx-external:6379`

2. **Save Connection Details**:
   ```bash
   # Render Redis Connection Details
   
   # Internal URL (use for Render services)
   REDIS_URL=redis://red-xxxxxxxxxxxxx:6379
   
   # External URL (use for external connections)
   REDIS_EXTERNAL_URL=redis://red-xxxxxxxxxxxxx-external:6379
   
   # Celery Configuration
   CELERY_BROKER_URL=redis://red-xxxxxxxxxxxxx:6379/0
   CELERY_RESULT_BACKEND=redis://red-xxxxxxxxxxxxx:6379/0
   
   # Cache Configuration
   REDIS_CACHE_DB=1
   ```

### Step 3: Test Connection

1. **Using Redis CLI**:
   ```bash
   redis-cli -u redis://red-xxxxxxxxxxxxx-external:6379
   ```

2. **Test Commands**:
   ```redis
   PING
   SET test "Hello Render"
   GET test
   ```

### Step 4: Limitations

Render free Redis has significant limitations:

- ❌ **No Persistence**: Data lost on restart
- ❌ **25MB RAM**: Very limited storage
- ❌ **No Backups**: Cannot restore data
- ✅ **Good for**: Development, testing, demos
- ❌ **Not for**: Production, important data

**Recommendation**: Upgrade to paid plan ($7/month) for:
- 256MB RAM
- Persistence enabled
- Automatic backups

---

## Configuration Summary

Add these environment variables to your backend and Celery services:

### Railway Configuration

```bash
# Redis Connection (internal URL for Railway services)
REDIS_URL=redis://default:[PASSWORD]@redis.railway.internal:6379

# Celery Broker and Backend
CELERY_BROKER_URL=redis://default:[PASSWORD]@redis.railway.internal:6379/0
CELERY_RESULT_BACKEND=redis://default:[PASSWORD]@redis.railway.internal:6379/0
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP=True
CELERY_RESULT_EXPIRES=3600

# Cache Configuration
REDIS_CACHE_DB=1
REDIS_CACHE_TTL=300

# Rate Limiting
REDIS_RATE_LIMIT_DB=2
```

### Render Configuration

```bash
# Redis Connection (internal URL for Render services)
REDIS_URL=redis://red-xxxxxxxxxxxxx:6379

# Celery Broker and Backend
CELERY_BROKER_URL=redis://red-xxxxxxxxxxxxx:6379/0
CELERY_RESULT_BACKEND=redis://red-xxxxxxxxxxxxx:6379/0
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP=True
CELERY_RESULT_EXPIRES=3600

# Cache Configuration
REDIS_CACHE_DB=1
REDIS_CACHE_TTL=300

# Rate Limiting
REDIS_RATE_LIMIT_DB=2
```

## Testing Checklist

- [ ] Redis instance created and running
- [ ] Can connect from local machine (if using external URL)
- [ ] Can connect from backend service
- [ ] PING command returns PONG
- [ ] Can SET and GET keys
- [ ] Persistence enabled (Railway only)
- [ ] Memory limits configured
- [ ] Multiple databases accessible (0, 1, 2)
- [ ] Celery can connect to broker
- [ ] Cache operations work

## Troubleshooting

### Connection Refused

**Problem**: Cannot connect to Redis

**Solutions**:
1. Verify Redis service is running
2. Check connection URL is correct
3. Use internal URL for services within Railway/Render
4. Check firewall/network settings

### Out of Memory

**Problem**: Redis runs out of memory

**Solutions**:
1. Check memory usage in dashboard
2. Implement cache eviction policy (already configured)
3. Reduce cache TTL
4. Clear old keys:
   ```bash
   redis-cli -u $REDIS_URL FLUSHDB
   ```
5. Upgrade to larger plan

### Celery Can't Connect

**Problem**: Celery workers can't connect to Redis

**Solutions**:
1. Verify `CELERY_BROKER_URL` is correct
2. Check Redis is running
3. Test connection manually:
   ```python
   from celery import Celery
   app = Celery(broker='redis://...')
   print(app.connection().connect())
   ```
4. Enable connection retry:
   ```bash
   CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP=True
   ```

### Data Loss (Render)

**Problem**: Data disappears after restart

**Solution**: This is expected on Render free tier (no persistence). Either:
1. Upgrade to paid plan ($7/month)
2. Switch to Railway (free tier has persistence)
3. Accept data loss for non-critical data

## Performance Optimization

### 1. Connection Pooling

Configure connection pooling in your application:

```python
# app/core/redis.py
import redis
from redis.connection import ConnectionPool

pool = ConnectionPool.from_url(
    settings.REDIS_URL,
    max_connections=10,
    decode_responses=True
)

def get_redis_client():
    return redis.Redis(connection_pool=pool)
```

### 2. Cache Strategy

Implement smart caching:

```python
# Cache popular searches for 5 minutes
CACHE_TTL_SEARCH = 300

# Cache job details for 1 hour
CACHE_TTL_JOB = 3600

# Cache user sessions for 1 day
CACHE_TTL_SESSION = 86400
```

### 3. Key Naming Convention

Use consistent key naming:

```python
# Format: {namespace}:{entity}:{id}
cache_key = f"search:{query_hash}:{page}"
session_key = f"session:{user_id}"
rate_limit_key = f"ratelimit:{user_id}:{endpoint}"
```

### 4. Monitor Key Expiration

Set expiration on all keys:

```python
# Always set TTL
redis_client.setex(key, ttl, value)

# Or set after creation
redis_client.set(key, value)
redis_client.expire(key, ttl)
```

## Free Tier Limits

### Railway Redis Free Tier

- **Memory**: 512MB RAM
- **Persistence**: Supported (AOF)
- **Bandwidth**: Unlimited
- **Connections**: Unlimited
- **Uptime**: 99.9% SLA
- **Cost**: $0/month

### Render Redis Free Tier

- **Memory**: 25MB RAM
- **Persistence**: NOT supported
- **Bandwidth**: Limited
- **Connections**: Limited
- **Uptime**: Best effort
- **Cost**: $0/month

**Recommendation**: Use Railway for production.

## Next Steps

After completing Redis deployment:

1. ✅ Redis deployed and configured
2. ✅ Persistence enabled (Railway)
3. ✅ Connection tested
4. ➡️ **Next**: Deploy Backend (Task 36.3) - will use this Redis
5. ➡️ Deploy Celery Workers (Task 36.4) - will use this Redis

## Support Resources

- **Railway Documentation**: https://docs.railway.app/databases/redis
- **Render Documentation**: https://render.com/docs/redis
- **Redis Documentation**: https://redis.io/documentation
- **Railway Discord**: https://discord.gg/railway
- **Render Community**: https://community.render.com

---

**Task 36.2 Complete!** ✅

Your Redis instance is now deployed and ready for caching, Celery, and rate limiting.
