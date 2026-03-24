"""
Password hashing and validation utilities for the job aggregation platform.

This module provides secure password hashing using bcrypt with cost factor 12,
password verification, password strength validation, and JWT token management.
"""
import re
from datetime import datetime, timedelta
from typing import Optional, Tuple, Dict, Any
from passlib.context import CryptContext
from jose import JWTError, jwt
from app.core.config import settings


# Configure bcrypt with cost factor 12 as per requirement 12.1
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt with cost factor 12.
    
    Args:
        password: Plain text password to hash
        
    Returns:
        Hashed password string
        
    Raises:
        ValueError: If password is empty or None
        
    Example:
        >>> hashed = hash_password("MySecurePass123!")
        >>> len(hashed) > 0
        True
    """
    if not password:
        raise ValueError("Password cannot be empty")
    
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against a hashed password.
    
    Args:
        plain_password: Plain text password to verify
        hashed_password: Hashed password to compare against
        
    Returns:
        True if password matches, False otherwise
        
    Example:
        >>> hashed = hash_password("MySecurePass123!")
        >>> verify_password("MySecurePass123!", hashed)
        True
        >>> verify_password("WrongPassword", hashed)
        False
    """
    if not plain_password or not hashed_password:
        return False
    
    try:
        # Use bcrypt directly to avoid passlib compatibility issues with bcrypt 5.0+
        import bcrypt
        password_bytes = plain_password.encode('utf-8')
        hash_bytes = hashed_password.encode('utf-8')
        return bcrypt.checkpw(password_bytes, hash_bytes)
    except Exception:
        # Handle any verification errors (malformed hash, etc.)
        return False


def validate_password_strength(password: str) -> Tuple[bool, str]:
    """
    Validate password strength according to security requirements.
    
    Password must meet the following criteria:
    - Minimum 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    - At least one special character
    
    Args:
        password: Password to validate
        
    Returns:
        Tuple of (is_valid, error_message)
        - is_valid: True if password meets all requirements
        - error_message: Empty string if valid, otherwise describes the issue
        
    Example:
        >>> validate_password_strength("MySecurePass123!")
        (True, '')
        >>> validate_password_strength("weak")
        (False, 'Password must be at least 8 characters long')
    """
    if not password:
        return False, "Password cannot be empty"
    
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter"
    
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter"
    
    if not re.search(r"\d", password):
        return False, "Password must contain at least one digit"
    
    # Special characters: any non-alphanumeric character
    if not re.search(r"[^A-Za-z0-9]", password):
        return False, "Password must contain at least one special character"
    
    return True, ""


# JWT Token Management

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token with specified expiration.
    
    Args:
        data: Dictionary containing claims to encode in the token (e.g., user_id, role)
        expires_delta: Optional custom expiration time. Defaults to 15 minutes.
        
    Returns:
        Encoded JWT token string
        
    Example:
        >>> token = create_access_token({"sub": "user123", "role": "employer"})
        >>> len(token) > 0
        True
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "type": "access"})
    
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.JWT_SECRET_KEY, 
        algorithm=settings.JWT_ALGORITHM
    )
    
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """
    Create a JWT refresh token with 7-day expiration.
    
    Args:
        data: Dictionary containing claims to encode in the token (e.g., user_id)
        
    Returns:
        Encoded JWT refresh token string
        
    Example:
        >>> token = create_refresh_token({"sub": "user123"})
        >>> len(token) > 0
        True
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
    
    to_encode.update({"exp": expire, "type": "refresh"})
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    
    return encoded_jwt


def decode_token(token: str) -> Dict[str, Any]:
    """
    Decode and validate a JWT token.
    
    Args:
        token: JWT token string to decode
        
    Returns:
        Dictionary containing the decoded token payload
        
    Raises:
        JWTError: If token is invalid, expired, or malformed
        
    Example:
        >>> token = create_access_token({"sub": "user123", "role": "employer"})
        >>> payload = decode_token(token)
        >>> payload["sub"]
        'user123'
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except JWTError as e:
        raise JWTError(f"Token validation failed: {str(e)}")


