# Load Testing Quick Reference

Quick commands and tips for running load tests on the Job Aggregation Platform.

**Validates: Requirements 16.1, 16.2, 16.3**

## Quick Start

```bash
# Install Locust
pip install locust==2.20.0

# Start services
cd backend
docker-compose up -d

# Run basic load test with UI
locust -f tests/load/locustfile.py --host=http://localhost:8000
# Open http://localhost:8089 in browser

# Run headless test
locust -f tests/load/locustfile.py \
  --host=http://localhost:8000 \
  --users 100 \
  --spawn-rate 10 \
  --run-time 10m \
  --headless
```

## Common Test Scenarios

### 1. API Load Test (100 Concurrent Users)
```bash
locust -f tests/load/locustfile.py \
  --host=http://localhost:8000 \
  --users 100 \
  --spawn-rate 10 \
  --run-time 10m \
  --headless \
  --html reports/api_load_test.html
```

**Expected Results:**
- 95th percentile < 500ms for reads
- 95th percentile < 1000ms for writes
- Error rate < 1%

### 2. Search Performance Test
```bash
locust -f tests/load/test_search_performance.py \
  --host=http://localhost:8000 \
  --users 50 \
  --spawn-rate 5 \
  --run-time 5m \
  --headless \
  --html reports/search_performance.html
```

**Expected Results:**
- Average response time < 200ms
- 95th percentile < 500ms
- Cache hit rate > 60%

### 3. Scraping Performance Test
```bash
python tests/load/test_scraping_performance.py
```

**Expected Results:**
- 100+ jobs per minute
- Error rate < 5%
- Deduplication < 5s per job
- Quality scoring < 1s per job

### 4. Mixed Workload Test
```bash
locust -f tests/load/locustfile.py \
  --host=http://localhost:8000 \
  --users 200 \
  --spawn-rate 20 \
  --run-time 20m \
  --headless \
  --html reports/mixed_workload.html
```

**Expected Results:**
- System remains stable
- CPU < 80%
- Memory < 80%
- DB connections < 80% of pool

### 5. Spike Test
```bash
# Start with 20 users, spike to 200, return to 20
locust -f tests/load/locustfile.py \
  --host=http://localhost:8000 \
  --users 200 \
  --spawn-rate 50 \
  --run-time 5m \
  --headless
```

**Expected Results:**
- No crashes during spike
- Recovery within 30 seconds
- Graceful degradation

## Performance Targets

| Metric | Target | Critical |
|--------|--------|----------|
| API Response (GET) | < 200ms | > 1000ms |
| API Response (POST) | < 500ms | > 2000ms |
| Search (simple) | < 100ms | > 500ms |
| Search (complex) | < 200ms | > 1000ms |
| Error Rate | < 1% | > 5% |
| CPU Usage | < 70% | > 90% |
| Memory Usage | < 75% | > 90% |
| DB Connections | < 70% | > 85% |

## Monitoring During Tests

### System Resources
```bash
# Monitor CPU and memory
htop

# Monitor disk I/O
iostat -x 1

# Monitor network
iftop
```

### Database Performance
```bash
# Connect to PostgreSQL
docker-compose exec postgres psql -U postgres -d jobplatform

# Check active connections
SELECT count(*), state FROM pg_stat_activity GROUP BY state;

# Check slow queries
SELECT query, mean_time, calls 
FROM pg_stat_statements 
WHERE mean_time > 100 
ORDER BY mean_time DESC 
LIMIT 10;
```

### Redis Performance
```bash
# Monitor Redis
docker-compose exec redis redis-cli --stat

# Check memory
docker-compose exec redis redis-cli INFO memory

# Check slow log
docker-compose exec redis redis-cli SLOWLOG GET 10
```

### Application Logs
```bash
# Follow backend logs
docker-compose logs -f backend

# Check for errors
docker-compose logs backend | grep ERROR

# Check for warnings
docker-compose logs backend | grep WARN
```

## Distributed Load Testing

For higher load, run Locust in distributed mode:

```bash
# Terminal 1: Start master
locust -f tests/load/locustfile.py \
  --master \
  --host=http://localhost:8000 \
  --expect-workers=3

# Terminal 2-4: Start workers
locust -f tests/load/locustfile.py --worker --master-host=localhost
locust -f tests/load/locustfile.py --worker --master-host=localhost
locust -f tests/load/locustfile.py --worker --master-host=localhost
```

## Analyzing Results

### Locust HTML Report
```bash
# Generate report
locust -f tests/load/locustfile.py \
  --host=http://localhost:8000 \
  --users 100 \
  --run-time 10m \
  --headless \
  --html reports/report_$(date +%Y%m%d_%H%M%S).html \
  --csv reports/results_$(date +%Y%m%d_%H%M%S)
```

### Key Metrics to Check
1. **Total Requests per Second**: Should be stable
2. **Response Times**: Check 50th, 95th, 99th percentiles
3. **Failure Rate**: Should be < 1%
4. **Response Time Distribution**: Look for outliers

### CSV Analysis
```python
import pandas as pd

# Load results
df = pd.read_csv('reports/results_stats.csv')

# Calculate metrics
print(f"Average RPS: {df['Requests/s'].mean():.2f}")
print(f"Average Response Time: {df['Average Response Time'].mean():.2f}ms")
print(f"Total Failures: {df['Failure Count'].sum()}")
```

## Common Issues and Solutions

### High Response Times
- Check database query performance
- Verify indexes are in place
- Check for N+1 query problems
- Increase connection pool size

### Connection Pool Exhausted
```python
# In config.py, increase pool size
SQLALCHEMY_POOL_SIZE = 20
SQLALCHEMY_MAX_OVERFLOW = 10
```

### Memory Leaks
```bash
# Profile memory usage
pip install memory_profiler
python -m memory_profiler app/main.py
```

### Rate Limiting Triggered
- Adjust rate limits in config
- Use different test accounts
- Implement token bucket algorithm

### Database Locks
```sql
-- Check for locks
SELECT * FROM pg_locks WHERE NOT granted;

-- Kill blocking queries
SELECT pg_terminate_backend(pid) 
FROM pg_stat_activity 
WHERE state = 'idle in transaction';
```

## CI/CD Integration

Add to `.github/workflows/load-test.yml`:

```yaml
name: Weekly Load Test
on:
  schedule:
    - cron: '0 2 * * 0'  # Sunday 2 AM

jobs:
  load-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run load test
        run: |
          pip install locust==2.20.0
          docker-compose up -d
          sleep 30
          locust -f tests/load/locustfile.py \
            --host=http://localhost:8000 \
            --users 50 \
            --run-time 5m \
            --headless \
            --html reports/load_test.html
      - name: Upload results
        uses: actions/upload-artifact@v3
        with:
          name: load-test-results
          path: reports/
```

## Best Practices

1. ✓ Test in isolated environment
2. ✓ Use realistic test data
3. ✓ Ramp up gradually
4. ✓ Monitor all metrics
5. ✓ Document results
6. ✓ Test regularly
7. ✓ Clean up after tests
8. ✓ Version control test scripts
9. ✓ Share findings with team
10. ✓ Set up alerts for failures

## Resources

- [Locust Documentation](https://docs.locust.io/)
- [Load Testing Guide](./LOAD_TESTING_GUIDE.md)
- [Performance Optimization Guide](./PERFORMANCE_OPTIMIZATION_QUICK_REFERENCE.md)
- [Deployment Guide](../DEPLOYMENT_GUIDE.md)
