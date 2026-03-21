# Rate Limiting Guide

## Overview

The Job Aggregation Platform implements comprehensive rate limiting to protect the API from abuse and ensure fair resource allocation. Rate limiting is enforced at the middleware level using Redis for distributed tracking.

## Features

### 1. Request Tracking (Requirement 14.1)
- Tracks request count per user per minute
- Uses Redis for distributed rate limiting across multiple servers
- Automatically resets counters every minute

### 2. Rate Limit Enforcement (Requirement 14.2)
- Rejects requests exceeding the limit with HTTP 429 (Too Many Requests)
- Returns clear error messages with current count and limit
- Includes rate limit information in response headers

### 3. Retry-After Header (Requirement 14.4)
- All 429 responses include `Retry-After` header
- Indicates seconds until the next minute window
- Helps clients implement proper backoff strategies

### 4. Tier-Based Limits (Requirement 14.5)
- **Free Tier**: 100 requests/minute
- **Basic Tier**: 200 requests/minute
- **Premium Tier**: 500 requests/minute
- **Unauthenticated**: 100 requests/minute (IP-based)

### 5. Violation Monitoring (Requirement 14.6)
- Logs all rate limit violations
- Tracks repeated violations per user
- Alerts administrators for users with 5+ violations per hour
- Provides admin endpoints for violation review

## Rate Limit Headers

All API responses include rate limit information in headers:

```
X-RateLimit-Limit: 100          # Maximum requests per minute
X-RateLimit-Remaining: 45       # Remaining requests in current window
X-RateLimit-Reset: 23           # Seconds until window resets
```

When rate limit is exceeded:

```
HTTP/1.1 429 Too Many Requests
Retry-After: 23
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 23

{
  "detail": "Rate limit exceeded. Please try again later.",
  "limit": 100,
  "current": 101,
  "retry_after": 23
}
```

## Exempt Paths

The following paths are exempt from rate limiting:

- `/health` - Health check endpoint
- `/` - Root endpoint
- `/docs` - API documentation
- `/openapi.json` - OpenAPI schema
- `/redoc` - ReDoc documentation

## User Identification

Rate limits are tracked per user:

1. **Authenticated Users**: Identified by JWT token (user_id from `sub` claim)
2. **Unauthenticated Users**: Identified by IP address

For employers, the system automatically retrieves their subscription tier to apply appropriate rate limits.

## Admin Monitoring

Administrators can monitor rate limit violations using the following endpoints:

### Get User Violations

```bash
GET /api/admin/rate-limit/violations/{user_id}?limit=100
Authorization: Bearer <admin_token>
```

Returns recent violations for a specific user:

```json
{
  "user_id": "123e4567-e89b-12d3-a456-426614174000",
  "violations": [
    {
      "timestamp": "2024-01-15T10:30:45Z",
      "user_id": "123e4567-e89b-12d3-a456-426614174000",
      "path": "/api/jobs",
      "count": 101,
      "limit": 100
    }
  ],
  "total_count": 1
}
```

### Get All Violators

```bash
GET /api/admin/rate-limit/violators?hours=24
Authorization: Bearer <admin_token>
```

Returns list of users with violations in the specified time window:

```json
{
  "violators": [
    "123e4567-e89b-12d3-a456-426614174000",
    "987fcdeb-51a2-43f7-8b9c-123456789abc"
  ],
  "total_count": 2,
  "time_window_hours": 24
}
```

### Get Rate Limit Statistics

```bash
GET /api/admin/rate-limit/stats?hours=24&top_n=10
Authorization: Bearer <admin_token>
```

Returns aggregate statistics:

```json
{
  "total_violators": 15,
  "time_window_hours": 24,
  "top_violators": [
    {
      "user_id": "123e4567-e89b-12d3-a456-426614174000",
      "violation_count": 25
    },
    {
      "user_id": "987fcdeb-51a2-43f7-8b9c-123456789abc",
      "violation_count": 12
    }
  ]
}
```

### Clear User Violations

```bash
DELETE /api/admin/rate-limit/violations/{user_id}
Authorization: Bearer <admin_token>
```

Clears violation history for a user (useful after resolving issues).

## Implementation Details

### Redis Keys

Rate limiting uses the following Redis key patterns:

- **Rate Limit Counter**: `rate_limit:{user_id}:{window_start}`
  - Stores request count for current minute window
  - Expires after 2 minutes
  - Example: `rate_limit:user-123:1705320000`

- **Violation Log**: `rate_limit_violations:{user_id}`
  - Sorted set of violation records
  - Keeps last 100 violations per user
  - Expires after 7 days
  - Example: `rate_limit_violations:user-123`

### Middleware Order

Rate limiting middleware is applied in the following order:

1. CORS Middleware
2. CSRF Protection Middleware
3. **Rate Limit Middleware** ← Applied here
4. Security Headers Middleware
5. HTTPS Redirect Middleware

This ensures rate limiting happens early in the request pipeline but after CSRF validation.

### Error Handling

The rate limiting system is designed to "fail open":

- If Redis is unavailable, requests are allowed through
- Errors are logged but don't block legitimate traffic
- This prevents Redis outages from taking down the entire API

### Performance

- **Redis Operations**: Single `INCR` operation per request (O(1))
- **Memory Usage**: ~100 bytes per user per minute window
- **Overhead**: < 1ms per request
- **Scalability**: Supports distributed deployments with shared Redis

## Client Implementation

### Respecting Rate Limits

Clients should:

