# Security Guide: Password Hashing and Validation

This guide explains the password security implementation for the Job Aggregation Platform, covering password hashing, verification, and strength validation.

## Overview

The platform implements secure password handling using bcrypt with a cost factor of 12, as specified in Requirement 12.1. All password operations are centralized in the `app.core.security` module.

## Password Hashing

### Implementation

Passwords are hashed using bcrypt with a cost factor of 12, providing strong protection against brute-force attacks.

```python
from app.core.security import hash_password

# Hash a password
hashed = hash_password("MySecurePass123!")
```

### Key Features

- **Cost Factor 12**: Provides strong security while maintaining reasonable performance
- **Automatic Salt Generation**: Each password gets a unique salt
- **One-Way Hashing**: Passwords cannot be reversed from the hash
- **Future-Proof**: Cost factor can be increased as computing power grows

### Technical Details

- Algorithm: bcrypt
- Cost Factor: 12 (2^12 = 4,096 iterations)
- Hash Format: `$2b$12$[salt][hash]`
- Hash Length: 60 characters

## Password Verification

### Implementation

Verify a plain password against a stored hash:

```python
from app.core.security import verify_password

# Verify password
is_valid = verify_password("MySecurePass123!", hashed_password)
if is_valid:
    # Password is correct
    pass
else:
    # Password is incorrect
    pass
```

### Key Features

- **Constant-Time Comparison**: Prevents timing attacks
- **Error Handling**: Gracefully handles malformed hashes
- **Case-Sensitive**: Passwords are case-sensitive

### Security Considerations

- Always use `verify_password()` for password checking
- Never compare password hashes directly
- Never log or expose password hashes
- Implement rate limiting on login attempts

## Password Strength Validation

### Implementation

Validate password strength before accepting user registration:

```python
from app.core.security import validate_password_strength

# Validate password
is_valid, error_message = validate_password_strength("MySecurePass123!")
if is_valid:
    # Password meets all requirements
    hashed = hash_password("MySecurePass123!")
else:
    # Password is weak, show error_message to user
    print(error_message)
```

### Password Requirements

All passwords must meet the following criteria:

1. **Minimum Length**: At least 8 characters
2. **Uppercase Letter**: At least one uppercase letter (A-Z)
3. **Lowercase Letter**: At least one lowercase letter (a-z)
4. **Digit**: At least one digit (0-9)
5. **Special Character**: At least one special character (!@#$%^&*()_+-=[]{}|;:,.<>?/~`)

### Example Valid Passwords

- `MySecurePass123!`
- `P@ssw0rd2024`
- `Admin#User99`
- `Test_Password1`

### Example Invalid Passwords

| Password | Issue |
|----------|-------|
| `short1!` | Too short (< 8 characters) |
| `lowercase123!` | Missing uppercase letter |
| `UPPERCASE123!` | Missing lowercase letter |
| `NoDigitsHere!` | Missing digit |
| `NoSpecial123` | Missing special character |

## Usage in Authentication Flow

### User Registration

```python
from app.core.security import validate_password_strength, hash_password

def register_user(email: str, password: str):
    # 1. Validate password strength
    is_valid, error = validate_password_strength(password)
    if not is_valid:
        raise ValueError(f"Weak password: {error}")
    
    # 2. Hash the password
    password_hash = hash_password(password)
    
    # 3. Store user with hashed password
    user = User(email=email, password_hash=password_hash)
    db.add(user)
    db.commit()
    
    return user
```

### User Login

```python
from app.core.security import verify_password

def login_user(email: str, password: str):
    # 1. Retrieve user from database
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise ValueError("Invalid credentials")
    
    # 2. Verify password
    if not verify_password(password, user.password_hash):
        raise ValueError("Invalid credentials")
    
    # 3. Generate and return JWT token
    token = create_access_token(user.id)
    return token
```

### Password Reset

```python
from app.core.security import validate_password_strength, hash_password

def reset_password(user_id: str, new_password: str):
    # 1. Validate new password strength
    is_valid, error = validate_password_strength(new_password)
    if not is_valid:
        raise ValueError(f"Weak password: {error}")
    
    # 2. Hash the new password
    password_hash = hash_password(new_password)
    
    # 3. Update user's password
    user = db.query(User).filter(User.id == user_id).first()
    user.password_hash = password_hash
    db.commit()
```

## Security Best Practices

### Do's

✅ **Always validate password strength** before hashing
✅ **Use `hash_password()`** for all password hashing
✅ **Use `verify_password()`** for all password verification
✅ **Implement rate limiting** on login endpoints
✅ **Use HTTPS** for all authentication endpoints
✅ **Log authentication failures** for security monitoring
✅ **Implement account lockout** after multiple failed attempts
✅ **Use JWT tokens** with short expiration times

### Don'ts

❌ **Never store plain text passwords**
❌ **Never log passwords** (plain or hashed)
❌ **Never expose password hashes** in API responses
❌ **Never compare hashes directly** (use `verify_password()`)
❌ **Never reuse passwords** across different services
❌ **Never send passwords** via email or insecure channels
❌ **Never use weak hashing algorithms** (MD5, SHA1)

## Performance Considerations

### Hashing Performance

- **Cost Factor 12**: ~100-200ms per hash on modern hardware
- **Acceptable for Authentication**: Users expect slight delay during login/registration
- **Not Suitable for High-Frequency Operations**: Don't hash passwords in loops or batch operations

### Optimization Tips

1. **Cache Authentication Results**: Use session tokens after initial login
2. **Implement Rate Limiting**: Prevent brute-force attacks
3. **Use Async Operations**: Hash passwords asynchronously in background tasks
4. **Monitor Performance**: Track hashing times in production

## Testing

### Unit Tests

The security module includes comprehensive unit tests:

```bash
# Run security tests
pytest tests/test_security.py -v

# Run with coverage
pytest tests/test_security.py --cov=app.core.security --cov-report=term
```

### Test Coverage

- ✅ Password hashing with bcrypt cost factor 12
- ✅ Password verification (correct and incorrect)
- ✅ Password strength validation (all requirements)
- ✅ Edge cases (empty passwords, special characters, unicode)
- ✅ Error handling (malformed hashes, None values)
- ✅ Complete authentication workflows

## Compliance

### OWASP Guidelines

This implementation follows OWASP password storage recommendations:

- ✅ Use strong adaptive hashing (bcrypt)
- ✅ Use sufficient cost factor (12)
- ✅ Use unique salt per password (automatic)
- ✅ Enforce password complexity requirements
- ✅ Implement secure password reset flow

### Regulatory Compliance

- **GDPR**: Passwords are hashed and cannot be recovered
- **PCI DSS**: Strong cryptography for password storage
- **HIPAA**: Secure authentication mechanisms

## Troubleshooting

### Common Issues

#### Issue: "Password cannot be empty"

**Cause**: Attempting to hash an empty or None password

**Solution**: Validate input before calling `hash_password()`

```python
if not password:
    raise ValueError("Password is required")
hashed = hash_password(password)
```

#### Issue: Verification always returns False

**Cause**: Comparing wrong password or corrupted hash

**Solution**: Verify the hash is stored correctly and password is exact match

```python
# Debug verification
print(f"Hash length: {len(hashed_password)}")  # Should be 60
print(f"Hash prefix: {hashed_password[:7]}")   # Should be $2b$12$
```

#### Issue: Slow password hashing

**Cause**: Cost factor 12 is computationally intensive

**Solution**: This is expected behavior. Consider:
- Using async operations for registration
- Implementing caching for authenticated sessions
- Monitoring performance in production

## Migration Guide

### Upgrading from Weaker Hashing

If migrating from a weaker hashing algorithm:

1. **Dual Verification**: Support both old and new hashes temporarily
2. **Gradual Migration**: Rehash passwords on next login
3. **Force Reset**: Require password reset for inactive accounts

```python
def verify_and_upgrade_password(user, password):
    # Try new bcrypt hash first
    if verify_password(password, user.password_hash):
        return True
    
    # Fall back to old hash (e.g., SHA256)
    if verify_old_hash(password, user.password_hash):
        # Upgrade to bcrypt
        user.password_hash = hash_password(password)
        db.commit()
        return True
    
    return False
```

## API Reference

### `hash_password(password: str) -> str`

Hash a password using bcrypt with cost factor 12.

**Parameters:**
- `password` (str): Plain text password to hash

**Returns:**
- `str`: Hashed password (60 characters)

**Raises:**
- `ValueError`: If password is empty or None

### `verify_password(plain_password: str, hashed_password: str) -> bool`

Verify a plain password against a hashed password.

**Parameters:**
- `plain_password` (str): Plain text password to verify
- `hashed_password` (str): Hashed password to compare against

**Returns:**
- `bool`: True if password matches, False otherwise

### `validate_password_strength(password: str) -> Tuple[bool, str]`

Validate password strength according to security requirements.

**Parameters:**
- `password` (str): Password to validate

**Returns:**
- `Tuple[bool, str]`: (is_valid, error_message)
  - `is_valid`: True if password meets all requirements
  - `error_message`: Empty string if valid, otherwise describes the issue

## Additional Resources

- [OWASP Password Storage Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html)
- [bcrypt Documentation](https://github.com/pyca/bcrypt/)
- [Passlib Documentation](https://passlib.readthedocs.io/)
- [NIST Password Guidelines](https://pages.nist.gov/800-63-3/sp800-63b.html)

## Support

For security concerns or questions:

1. Review this documentation
2. Check the unit tests in `tests/test_security.py`
3. Consult the requirements document (Requirement 12.1)
4. Contact the security team for sensitive issues


---

# JWT Token Management

This section covers JWT (JSON Web Token) authentication implementation, including token generation, validation, and refresh mechanisms.

## Overview

The platform uses JWT tokens for stateless authentication with two token types:
- **Access Token**: Short-lived (15 minutes) for API authentication
- **Refresh Token**: Long-lived (7 days) for obtaining new access tokens

This implementation satisfies Requirements 12.3, 12.4, and 12.9.

## Token Generation

### Access Token Creation

Access tokens are used for authenticating API requests and expire after 15 minutes.

```python
from app.core.security import create_access_token

# Create access token with user data
token = create_access_token({
    "sub": user_id,  # Subject (user ID)
    "role": "employer"  # User role
})
```

**Token Payload:**
```json
{
  "sub": "123e4567-e89b-12d3-a456-426614174000",
  "role": "employer",
  "type": "access",
  "exp": 1234567890
}
```

### Refresh Token Creation

Refresh tokens are used to obtain new access tokens without re-authentication.

```python
from app.core.security import create_refresh_token

# Create refresh token
refresh_token = create_refresh_token({
    "sub": user_id,
    "role": "employer"
})
```

**Token Payload:**
```json
{
  "sub": "123e4567-e89b-12d3-a456-426614174000",
  "role": "employer",
  "type": "refresh",
  "exp": 1234567890
}
```

### Custom Expiration

You can override the default access token expiration:

```python
from datetime import timedelta

# Create token with 30-minute expiration
token = create_access_token(
    {"sub": user_id, "role": "admin"},
    expires_delta=timedelta(minutes=30)
)
```

## Token Validation

### Decoding Tokens

Decode and validate a JWT token:

```python
from app.core.security import decode_token
from jose import JWTError

try:
    payload = decode_token(token)
    user_id = payload["sub"]
    role = payload["role"]
    token_type = payload["type"]
except JWTError as e:
    # Token is invalid, expired, or malformed
    print(f"Token validation failed: {e}")
```

### Token Type Verification

Verify that a token has the expected type:

```python
from app.core.security import verify_token_type

payload = decode_token(token)

# Check if it's an access token
if verify_token_type(payload, "access"):
    # Use for API authentication
    pass

# Check if it's a refresh token
if verify_token_type(payload, "refresh"):
    # Use for token refresh
    pass
```

## FastAPI Dependencies

### Protecting Endpoints

Use FastAPI dependencies to protect routes and enforce authentication:

```python
from fastapi import APIRouter, Depends
from app.api.dependencies import get_current_user_from_token
from app.schemas.auth import TokenData

router = APIRouter()

@router.get("/protected")
async def protected_route(
    current_user: TokenData = Depends(get_current_user_from_token)
):
    return {
        "message": "Access granted",
        "user_id": current_user.user_id,
        "role": current_user.role
    }
```

### Role-Based Access Control

Enforce role-specific access using specialized dependencies:

#### Employer-Only Endpoints

```python
from app.api.dependencies import get_current_employer

@router.post("/jobs")
async def create_job(
    employer: TokenData = Depends(get_current_employer)
):
    # Only employers can access this endpoint
    return {"employer_id": employer.user_id}
```

#### Job Seeker-Only Endpoints

```python
from app.api.dependencies import get_current_job_seeker

@router.post("/applications")
async def apply_to_job(
    job_seeker: TokenData = Depends(get_current_job_seeker)
):
    # Only job seekers can access this endpoint
    return {"job_seeker_id": job_seeker.user_id}
```

#### Admin-Only Endpoints

```python
from app.api.dependencies import get_current_admin

@router.get("/admin/stats")
async def get_system_stats(
    admin: TokenData = Depends(get_current_admin)
):
    # Only admins can access this endpoint
    return {"admin_id": admin.user_id}
```

## Complete Authentication Flow

### User Login

```python
from fastapi import APIRouter, HTTPException, status
from app.core.security import verify_password, create_access_token, create_refresh_token
from app.schemas.auth import Token

router = APIRouter()

@router.post("/auth/login", response_model=Token)
async def login(email: str, password: str):
    # 1. Retrieve user from database
    user = await get_user_by_email(email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    # 2. Verify password
    if not verify_password(password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    # 3. Generate tokens
    access_token = create_access_token({
        "sub": str(user.id),
        "role": user.role
    })
    
    refresh_token = create_refresh_token({
        "sub": str(user.id),
        "role": user.role
    })
    
    # 4. Return tokens
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer"
    )
```

### Token Refresh

```python
from app.api.dependencies import verify_refresh_token
from app.schemas.auth import AccessTokenResponse

@router.post("/auth/refresh", response_model=AccessTokenResponse)
async def refresh_access_token(
    user: TokenData = Depends(verify_refresh_token)
):
    # Generate new access token
    new_access_token = create_access_token({
        "sub": user.user_id,
        "role": user.role
    })
    
    return AccessTokenResponse(
        access_token=new_access_token,
        token_type="bearer"
    )
```

### User Logout

```python
@router.post("/auth/logout")
async def logout(
    current_user: TokenData = Depends(get_current_user_from_token)
):
    # For stateless JWT, logout is handled client-side by discarding tokens
    # Optionally, add refresh token to blacklist in Redis
    await blacklist_refresh_token(current_user.user_id)
    
    return {"message": "Logged out successfully"}
```

## Client-Side Usage

### Storing Tokens

**Recommended Approach:**
- Store access token in memory (JavaScript variable)
- Store refresh token in httpOnly cookie or secure storage

```javascript
// After login
const response = await fetch('/auth/login', {
  method: 'POST',
  body: JSON.stringify({ email, password })
});

const { access_token, refresh_token } = await response.json();

// Store in memory
let accessToken = access_token;

// Store refresh token securely (httpOnly cookie preferred)
localStorage.setItem('refresh_token', refresh_token);
```

### Making Authenticated Requests

```javascript
// Include access token in Authorization header
const response = await fetch('/api/jobs', {
  headers: {
    'Authorization': `Bearer ${accessToken}`
  }
});
```

### Handling Token Expiration

```javascript
async function makeAuthenticatedRequest(url, options = {}) {
  // Try request with current access token
  let response = await fetch(url, {
    ...options,
    headers: {
      ...options.headers,
      'Authorization': `Bearer ${accessToken}`
    }
  });
  
  // If token expired, refresh and retry
  if (response.status === 401) {
    const refreshToken = localStorage.getItem('refresh_token');
    
    // Get new access token
    const refreshResponse = await fetch('/auth/refresh', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${refreshToken}`
      }
    });
    
    if (refreshResponse.ok) {
      const { access_token } = await refreshResponse.json();
      accessToken = access_token;
      
      // Retry original request
      response = await fetch(url, {
        ...options,
        headers: {
          ...options.headers,
          'Authorization': `Bearer ${accessToken}`
        }
      });
    } else {
      // Refresh failed, redirect to login
      window.location.href = '/login';
    }
  }
  
  return response;
}
```

## Security Best Practices

### Token Security

✅ **Use HTTPS Only**: Never transmit tokens over HTTP
✅ **Short Access Token Expiration**: 15 minutes limits exposure window
✅ **Secure Refresh Token Storage**: Use httpOnly cookies when possible
✅ **Validate Token Type**: Always check token type before use
✅ **Include User Role**: Embed role in token for authorization
✅ **Use Strong Secret Key**: Generate cryptographically secure JWT_SECRET_KEY

### Token Management

✅ **Implement Token Refresh**: Allow seamless re-authentication
✅ **Blacklist on Logout**: Invalidate refresh tokens on logout
✅ **Rotate Refresh Tokens**: Issue new refresh token on each refresh
✅ **Monitor Token Usage**: Log authentication events
✅ **Rate Limit Auth Endpoints**: Prevent brute-force attacks

### Common Vulnerabilities

❌ **Never store tokens in localStorage for sensitive apps**: XSS vulnerable
❌ **Never include sensitive data in tokens**: Tokens are not encrypted
❌ **Never use weak secret keys**: Use at least 256-bit random key
❌ **Never skip token expiration validation**: Always check exp claim
❌ **Never trust client-provided tokens**: Always validate signature

## Configuration

### Environment Variables

Configure JWT settings in `.env`:

```bash
# JWT Configuration
JWT_SECRET_KEY=your-secret-key-here-min-32-chars
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7
```

### Generating Secret Key

Generate a secure secret key:

```bash
# Using OpenSSL
openssl rand -hex 32

