# Load Testing Scripts

This directory contains load testing scripts for the Job Aggregation Platform.

**Validates: Requirements 16.1, 16.2, 16.3**

## Files

### `locustfile.py`
Main load testing file with realistic user behavior simulation.

**User Types:**
- `JobSeekerUser` (70%): Searches, views jobs, browses
- `EmployerUser` (20%): Posts jobs, manages dashboard, views applications
- `AnonymousUser` (10%): Browses without authentication

**Run:**
```bash
# With web UI
locust -f locustfile.py --host=http://localhost:8000

# Headless
locust -f locustfile.py --host=http://localhost:8000 --users 100 --run-time 10m --headless
```

### `test_search_performance.py`
Focused testing of search functionality with various query patterns.

**Test Patterns:**
- Simple keyword search
- Multi-filter search
- Location-based search
- Paginated search
- Salary range search
- Recent jobs search
- Featured jobs search

**Run:**
```bash
locust -f test_search_performance.py --host=http://localhost:8000 --users 50 --run-time 5m --headless
```

### `test_scraping_performance.py`
Tests scraping system performance with multiple concurrent sources.

**Tests:**
- Concurrent scraping (4 sources)
- Deduplication performance
- Quality scoring performance

**Run:**
```bash
python test_scraping_performance.py
```

## Quick Start

1. **Install Locust:**
   ```bash
   pip install locust==2.20.0
   ```

2. **Start services:**
   ```bash
   cd backend
   docker-compose up -d
   ```

3. **Run a test:**
   ```bash
   locust -f tests/load/locustfile.py --host=http://localhost:8000
   ```

4. **Open browser:**
   Navigate to http://localhost:8089

5. **Configure test:**
   - Number of users: 100
   - Spawn rate: 10
   - Host: http://localhost:8000

6. **Start test:**
   Click "Start Swarming"

## Performance Targets

| Metric | Target |
|--------|--------|
| API Response (GET) | < 200ms avg, < 500ms p95 |
| API Response (POST) | < 500ms avg, < 1000ms p95 |
| Search (simple) | < 100ms avg, < 200ms p95 |
| Search (complex) | < 200ms avg, < 500ms p95 |
| Error Rate | < 1% |
| Scraping Rate | > 100 jobs/min |

## Documentation

For detailed information, see:
- [Load Testing Guide](../../LOAD_TESTING_GUIDE.md)
- [Quick Reference](../../LOAD_TESTING_QUICK_REFERENCE.md)
- [Task Completion](../../TASK_37.6_LOAD_TESTING_COMPLETION.md)

## Monitoring

Run system monitoring during tests:
```bash
python scripts/monitor_system.py --duration 600 --output reports/system_metrics.json
```

## Threshold Checking

Check results against thresholds:
```bash
python scripts/check_performance_thresholds.py reports/load_test_results_stats.csv
```

## Tips

- Start with small user counts and ramp up gradually
- Monitor system resources during tests
- Use headless mode for CI/CD integration
- Generate HTML reports for detailed analysis
- Run tests in isolated environment
- Clean up test data between runs