1. **Check Headers**: Monitor `X-RateLimit-Remaining` header
2. **Handle 429**: Implement exponential backoff when rate limited
3. **Use Retry-After**: Wait the specified seconds before retrying
4. **Upgrade Tier**: Consider upgrading subscription if frequently rate limited

### Example Client Code

```python
import requests
import time

def make_api_request(url, headers):
    response = requests.get(url, headers=headers)
    
    # Check rate limit headers
    remaining = int(response.headers.get('X-RateLimit-Remaining', 0))
    
    if remaining < 10:
        print(f"Warning: Only {remaining} requests remaining")
    
    # Handle rate limit
    if response.status_code == 429:
        retry_after = int(response.headers.get('Retry-After', 60))
        print(f"Rate limited. Waiting {retry_after} seconds...")
        time.sleep(retry_after)
        return make_api_request(url, headers)  # Retry
    
    return response
```

### JavaScript/TypeScript Example

```typescript
async function makeApiRequest(url: string, headers: Headers): Promise<Response> {
  const response = await fetch(url, { headers });
  
  // Check rate limit headers
  const remaining = parseInt(response.headers.get('X-RateLimit-Remaining') || '0');
  
  if (remaining < 10) {
    console.warn(`Warning: Only ${remaining} requests remaining`);
  }
  
  // Handle rate limit
  if (response.status === 429) {
    const retryAfter = parseInt(response.headers.get('Retry-After') || '60');
    console.log(`Rate limited. Waiting ${retryAfter} seconds...`);
    await new Promise(resolve => setTimeout(resolve, retryAfter * 1000));
    return makeApiRequest(url, headers);  // Retry
  }
  
  return response;
}
```

## Testing

### Unit Tests

Run rate limiting unit tests:

```bash
pytest tests/test_rate_limiting.py -v
```

### Manual Testing

Test rate limiting manually:

```bash
# Make multiple requests quickly
for i in {1..105}; do
  curl -i http://localhost:8000/api/jobs
  echo "Request $i"
done
```

You should see:
- First 100 requests: HTTP 200 with decreasing `X-RateLimit-Remaining`
- Requests 101+: HTTP 429 with `Retry-After` header

### Load Testing

Test rate limiting under load:

```bash
# Using Apache Bench
ab -n 200 -c 10 http://localhost:8000/api/jobs

# Using wrk
wrk -t4 -c100 -d30s http://localhost:8000/api/jobs
```

## Configuration

Rate limits are configured in `app/core/rate_limiting.py`:

```python
RATE_LIMITS = {
    "standard": 100,  # Free tier and unauthenticated
    SubscriptionTier.FREE: 100,
    SubscriptionTier.BASIC: 200,
    SubscriptionTier.PREMIUM: 500,
}
```

To modify rate limits:

1. Update the `RATE_LIMITS` dictionary
2. Restart the application
3. No database migration required (configuration only)

## Monitoring

### Logs

Rate limit violations are logged at WARNING level:

```
WARNING: Rate limit violation: user=user-123, path=/api/jobs, count=101, limit=100
```

Repeated violations (5+ per hour) are logged at ERROR level:

```
ERROR: ALERT: Repeated rate limit violations detected for user user-123: 6 violations in last hour
```

### Metrics

Monitor these metrics:

- **Rate Limit Violations**: Count of 429 responses
- **Top Violators**: Users with most violations
- **Violation Trends**: Violations over time
- **Tier Distribution**: Violations by subscription tier

### Alerts

Set up alerts for:

- Users with 10+ violations per hour
- Sudden spike in rate limit violations
- High percentage of requests being rate limited (> 5%)

## Troubleshooting

### Issue: Legitimate users being rate limited

**Solution**: 
- Check if user needs subscription upgrade
- Review user's request patterns
- Consider increasing limits for specific users
- Clear violation history if false positive

### Issue: Rate limiting not working

**Checklist**:
1. Verify Redis is running: `redis-cli ping`
2. Check Redis connection in logs
3. Verify middleware is registered in `main.py`
4. Check exempt paths configuration

### Issue: Rate limit headers missing

**Cause**: Request to exempt path or middleware not applied

**Solution**: Verify path is not in `EXEMPT_PATHS` list

### Issue: Redis memory usage growing

**Cause**: Violation logs accumulating

**Solution**: 
- Logs automatically expire after 7 days
- Manually clear old violations: `redis-cli DEL rate_limit_violations:*`
- Reduce violation retention period

## Best Practices

1. **Monitor Regularly**: Review violation logs weekly
2. **Communicate Limits**: Document rate limits in API documentation
3. **Provide Feedback**: Include clear error messages with upgrade paths
4. **Test Thoroughly**: Test rate limiting in staging before production
5. **Plan Capacity**: Ensure Redis can handle peak traffic
6. **Set Alerts**: Alert on unusual violation patterns
7. **Review Tiers**: Adjust tier limits based on usage patterns

## Security Considerations

1. **DDoS Protection**: Rate limiting provides basic DDoS protection
2. **Brute Force Prevention**: Limits password guessing attempts
3. **Resource Protection**: Prevents resource exhaustion
4. **Fair Usage**: Ensures fair resource allocation among users

## Future Enhancements

Potential improvements:

1. **Dynamic Limits**: Adjust limits based on system load
2. **Burst Allowance**: Allow short bursts above limit
3. **Per-Endpoint Limits**: Different limits for different endpoints
4. **Geographic Limits**: Different limits by region
5. **Time-Based Limits**: Different limits by time of day
6. **Custom Limits**: Per-user custom rate limits
