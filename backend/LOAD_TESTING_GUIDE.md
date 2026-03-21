# Load Testing Guide - Job Aggregation Platform

## Overview

This guide provides comprehensive instructions for performing load testing on the Job Aggregation Platform. Load testing validates that the system meets performance requirements under various load conditions and helps identify bottlenecks before they impact production users.

**Validates: Requirements 16.1, 16.2, 16.3**

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Load Testing Tools](#load-testing-tools)
3. [Test Scenarios](#test-scenarios)
4. [Performance Targets](#performance-targets)
5. [Running Load Tests](#running-load-tests)
6. [Analyzing Results](#analyzing-results)
7. [Bottleneck Identification](#bottleneck-identification)
8. [Optimization Strategies](#optimization-strategies)

## Prerequisites

### System Requirements

- Python 3.11+
- Docker and Docker Compose (for isolated test environment)
- At least 4GB RAM available for testing
- Network bandwidth: 10 Mbps minimum

### Software Installation

```bash
# Install Locust for load testing
pip install locust==2.20.0

# Install additional monitoring tools
pip install psutil==5.9.6
pip install matplotlib==3.8.2  # For generating graphs
```

### Test Environment Setup

**Option 1: Local Testing**
```bash
# Start all services
cd backend
docker-compose up -d

# Verify services are running
docker-compose ps
```

**Option 2: Staging Environment**
- Use dedicated staging environment
- Ensure it mirrors production configuration
- Isolate from production database

### Test Data Preparation

```bash
# Seed database with test data
python scripts/seed_database.py --jobs 10000 --employers 500 --applications 5000

# Verify data seeding
python scripts/verify_test_data.py
```

## Load Testing Tools

### Primary Tool: Locust

**Why Locust?**
- Python-based (matches our backend stack)
- Distributed load generation
- Real-time web UI for monitoring
- Easy to write test scenarios
- Excellent reporting capabilities

**Alternative Tools:**
- **k6**: JavaScript-based, excellent for CI/CD integration
- **Apache JMeter**: Java-based, comprehensive but heavier
- **Artillery**: Node.js-based, good for API testing
- **Gatling**: Scala-based, excellent reporting

### Monitoring Tools

1. **System Metrics**: `htop`, `vmstat`, `iostat`
2. **Database Monitoring**: PostgreSQL `pg_stat_statements`
3. **Redis Monitoring**: `redis-cli --stat`
4. **Application Metrics**: Sentry, custom logging

## Test Scenarios

### Scenario 1: API Performance Under Load (100 Concurrent Users)

**Objective**: Validate API can handle 100 concurrent users making various requests

**Test Profile**:
- **Users**: 100 concurrent
- **Duration**: 10 minutes
- **Ramp-up**: 30 seconds
- **Request Mix**:
  - 40% Job Search (GET /api/jobs/search)
  - 30% Job Details (GET /api/jobs/{id})
  - 15% Job Posting (POST /api/jobs/direct)
  - 10% Application Submission (POST /api/applications)
  - 5% Dashboard Access (GET /api/employer/dashboard)

**Success Criteria**:
- 95th percentile response time < 500ms for reads
- 95th percentile response time < 1000ms for writes
- Error rate < 1%
- No database connection pool exhaustion
- No memory leaks

### Scenario 2: Search Performance with Large Dataset

**Objective**: Test search functionality with 100,000+ jobs in database

**Test Profile**:
- **Users**: 50 concurrent
- **Duration**: 5 minutes
- **Dataset**: 100,000 jobs
- **Query Types**:
  - Simple keyword search (50%)
  - Multi-filter search (30%)
  - Location-based search (20%)

**Success Criteria**:
- Average response time < 200ms
- 95th percentile < 500ms
- 99th percentile < 1000ms
- Cache hit rate > 60%
- Database CPU < 70%

### Scenario 3: Scraping Performance with Multiple Sources

**Objective**: Validate scraping system can handle multiple concurrent scraping tasks

**Test Profile**:
- **Concurrent Scrapers**: 4 workers
- **Sources**: LinkedIn, Indeed, Naukri, Monster
- **Duration**: 15 minutes
- **Rate Limits**: Respect per-source limits

**Success Criteria**:
- All sources scraped successfully
- Rate limits respected (no 429 errors)
- Deduplication completes within 5 seconds per job
- Quality scoring completes within 1 second per job
- No worker crashes or memory leaks

### Scenario 4: Mixed Workload (Realistic Traffic)

**Objective**: Simulate realistic production traffic patterns

**Test Profile**:
- **Total Users**: 200 concurrent
- **Duration**: 20 minutes
- **User Types**:
  - 70% Job Seekers (searching, viewing)
  - 20% Employers (posting, managing)
  - 10% Anonymous (browsing)

**Success Criteria**:
- System remains stable throughout test
- No service degradation
- Database connections < 80% of pool
- Redis memory < 80% of limit
- CPU usage < 80% average

### Scenario 5: Spike Testing

**Objective**: Test system behavior under sudden traffic spikes

**Test Profile**:
- **Baseline**: 20 users
- **Spike**: 200 users (10x increase)
- **Spike Duration**: 2 minutes
- **Recovery**: Return to baseline

**Success Criteria**:
- System handles spike without crashes
- Response times degrade gracefully
- System recovers within 30 seconds after spike
- No data loss or corruption

### Scenario 6: Stress Testing (Find Breaking Point)

**Objective**: Identify system capacity limits

**Test Profile**:
- **Starting Users**: 50
- **Increment**: +50 users every 2 minutes
- **Duration**: Until failure or 500 users
- **Stop Condition**: Error rate > 10% or response time > 5s

**Success Criteria**:
- Document maximum sustainable load
- Identify first component to fail
- System degrades gracefully (no crashes)
- System recovers after load reduction

## Performance Targets

### API Response Times

| Endpoint Type | Average | 95th Percentile | 99th Percentile |
|---------------|---------|-----------------|-----------------|
| GET (simple) | < 100ms | < 200ms | < 500ms |
| GET (complex) | < 200ms | < 500ms | < 1000ms |
| POST (create) | < 300ms | < 800ms | < 1500ms |
| PUT (update) | < 250ms | < 700ms | < 1200ms |
| DELETE | < 150ms | < 400ms | < 800ms |

### Search Performance

| Dataset Size | Average | 95th Percentile | Cache Hit Rate |
|--------------|---------|-----------------|----------------|
| < 10K jobs | < 50ms | < 100ms | > 70% |
| 10K-50K jobs | < 100ms | < 250ms | > 60% |
| 50K-100K jobs | < 200ms | < 500ms | > 50% |
| > 100K jobs | < 300ms | < 800ms | > 40% |

### Scraping Performance

| Metric | Target | Maximum |
|--------|--------|---------|
| Jobs per minute | 100 | 200 |
| Deduplication time | < 5s per job | < 10s |
| Quality scoring | < 1s per job | < 3s |
| Memory per worker | < 500MB | < 1GB |
| Error rate | < 2% | < 5% |

### System Resources

| Resource | Normal Load | High Load | Critical |
|----------|-------------|-----------|----------|
| CPU Usage | < 50% | < 70% | > 80% |
| Memory Usage | < 60% | < 75% | > 85% |
| DB Connections | < 50% pool | < 70% pool | > 80% pool |
| Redis Memory | < 50% | < 70% | > 80% |
| Disk I/O | < 60% | < 80% | > 90% |

## Running Load Tests

### Step 1: Prepare Environment

```bash
# Navigate to backend directory
cd backend

# Activate virtual environment
source venv/bin/activate

# Verify services are running
docker-compose ps

# Check service health
curl http://localhost:8000/health
```

### Step 2: Run Basic Load Test

```bash
# Run Locust with web UI
locust -f tests/load/locustfile.py --host=http://localhost:8000

# Open browser to http://localhost:8089
# Configure:
# - Number of users: 100
# - Spawn rate: 10 users/second
# - Host: http://localhost:8000

# Click "Start Swarming"
```

### Step 3: Run Headless Load Test

```bash
# Run without web UI (for CI/CD)
locust -f tests/load/locustfile.py \
  --host=http://localhost:8000 \
  --users 100 \
  --spawn-rate 10 \
  --run-time 10m \
  --headless \
  --html reports/load_test_report.html \
  --csv reports/load_test_results
```

### Step 4: Run Distributed Load Test

```bash
# Terminal 1: Start master
locust -f tests/load/locustfile.py --master --host=http://localhost:8000

# Terminal 2-4: Start workers
locust -f tests/load/locustfile.py --worker --master-host=localhost
locust -f tests/load/locustfile.py --worker --master-host=localhost
locust -f tests/load/locustfile.py --worker --master-host=localhost
```

### Step 5: Run Specific Scenarios

```bash
# API load test
locust -f tests/load/test_api_load.py --host=http://localhost:8000 --users 100 --run-time 10m --headless

# Search performance test
locust -f tests/load/test_search_performance.py --host=http://localhost:8000 --users 50 --run-time 5m --headless

# Scraping performance test
python tests/load/test_scraping_performance.py

# Mixed workload test
locust -f tests/load/test_mixed_workload.py --host=http://localhost:8000 --users 200 --run-time 20m --headless
```

## Analyzing Results

### Locust Web UI Metrics

**Key Metrics to Monitor**:
1. **Requests per Second (RPS)**: Throughput indicator
2. **Response Times**: 50th, 95th, 99th percentiles
3. **Failure Rate**: Percentage of failed requests
4. **User Count**: Current number of simulated users

**Interpreting Charts**:
- **Total Requests per Second**: Should be stable, not declining
- **Response Times**: Should remain within targets
- **Number of Users**: Verify ramp-up is smooth
- **Failures**: Investigate any spikes

### HTML Report Analysis

```bash
# Generate comprehensive report
locust -f tests/load/locustfile.py \
  --host=http://localhost:8000 \
  --users 100 \
  --run-time 10m \
  --headless \
  --html reports/load_test_$(date +%Y%m%d_%H%M%S).html
```

**Report Sections**:
1. **Request Statistics**: Response times, RPS, failures
2. **Response Time Distribution**: Histogram of response times
3. **Failures**: Detailed error messages
4. **Exceptions**: Stack traces for errors

### System Metrics Analysis

```bash
# Monitor system resources during test
python scripts/monitor_system.py --duration 600 --output reports/system_metrics.json

# Generate system metrics report
python scripts/analyze_system_metrics.py reports/system_metrics.json
```

### Database Performance Analysis

```sql
-- Check slow queries during load test
SELECT 
  query,
  calls,
  total_time,
  mean_time,
  max_time
FROM pg_stat_statements
WHERE mean_time > 100
ORDER BY total_time DESC
LIMIT 20;

-- Check connection pool usage
SELECT 
  count(*) as connections,
  state,
  wait_event_type
FROM pg_stat_activity
GROUP BY state, wait_event_type;

-- Check cache hit ratio
SELECT 
  sum(heap_blks_read) as heap_read,
  sum(heap_blks_hit) as heap_hit,
  sum(heap_blks_hit) / (sum(heap_blks_hit) + sum(heap_blks_read)) as ratio
FROM pg_statio_user_tables;
```

### Redis Performance Analysis

```bash
# Monitor Redis during test
redis-cli --stat

# Check memory usage
redis-cli INFO memory

# Check slow log
redis-cli SLOWLOG GET 10
```

## Bottleneck Identification

### Common Bottlenecks

#### 1. Database Connection Pool Exhaustion

**Symptoms**:
- Increasing response times
- "Too many connections" errors
- Requests timing out

**Diagnosis**:
```sql
SELECT count(*) FROM pg_stat_activity;
```

**Solutions**:
- Increase connection pool size
- Implement connection pooling at application level
- Use read replicas for read-heavy operations
- Optimize slow queries

#### 2. Slow Database Queries

**Symptoms**:
- High database CPU usage
- Increasing query execution times
- Lock contention

**Diagnosis**:
```sql
-- Find slow queries
SELECT * FROM pg_stat_statements 
WHERE mean_time > 100 
ORDER BY total_time DESC;

-- Check for missing indexes
SELECT * FROM pg_stat_user_tables 
WHERE seq_scan > 1000 AND idx_scan = 0;
```

**Solutions**:
- Add appropriate indexes
- Optimize query structure
- Use EXPLAIN ANALYZE
- Implement query result caching

#### 3. Memory Leaks

**Symptoms**:
- Steadily increasing memory usage
- Out of memory errors
- System slowdown over time

**Diagnosis**:
```bash
# Monitor memory usage
python scripts/memory_profiler.py

# Check for memory leaks in Python
pip install memory_profiler
python -m memory_profiler app/main.py
```

**Solutions**:
- Profile application memory usage
- Fix resource leaks (unclosed connections, file handles)
- Implement proper cleanup in finally blocks
- Use context managers

#### 4. CPU Bottlenecks

**Symptoms**:
- High CPU usage (> 80%)
- Slow response times
- Request queuing

**Diagnosis**:
```bash
# Profile CPU usage
python -m cProfile -o profile.stats app/main.py

# Analyze profile
python -c "import pstats; p = pstats.Stats('profile.stats'); p.sort_stats('cumulative'); p.print_stats(20)"
```

**Solutions**:
- Optimize hot code paths
- Use caching for expensive operations
- Implement async processing
- Scale horizontally

#### 5. Network Latency

**Symptoms**:
- High response times despite low server load
- Timeouts on external API calls
- Slow scraping operations

**Diagnosis**:
```bash
# Test network latency
ping -c 10 api.example.com

# Test API response times
curl -w "@curl-format.txt" -o /dev/null -s http://localhost:8000/api/jobs/search
```

**Solutions**:
- Use CDN for static assets
- Implement request caching
- Optimize payload sizes
- Use connection pooling for external APIs

#### 6. Redis Performance Issues

**Symptoms**:
- Slow cache operations
- High Redis CPU usage
- Memory eviction warnings

**Diagnosis**:
```bash
# Check Redis performance
redis-cli --latency
redis-cli --latency-history

# Check memory usage
redis-cli INFO memory
```

**Solutions**:
- Optimize cache key structure
- Implement proper TTL policies
- Use Redis pipelining
- Consider Redis cluster for scaling

## Optimization Strategies

### Application Level

1. **Implement Caching**
   - Cache frequently accessed data
   - Use Redis for session storage
   - Implement HTTP caching headers

2. **Optimize Database Queries**
   - Use select_related() and prefetch_related()
   - Avoid N+1 query problems
   - Use database indexes effectively

3. **Async Processing**
   - Move heavy operations to Celery tasks
   - Use async/await for I/O operations
   - Implement background job processing

4. **Connection Pooling**
   - Configure appropriate pool sizes
   - Reuse connections
   - Implement connection health checks

### Database Level

1. **Indexing Strategy**
   - Create indexes on frequently queried columns
   - Use composite indexes for multi-column queries
   - Monitor index usage and remove unused indexes

2. **Query Optimization**
   - Use EXPLAIN ANALYZE
   - Avoid SELECT *
   - Use appropriate JOIN types

3. **Database Configuration**
   - Tune shared_buffers
   - Optimize work_mem
   - Configure effective_cache_size

### Infrastructure Level

1. **Horizontal Scaling**
   - Add more application servers
   - Use load balancer
   - Implement read replicas

2. **Vertical Scaling**
   - Increase server resources (CPU, RAM)
   - Use faster storage (SSD)
   - Upgrade network bandwidth

3. **CDN and Caching**
   - Use CDN for static assets
   - Implement edge caching
   - Use reverse proxy caching

## Continuous Load Testing

### CI/CD Integration

```yaml
# .github/workflows/load-test.yml
name: Load Testing

on:
  schedule:
    - cron: '0 2 * * 0'  # Weekly on Sunday at 2 AM
  workflow_dispatch:

jobs:
  load-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install locust==2.20.0
      
      - name: Start services
        run: docker-compose up -d
      
      - name: Wait for services
        run: sleep 30
      
      - name: Run load test
        run: |
          locust -f tests/load/locustfile.py \
            --host=http://localhost:8000 \
            --users 50 \
            --spawn-rate 5 \
            --run-time 5m \
            --headless \
            --html reports/load_test_report.html
      
      - name: Upload results
        uses: actions/upload-artifact@v3
        with:
          name: load-test-results
          path: reports/
      
      - name: Check performance thresholds
        run: python scripts/check_performance_thresholds.py reports/load_test_results_stats.csv
```

### Monitoring and Alerts

```python
# scripts/check_performance_thresholds.py
import sys
import pandas as pd

def check_thresholds(csv_path):
    df = pd.read_csv(csv_path)
    
    failures = []
    
    # Check 95th percentile response times
    for _, row in df.iterrows():
        if row['95%'] > 1000:  # 1 second threshold
            failures.append(f"{row['Name']}: 95th percentile {row['95%']}ms exceeds 1000ms")
    
    # Check failure rate
    for _, row in df.iterrows():
        failure_rate = (row['Failure Count'] / row['Request Count']) * 100
        if failure_rate > 1:  # 1% threshold
            failures.append(f"{row['Name']}: Failure rate {failure_rate:.2f}% exceeds 1%")
    
    if failures:
        print("Performance thresholds exceeded:")
        for failure in failures:
            print(f"  - {failure}")
        sys.exit(1)
    else:
        print("All performance thresholds met!")
        sys.exit(0)

if __name__ == "__main__":
    check_thresholds(sys.argv[1])
```

## Best Practices

1. **Test in Isolation**: Use dedicated test environment
2. **Realistic Data**: Use production-like dataset sizes
3. **Gradual Ramp-up**: Don't start with maximum load
4. **Monitor Everything**: Track all system metrics
5. **Document Results**: Keep historical performance data
6. **Test Regularly**: Run load tests on schedule
7. **Test Before Deploy**: Load test before major releases
8. **Clean Up**: Reset test data between runs
9. **Version Control**: Track load test scripts in git
10. **Share Results**: Communicate findings with team

## Troubleshooting

### Issue: Locust Won't Start

```bash
# Check Python version
python --version  # Should be 3.11+

# Reinstall Locust
pip uninstall locust
pip install locust==2.20.0

# Check for port conflicts
lsof -i :8089
```

### Issue: Services Not Responding

```bash
# Check service status
docker-compose ps

# Check logs
docker-compose logs backend
docker-compose logs postgres
docker-compose logs redis

# Restart services
docker-compose restart
```

### Issue: Database Connection Errors

```bash
# Check PostgreSQL is running
docker-compose ps postgres

# Check connection
psql -h localhost -U postgres -d jobplatform

# Check connection pool
# In application logs, look for connection pool warnings
```

### Issue: High Error Rates

1. Check application logs for errors
2. Verify test data is properly seeded
3. Check authentication tokens are valid
4. Verify rate limits aren't being hit
5. Check database constraints aren't violated

## Conclusion

Load testing is critical for ensuring the Job Aggregation Platform can handle production traffic. Follow this guide to:

- Validate performance requirements
- Identify bottlenecks early
- Optimize system performance
- Build confidence in system scalability

Regular load testing helps maintain system reliability and provides data for capacity planning.

## References

- [Locust Documentation](https://docs.locust.io/)
- [PostgreSQL Performance Tuning](https://wiki.postgresql.org/wiki/Performance_Optimization)
- [Redis Performance Best Practices](https://redis.io/docs/management/optimization/)
- [FastAPI Performance Tips](https://fastapi.tiangolo.com/deployment/concepts/)