# Using Python
python -c "import secrets; print(secrets.token_hex(32))"
```

## Error Handling

### Common JWT Errors

#### Invalid Token Signature

```python
try:
    payload = decode_token(token)
except JWTError:
    raise HTTPException(
        status_code=401,
        detail="Invalid token signature"
    )
```

#### Expired Token

```python
try:
    payload = decode_token(token)
except JWTError as e:
    if "expired" in str(e).lower():
        raise HTTPException(
            status_code=401,
            detail="Token has expired"
        )
```

#### Wrong Token Type

```python
payload = decode_token(token)
if not verify_token_type(payload, "access"):
    raise HTTPException(
        status_code=401,
        detail="Invalid token type. Access token required."
    )
```

## Testing JWT Implementation

### Unit Tests

Run JWT-specific tests:

```bash
# Run JWT tests
pytest tests/test_jwt.py -v

# Run with coverage
pytest tests/test_jwt.py --cov=app.core.security --cov-report=term
```

### Test Coverage

- ✅ Access token generation with 15-minute expiration
- ✅ Refresh token generation with 7-day expiration
- ✅ Token decoding and validation
- ✅ Token type verification
- ✅ Custom expiration times
- ✅ Invalid token handling
- ✅ Expired token handling
- ✅ Malformed token handling
- ✅ Token signature validation

### Integration Tests

Test complete authentication flow:

```python
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_login_and_access_protected_route(client: AsyncClient):
    # 1. Login
    response = await client.post("/auth/login", json={
        "email": "test@example.com",
        "password": "SecurePass123!"
    })
    assert response.status_code == 200
    
    tokens = response.json()
    access_token = tokens["access_token"]
    
    # 2. Access protected route
    response = await client.get(
        "/api/jobs",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_token_refresh(client: AsyncClient):
    # 1. Login
    login_response = await client.post("/auth/login", json={
        "email": "test@example.com",
        "password": "SecurePass123!"
    })
    refresh_token = login_response.json()["refresh_token"]
    
    # 2. Refresh access token
    response = await client.post(
        "/auth/refresh",
        headers={"Authorization": f"Bearer {refresh_token}"}
    )
    assert response.status_code == 200
    assert "access_token" in response.json()
```

## Monitoring and Logging

### Authentication Events

Log important authentication events:

```python
import logging

logger = logging.getLogger(__name__)

# Successful login
logger.info(f"User {user_id} logged in successfully", extra={
    "user_id": user_id,
    "role": role,
    "ip_address": request.client.host
})

# Failed login attempt
logger.warning(f"Failed login attempt for {email}", extra={
    "email": email,
    "ip_address": request.client.host
})

# Token refresh
logger.info(f"Token refreshed for user {user_id}", extra={
    "user_id": user_id
})
```

### Security Metrics

Track authentication metrics:
- Login success/failure rate
- Token refresh frequency
- Average token lifetime
- Failed authentication attempts per IP
- Unusual authentication patterns

## Troubleshooting

### Issue: "Could not validate credentials"

**Cause**: Invalid or expired token

**Solution**: Check token format and expiration

```python
# Debug token
try:
    payload = decode_token(token)
    print(f"Token valid until: {datetime.fromtimestamp(payload['exp'])}")
except JWTError as e:
    print(f"Token error: {e}")
```

### Issue: "Invalid token type"

**Cause**: Using refresh token for API access or vice versa

**Solution**: Use correct token type for each operation

```python
# Check token type
payload = decode_token(token)
print(f"Token type: {payload.get('type')}")
```

### Issue: Token works locally but fails in production

**Cause**: Different JWT_SECRET_KEY in environments

**Solution**: Ensure consistent secret key across environments

```bash
# Verify secret key is set
echo $JWT_SECRET_KEY
```

## API Reference

### `create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str`

Create a JWT access token with specified expiration.

**Parameters:**
- `data` (dict): Claims to encode (must include "sub" for user ID)
- `expires_delta` (Optional[timedelta]): Custom expiration time

**Returns:**
- `str`: Encoded JWT token

### `create_refresh_token(data: dict) -> str`

Create a JWT refresh token with 7-day expiration.

**Parameters:**
- `data` (dict): Claims to encode (must include "sub" for user ID)

**Returns:**
- `str`: Encoded JWT refresh token

### `decode_token(token: str) -> Dict[str, Any]`

Decode and validate a JWT token.

**Parameters:**
- `token` (str): JWT token to decode

**Returns:**
- `Dict[str, Any]`: Decoded token payload

**Raises:**
- `JWTError`: If token is invalid, expired, or malformed

### `verify_token_type(payload: Dict[str, Any], expected_type: str) -> bool`

Verify that a decoded token has the expected type.

**Parameters:**
- `payload` (Dict): Decoded token payload
- `expected_type` (str): Expected type ("access" or "refresh")

**Returns:**
- `bool`: True if type matches, False otherwise

## Additional Resources

- [JWT.io](https://jwt.io/) - JWT debugger and documentation
- [RFC 7519](https://tools.ietf.org/html/rfc7519) - JWT specification
- [OWASP JWT Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/JSON_Web_Token_for_Java_Cheat_Sheet.html)
- [python-jose Documentation](https://python-jose.readthedocs.io/)

