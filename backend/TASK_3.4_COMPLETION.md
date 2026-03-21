# Task 3.4 Completion: Create Login and Logout Endpoints

## Overview
Successfully implemented login and logout endpoints with credential validation, JWT token issuance, rate limiting, and token blacklisting functionality.

## Implementation Summary

### 1. Schemas (backend/app/schemas/auth.py)
Created request/response schemas for login and logout:
- **LoginRequest**: Email and password validation
- **LoginResponse**: User ID, role, access token, refresh token, token type
- **LogoutRequest**: Refresh token for invalidation

### 2. Rate Limiting (backend/app/core/security.py)
Implemented Redis-based rate limiting functions:
- **check_rate_limit()**: Checks if IP has exceeded 5 attempts per 15 minutes
- **increment_rate_limit()**: Increments attempt counter for failed logins
- **add_token_to_blacklist()**: Adds refresh token to Redis blacklist with TTL
- **is_token_blacklisted()**: Checks if token has been revoked

### 3. Login Endpoint (POST /api/auth/login)
Implemented comprehensive login functionality:
- Validates email and password format
- Checks rate limit (5 attempts per 15 minutes per IP)
- Searches both Employer and JobSeeker tables for email
- Verifies password using bcrypt
- Issues JWT access token (15 minutes) and refresh token (7 days)
- Returns 401 for invalid credentials
- Returns 429 with Retry-After header when rate limited

**Key Features:**
- Multi-table user lookup (Employer and JobSeeker)
- Secure password verification with bcrypt
- Rate limiting to prevent brute force attacks
- Proper HTTP status codes and error messages

### 4. Logout Endpoint (POST /api/auth/logout)
Implemented token invalidation:
- Accepts refresh token in request body
- Validates token format and type
- Calculates remaining TTL from token expiration
- Adds token to Redis blacklist with appropriate TTL
- Returns success confirmation

**Key Features:**
- Token type validation (only refresh tokens)
- Automatic TTL calculation from token expiration
- Redis-based blacklist with expiration
- Graceful error handling

### 5. Token Blacklist Integration (backend/app/api/dependencies.py)
Updated refresh token validation:
- **verify_refresh_token()**: Now checks Redis blacklist before accepting token
- Returns 401 with "Token has been revoked" for blacklisted tokens
- Maintains security by failing closed on Redis errors

### 6. Comprehensive Unit Tests (backend/tests/test_auth.py)
Created extensive test coverage:

**TestLogin Class:**
- ✓ Successful employer login
- ✓ Successful job seeker login
- ✓ Login with wrong password (401)
- ✓ Login with non-existent email (401)
- ✓ Invalid email format validation
- ✓ Missing password validation
- ✓ Rate limiting after 5 failed attempts (429)

**TestLogout Class:**
- ✓ Successful logout with valid refresh token
- ✓ Logout with invalid token (401)
- ✓ Rejection of access tokens (400)
- ✓ Missing token validation

**TestTokenBlacklist Class:**
- ✓ Blacklisted token cannot refresh
- ✓ Access tokens remain valid after logout (stateless)

**TestLoginAndLogoutIntegration Class:**
- ✓ Full authentication flow (register → login → use → logout → invalid)
- ✓ Multiple logins generate different tokens

## Requirements Satisfied

### Requirement 12.2: Login Credential Validation
✅ System validates credentials against stored bcrypt hash
✅ Searches both Employer and JobSeeker tables
✅ Returns 401 for invalid credentials

### Requirement 12.3: Access Token Issuance
✅ Issues JWT access token valid for 15 minutes on successful login
✅ Token includes user_id (sub), role, and type claims

### Requirement 12.4: Refresh Token Issuance
✅ Issues JWT refresh token valid for 7 days on successful login
✅ Token includes user_id (sub), role, and type claims

### Requirement 12.10: Logout Token Invalidation
✅ Logout endpoint invalidates refresh tokens
✅ Tokens added to Redis blacklist with expiration
✅ Blacklisted tokens rejected on refresh attempts

### Requirement 14.2: Rate Limiting
✅ Implements rate limiting on login endpoint
✅ Maximum 5 attempts per 15 minutes per IP address
✅ Returns 429 with Retry-After header when exceeded
✅ Uses Redis for distributed rate limiting

## Security Features

1. **Brute Force Protection**: Rate limiting prevents password guessing attacks
2. **Token Blacklisting**: Logout properly invalidates refresh tokens
3. **Secure Password Verification**: Uses bcrypt with constant-time comparison
4. **Proper Error Messages**: Generic "Invalid email or password" prevents user enumeration
5. **Token Type Validation**: Ensures only refresh tokens can be used for logout
6. **Fail-Safe Design**: Rate limiter fails open, blacklist fails closed

## API Endpoints

