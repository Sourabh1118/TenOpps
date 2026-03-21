# JWT Quick Reference Guide

## Quick Start

### 1. Generate Tokens (Login)

```python
from app.core.security import create_access_token, create_refresh_token

# After successful authentication
access_token = create_access_token({
    "sub": str(user.id),
    "role": user.role
})

refresh_token = create_refresh_token({
    "sub": str(user.id),
    "role": user.role
})

return {
    "access_token": access_token,
    "refresh_token": refresh_token,
    "token_type": "bearer"
}
```

### 2. Protect Endpoints

```python
from fastapi import Depends
from app.api.dependencies import get_current_user_from_token

@router.get("/protected")
async def protected_route(
    current_user: TokenData = Depends(get_current_user_from_token)
):
    return {"user_id": current_user.user_id}
```

### 3. Role-Based Protection

```python
from app.api.dependencies import get_current_employer, get_current_job_seeker

# Employer only
@router.post("/jobs")
async def create_job(employer: TokenData = Depends(get_current_employer)):
    pass

# Job seeker only
@router.post("/applications")
async def apply(job_seeker: TokenData = Depends(get_current_job_seeker)):
    pass
```

### 4. Refresh Token

```python
# Endpoint already implemented at POST /auth/refresh
# Client usage:
POST /auth/refresh
Authorization: Bearer <refresh_token>

# Returns new access token
```

## Token Specifications

| Token Type | Expiration | Use Case |
|------------|------------|----------|
| Access Token | 15 minutes | API authentication |
| Refresh Token | 7 days | Get new access token |

## Common Patterns

### Login Flow
```python
@router.post("/auth/login")
async def login(email: str, password: str):
    user = await authenticate_user(email, password)
    
    access_token = create_access_token({
        "sub": str(user.id),
        "role": user.role
    })
    
    refresh_token = create_refresh_token({
        "sub": str(user.id),
        "role": user.role
    })
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer"
    )
```

### Protected Route
```python
@router.get("/me")
async def get_current_user(
    current_user: TokenData = Depends(get_current_user_from_token)
):
    user = await get_user_by_id(current_user.user_id)
    return user
```

### Role Check
```python
@router.post("/jobs")
async def create_job(
    job_data: JobCreate,
    employer: TokenData = Depends(get_current_employer)
):
    job = await create_job_for_employer(employer.user_id, job_data)
    return job
```

## Client-Side Usage

### Store Tokens
```javascript
// After login
const { access_token, refresh_token } = await response.json();
let accessToken = access_token;  // In memory
localStorage.setItem('refresh_token', refresh_token);
```

### Make Request
```javascript
const response = await fetch('/api/jobs', {
  headers: {
    'Authorization': `Bearer ${accessToken}`
  }
});
```

### Handle Expiration
```javascript
if (response.status === 401) {
  // Refresh token
  const refreshResponse = await fetch('/auth/refresh', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${localStorage.getItem('refresh_token')}`
    }
  });
  
  const { access_token } = await refreshResponse.json();
  accessToken = access_token;
  
  // Retry original request
}
```

## Error Handling

### Invalid Token
```python
from jose import JWTError

try:
    payload = decode_token(token)
except JWTError:
    raise HTTPException(status_code=401, detail="Invalid token")
```

### Wrong Token Type
```python
if not verify_token_type(payload, "access"):
    raise HTTPException(
        status_code=401,
        detail="Invalid token type. Access token required."
    )
```

### Expired Token
```python
# Automatically handled by decode_token()
# Raises JWTError with expiration message
```

## Configuration

### .env File
```bash
JWT_SECRET_KEY=your-secret-key-min-32-chars
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7
```

### Generate Secret
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

## Testing

### Run Tests
```bash
pytest tests/test_jwt.py -v
```

### Manual Test
```python
from app.core.security import create_access_token, decode_token

token = create_access_token({"sub": "test123", "role": "employer"})
payload = decode_token(token)
print(payload)
```

## Available Dependencies

| Dependency | Purpose | Returns |
|------------|---------|---------|
| `get_current_user_from_token` | Validate access token | TokenData |
| `get_current_employer` | Require employer role | TokenData |
| `get_current_job_seeker` | Require job_seeker role | TokenData |
| `get_current_admin` | Require admin role | TokenData |
| `verify_refresh_token` | Validate refresh token | TokenData |

## Token Payload Structure

### Access Token
```json
{
  "sub": "user-id",
  "role": "employer",
  "type": "access",
  "exp": 1234567890
}
```

### Refresh Token
```json
{
  "sub": "user-id",
  "role": "employer",
  "type": "refresh",
  "exp": 1234567890
}
```

## Security Checklist

- ✅ Use HTTPS only
- ✅ Store refresh token securely (httpOnly cookie preferred)
- ✅ Keep access token in memory
- ✅ Validate token type before use
- ✅ Handle token expiration gracefully
- ✅ Use strong secret key (32+ characters)
- ✅ Never log tokens
- ✅ Implement rate limiting on auth endpoints

## Troubleshooting

### "Could not validate credentials"
- Check token format (Bearer <token>)
- Verify token hasn't expired
- Ensure correct JWT_SECRET_KEY

### "Invalid token type"
- Using refresh token for API access
- Using access token for refresh endpoint
- Check token type in payload

### Token works locally but not in production
- Different JWT_SECRET_KEY in environments
- Verify environment variables are set

## Resources

- Full Documentation: `backend/docs/SECURITY_GUIDE.md`
- Usage Examples: `backend/examples/jwt_usage_example.py`
- Unit Tests: `backend/tests/test_jwt.py`
- Task Completion: `backend/TASK_3.2_COMPLETION.md`
