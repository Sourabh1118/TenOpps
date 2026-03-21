# Rate Limiting Quick Reference

## Rate Limits by Tier

| Tier | Requests/Minute |
|------|----------------|
| Free | 100 |
| Basic | 200 |
| Premium | 500 |
| Unauthenticated | 100 (IP-based) |

## Response Headers

```
X-RateLimit-Limit: 100          # Max requests per minute
X-RateLimit-Remaining: 45       # Remaining in current window
X-RateLimit-Reset: 23           # Seconds until reset
```

## 429 Response Format

```json
{
  "detail": "Rate limit exceeded. Please try again later.",
  "limit": 100,
  "current": 101,
  "retry_after": 23
}
```

## Exempt Paths

- `/health`
- `/`
- `/docs`
- `/openapi.json`
- `/redoc`

## Admin Endpoints

### Get User Violations
```bash
GET /api/admin/rate-limit/violations/{user_id}?limit=100
```

### Get All Violators
```bash
GET /api/admin/rate-limit/violators?hours=24
```

### Get Statistics
```bash
GET /api/admin/rate-limit/stats?hours=24&top_n=10
```

### Clear Violations
```bash
DELETE /api/admin/rate-limit/violations/{user_id}
```

## Client Handling

```python
# Python
if response.status_code == 429:
    retry_after = int(response.headers.get('Retry-After', 60))
    time.sleep(retry_after)
    # Retry request
```

```typescript
// TypeScript
if (response.status === 429) {
  const retryAfter = parseInt(response.headers.get('Retry-After') || '60');
  await new Promise(resolve => setTimeout(resolve, retryAfter * 1000));
  // Retry request
}
```

## Testing

```bash
# Run tests
pytest tests/test_rate_limiting.py -v

# Manual test (should get 429 after 100 requests)
for i in {1..105}; do curl -i http://localhost:8000/api/jobs; done
```

## Redis Keys

- Rate limit counter: `rate_limit:{user_id}:{window_start}`
- Violation log: `rate_limit_violations:{user_id}`

## Configuration

Edit `app/core/rate_limiting.py`:

```python
RATE_LIMITS = {
    "standard": 100,
    SubscriptionTier.FREE: 100,
    SubscriptionTier.BASIC: 200,
    SubscriptionTier.PREMIUM: 500,
}
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Not working | Check Redis connection |
| Headers missing | Verify path not in EXEMPT_PATHS |
| False positives | Clear violations via admin endpoint |
| High memory | Logs auto-expire after 7 days |

## Monitoring

Watch for:
- Users with 10+ violations/hour
- Spike in 429 responses
- > 5% of requests rate limited

## Implementation Files

- Middleware: `app/core/rate_limiting.py`
- Admin API: `app/api/admin.py`
- Tests: `tests/test_rate_limiting.py`
- Registration: `app/main.py`