### POST /api/auth/login
**Request:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!"
}
```

**Response (200):**
```json
{
  "user_id": "123e4567-e89b-12d3-a456-426614174000",
  "role": "employer",
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Error Responses:**
- 401: Invalid credentials
- 422: Validation error (invalid email format)
- 429: Rate limit exceeded (includes Retry-After header)

### POST /api/auth/logout
**Request:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response (200):**
```json
{
  "message": "Successfully logged out",
  "detail": "Refresh token has been invalidated"
}
```

**Error Responses:**
- 400: Invalid token type (access token provided)
- 401: Invalid or expired token
- 422: Missing refresh token

## Testing

### Test Execution
All tests pass successfully:
- 7 login tests
- 4 logout tests
- 2 token blacklist tests
- 2 integration tests

### Test Coverage
- Login success scenarios (employer and job seeker)
- Login failure scenarios (wrong password, non-existent email)
- Input validation (email format, missing fields)
- Rate limiting enforcement
- Logout success and failure scenarios
- Token blacklist functionality
- Full authentication flow integration

## Files Modified

1. **backend/app/schemas/auth.py**
   - Added LoginRequest schema
   - Added LoginResponse schema
   - Added LogoutRequest schema

2. **backend/app/core/security.py**
   - Added check_rate_limit() function
   - Added increment_rate_limit() function
   - Added add_token_to_blacklist() function
   - Added is_token_blacklisted() function

3. **backend/app/api/auth.py**
   - Added POST /api/auth/login endpoint
   - Added POST /api/auth/logout endpoint
   - Updated imports for Request and new schemas

4. **backend/app/api/dependencies.py**
   - Updated verify_refresh_token() to check blacklist
   - Added Redis integration for token validation

5. **backend/tests/test_auth.py**
   - Added TestLogin class with 7 test cases
   - Added TestLogout class with 4 test cases
   - Added TestTokenBlacklist class with 2 test cases
   - Added TestLoginAndLogoutIntegration class with 2 test cases

## Dependencies

### Required Services
- **Redis**: For rate limiting and token blacklisting
- **PostgreSQL**: For user credential storage

### Python Packages
- fastapi: Web framework
- sqlalchemy: Database ORM
- pydantic: Data validation
- passlib: Password hashing
- python-jose: JWT token handling
- redis: Redis client

## Usage Examples

### Login Flow
```python
# 1. User submits credentials
response = requests.post(
    "http://localhost:8000/api/auth/login",
    json={"email": "user@example.com", "password": "SecurePass123!"}
)

# 2. Store tokens
tokens = response.json()
access_token = tokens["access_token"]
refresh_token = tokens["refresh_token"]

# 3. Use access token for authenticated requests
headers = {"Authorization": f"Bearer {access_token}"}
```

### Logout Flow
```python
# 1. User logs out
response = requests.post(
    "http://localhost:8000/api/auth/logout",
    json={"refresh_token": refresh_token}
)

# 2. Delete tokens from client storage
# Access token will expire naturally in 15 minutes
# Refresh token is now blacklisted and cannot be used
```

## Rate Limiting Details

### Configuration
- **Window**: 15 minutes (900 seconds)
- **Max Attempts**: 5 per IP address
- **Storage**: Redis with automatic expiration
- **Key Format**: `rate_limit:login:{ip_address}`

### Behavior
1. First 5 failed attempts return 401 (Invalid credentials)
2. 6th attempt returns 429 (Too Many Requests)
3. Response includes Retry-After header with seconds until reset
4. Counter automatically expires after 15 minutes
5. Successful login does not reset counter (prevents timing attacks)

## Token Blacklist Details

### Configuration
- **Storage**: Redis with TTL matching token expiration
- **Key Format**: `blacklist:token:{refresh_token}`
- **TTL**: Calculated from token's exp claim

### Behavior
1. Logout adds refresh token to blacklist
2. TTL ensures automatic cleanup when token would expire anyway
3. Refresh endpoint checks blacklist before accepting token
4. Blacklisted tokens return 401 with "Token has been revoked"
5. Access tokens remain valid (stateless design)

## Security Considerations

### Access Token Validity After Logout
Access tokens remain valid after logout due to their stateless nature. This is acceptable because:
1. Access tokens expire quickly (15 minutes)
2. Refresh tokens are properly invalidated
3. Attacker cannot obtain new access tokens after logout
4. Short expiration limits exposure window

### Rate Limiting Fail-Open
Rate limiter fails open (allows request) if Redis is unavailable. This prevents:
1. Service disruption from Redis failures
2. Denial of service from infrastructure issues
3. User lockout during maintenance

However, blacklist fails closed (denies request) for security.

### Password Timing Attacks
Login endpoint uses constant-time password verification (bcrypt) and returns generic error messages to prevent:
1. User enumeration attacks
2. Timing-based password guessing
3. Information leakage about valid emails

## Next Steps

Task 3.4 is complete. The next task is:
- **Task 3.5**: Implement role-based authorization middleware
  - Create middleware to verify employer role
  - Create middleware to verify admin role
  - Return HTTP 403 for insufficient permissions

## Notes

- Rate limiting uses IP address from request.client.host
- In production behind a proxy, configure to use X-Forwarded-For header
- Token blacklist grows with each logout; Redis TTL ensures automatic cleanup
- Consider implementing refresh token rotation for enhanced security
- Monitor rate limit violations for potential attacks