def verify_token_type(payload: Dict[str, Any], expected_type: str) -> bool:
    """
    Verify that a decoded token has the expected type.
    
    Args:
        payload: Decoded token payload
        expected_type: Expected token type ("access" or "refresh")
        
    Returns:
        True if token type matches, False otherwise
        
    Example:
        >>> token = create_access_token({"sub": "user123"})
        >>> payload = decode_token(token)
        >>> verify_token_type(payload, "access")
        True
        >>> verify_token_type(payload, "refresh")
        False
    """
    return payload.get("type") == expected_type



# Rate Limiting for Login Attempts

def check_rate_limit(redis_client, ip_address: str, max_attempts: int = 5, window_seconds: int = 900) -> Tuple[bool, Optional[int]]:
    """
    Check if an IP address has exceeded the rate limit for login attempts.
    
    Uses Redis to track login attempts per IP address with a sliding window.
    
    Args:
        redis_client: Redis client instance
        ip_address: IP address to check
        max_attempts: Maximum number of attempts allowed (default: 5)
        window_seconds: Time window in seconds (default: 900 = 15 minutes)
        
    Returns:
        Tuple of (is_allowed, retry_after_seconds)
        - is_allowed: True if request is allowed, False if rate limit exceeded
        - retry_after_seconds: Seconds until rate limit resets (None if allowed)
        
    Example:
        >>> is_allowed, retry_after = check_rate_limit(redis_client, "192.168.1.1")
        >>> if not is_allowed:
        ...     raise HTTPException(status_code=429, headers={"Retry-After": str(retry_after)})
    """
    key = f"rate_limit:login:{ip_address}"
    
    try:
        # Get current attempt count
        current_count = redis_client.get(key)
        
        if current_count is None:
            # First attempt, set counter with expiration
            redis_client.setex(key, window_seconds, 1)
            return True, None
        
        current_count = int(current_count)
        
        if current_count >= max_attempts:
            # Rate limit exceeded, get TTL for retry-after
            ttl = redis_client.ttl(key)
            return False, ttl if ttl > 0 else window_seconds
        
        # Increment counter
        redis_client.incr(key)
        return True, None
        
    except Exception as e:
        # If Redis fails, allow the request (fail open)
        # Log the error for monitoring
        print(f"Rate limit check failed: {e}")
        return True, None


def increment_rate_limit(redis_client, ip_address: str, window_seconds: int = 900) -> None:
    """
    Increment the rate limit counter for an IP address.
    
    This should be called after a failed login attempt.
    
    Args:
        redis_client: Redis client instance
        ip_address: IP address to increment
        window_seconds: Time window in seconds (default: 900 = 15 minutes)
        
    Example:
        >>> increment_rate_limit(redis_client, "192.168.1.1")
    """
    key = f"rate_limit:login:{ip_address}"
    
    try:
        current = redis_client.get(key)
        if current is None:
            redis_client.setex(key, window_seconds, 1)
        else:
            redis_client.incr(key)
    except Exception as e:
        # Log error but don't fail the request
        print(f"Rate limit increment failed: {e}")


def add_token_to_blacklist(redis_client, token: str, expiration_seconds: int) -> bool:
    """
    Add a refresh token to the blacklist in Redis.
    
    Blacklisted tokens are stored with an expiration matching the token's expiry time.
    
    Args:
        redis_client: Redis client instance
        token: Refresh token to blacklist
        expiration_seconds: Seconds until token expires naturally
        
    Returns:
        True if successful, False otherwise
        
    Example:
        >>> add_token_to_blacklist(redis_client, "token123", 604800)  # 7 days
        True
    """
    key = f"blacklist:token:{token}"
    
    try:
        redis_client.setex(key, expiration_seconds, "1")
        return True
    except Exception as e:
        print(f"Token blacklist failed: {e}")
        return False


def is_token_blacklisted(redis_client, token: str) -> bool:
    """
    Check if a refresh token is blacklisted.
    
    Args:
        redis_client: Redis client instance
        token: Refresh token to check
        
    Returns:
        True if token is blacklisted, False otherwise
        
    Example:
        >>> if is_token_blacklisted(redis_client, "token123"):
        ...     raise HTTPException(status_code=401, detail="Token has been revoked")
    """
    key = f"blacklist:token:{token}"
    
    try:
        return redis_client.exists(key) > 0
    except Exception as e:
        # If Redis fails, deny access (fail closed for security)
        print(f"Token blacklist check failed: {e}")
        return True
