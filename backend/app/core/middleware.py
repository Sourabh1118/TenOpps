"""
Security middleware for FastAPI application.

This module provides middleware for:
- HTTPS enforcement
- Security headers (HSTS, X-Content-Type-Options, X-Frame-Options)
- CSRF protection
- API response time tracking

Implements Requirements 13.4, 13.5, 19.2
"""
import secrets
import time
from typing import Callable, Optional
from uuid import UUID
from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.core.config import settings
from app.core.redis import redis_client
from app.core.logging import logger


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add security headers to all responses.
    
    Implements Requirement 13.4:
    - Adds HSTS header to enforce HTTPS
    - Adds X-Content-Type-Options to prevent MIME sniffing
    - Adds X-Frame-Options to prevent clickjacking
    - Adds X-XSS-Protection for older browsers
    - Adds Content-Security-Policy for XSS protection
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Add security headers to response."""
        response = await call_next(request)
        
        # HSTS: Enforce HTTPS for 1 year (only in production)
        if settings.APP_ENV == "production":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"
        
        # XSS protection for older browsers
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # Content Security Policy
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self'; "
            "connect-src 'self'; "
            "frame-ancestors 'none';"
        )
        
        # Referrer policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Permissions policy
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        
        return response


class HTTPSRedirectMiddleware(BaseHTTPMiddleware):
    """
    Middleware to enforce HTTPS in production.
    
    Implements Requirement 13.4:
    - Redirects HTTP requests to HTTPS in production
    - Allows HTTP in development for local testing
    - Respects X-Forwarded-Proto header from reverse proxies (Nginx)
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Redirect HTTP to HTTPS in production."""
        # Only enforce HTTPS in production
        if settings.APP_ENV == "production":
            # When behind a reverse proxy (Nginx), check X-Forwarded-Proto
            # instead of request.url.scheme, because the proxy connects
            # to the backend over plain HTTP on localhost.
            forwarded_proto = request.headers.get("x-forwarded-proto", request.url.scheme)
            
            if forwarded_proto == "http":
                # Build HTTPS URL
                https_url = request.url.replace(scheme="https")
                return JSONResponse(
                    status_code=status.HTTP_301_MOVED_PERMANENTLY,
                    content={"detail": "Please use HTTPS"},
                    headers={"Location": str(https_url)}
                )
        
        return await call_next(request)


class CSRFProtectionMiddleware(BaseHTTPMiddleware):
    """
    Middleware to provide CSRF protection for state-changing operations.
    
    Implements Requirement 13.5:
    - Generates CSRF tokens for sessions
    - Validates CSRF tokens on POST, PUT, PATCH, DELETE requests
    - Stores tokens in Redis with session ID
    
    Note: This is a simplified CSRF implementation. For production,
    consider using a more robust solution like fastapi-csrf-protect.
    """
    
    # Methods that require CSRF protection
    PROTECTED_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
    
    # Paths that don't require CSRF protection (authentication endpoints)
    EXEMPT_PATHS = {
        "/api/auth/login",
        "/api/auth/register/employer",
        "/api/auth/register/job-seeker",
        "/api/auth/refresh",
        "/health",
        "/",
        "/docs",
        "/openapi.json",
    }
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Validate CSRF token for state-changing requests."""
        # Skip CSRF check for exempt paths
        if request.url.path in self.EXEMPT_PATHS:
            return await call_next(request)
        
        # Skip CSRF check for safe methods
        if request.method not in self.PROTECTED_METHODS:
            return await call_next(request)
        
        # Skip CSRF check in development (for easier testing)
        if settings.APP_ENV == "development" and settings.DEBUG:
            return await call_next(request)
        
        # Skip CSRF check for Bearer token auth (JWT is inherently CSRF-safe —
        # browsers cannot auto-send Authorization headers cross-origin)
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            return await call_next(request)
        
        # Get CSRF token from header (for cookie-based sessions only)
        csrf_token = request.headers.get("X-CSRF-Token")
        
        if not csrf_token:
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"detail": "CSRF token missing"}
            )

        
        # Get session ID from Authorization header (JWT token)
        auth_header = request.headers.get("Authorization")
        
        if not auth_header or not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Authentication required for CSRF validation"}
            )
        
        # Extract token from header
        token = auth_header.split(" ")[1]
        
        # Validate CSRF token
        is_valid = await self._validate_csrf_token(token, csrf_token)
        
        if not is_valid:
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"detail": "Invalid CSRF token"}
            )
        
        return await call_next(request)
    
    async def _validate_csrf_token(self, session_token: str, csrf_token: str) -> bool:
        """
        Validate CSRF token against stored token in Redis.
        
        Args:
            session_token: JWT token from Authorization header
            csrf_token: CSRF token from X-CSRF-Token header
            
        Returns:
            True if token is valid, False otherwise
        """
        try:
            redis = redis_client.get_cache_client()
            
            # Get stored CSRF token from Redis
            cache_key = f"csrf:{session_token[:32]}"  # Use first 32 chars of JWT as key
            stored_token = redis.get(cache_key)
            
            if not stored_token:
                return False
            
            # Compare tokens (constant-time comparison)
            return secrets.compare_digest(stored_token.decode(), csrf_token)
            
        except Exception:
            return False


def generate_csrf_token(session_token: str) -> str:
    """
    Generate a CSRF token for a session.
    
    Implements Requirement 13.5:
    - Generates cryptographically secure CSRF token
    - Stores token in Redis with session ID
    - Token expires after 1 hour
    
    Args:
        session_token: JWT token from Authorization header
        
    Returns:
        Generated CSRF token
        
    Example:
        >>> token = generate_csrf_token("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...")
        >>> len(token)
        64
    """
    # Generate random token
    csrf_token = secrets.token_urlsafe(32)
    
    try:
        redis = redis_client.get_cache_client()
        
        # Store token in Redis with 1 hour expiration
        cache_key = f"csrf:{session_token[:32]}"
        redis.setex(cache_key, 3600, csrf_token)
        
    except Exception:
        # If Redis fails, still return token (will fail validation later)
        pass
    
    return csrf_token


def validate_csrf_token_sync(session_token: str, csrf_token: str) -> bool:
    """
    Synchronous version of CSRF token validation.
    
    Args:
        session_token: JWT token from Authorization header
        csrf_token: CSRF token to validate
        
    Returns:
        True if token is valid, False otherwise
    """
    try:
        redis = redis_client.get_cache_client()
        
        # Get stored CSRF token from Redis
        cache_key = f"csrf:{session_token[:32]}"
        stored_token = redis.get(cache_key)
        
        if not stored_token:
            return False
        
        # Compare tokens (constant-time comparison)
        return secrets.compare_digest(stored_token.decode(), csrf_token)
        
    except Exception:
        return False



class ResponseTimeMiddleware(BaseHTTPMiddleware):
    """
    Middleware to track API response times.
    
    Implements Requirement 19.2:
    - Track response times for all API requests
    - Log slow requests (>1 second)
    - Store metrics in database
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Track response time for request."""
        # Skip tracking for health check and static endpoints
        if request.url.path in ["/health", "/", "/docs", "/openapi.json"]:
            return await call_next(request)
        
        # Record start time
        start_time = time.time()
        
        # Process request
        response = await call_next(request)
        
        # Calculate response time
        response_time_ms = (time.time() - start_time) * 1000
        
        # Add response time header
        response.headers["X-Response-Time"] = f"{response_time_ms:.2f}ms"
        
        # Track metrics asynchronously (don't block response)
        try:
            # Extract user info if available
            user_id = None
            user_role = None
            auth_header = request.headers.get("authorization", "")
            
            if auth_header.startswith("Bearer "):
                try:
                    from app.core.security import decode_token
                    token = auth_header.split(" ")[1]
                    payload = decode_token(token)
                    user_id = payload.get("sub")
                    user_role = payload.get("role")
                except Exception:
                    pass
            
            # Store in Redis for immediate access (don't wait for DB)
            redis = redis_client.get_cache_client()
            
            # Track slow requests
            if response_time_ms > 1000:
                logger.warning(
                    f"Slow API request",
                    extra={
                        "endpoint": request.url.path,
                        "method": request.method,
                        "response_time_ms": response_time_ms,
                        "status_code": response.status_code,
                    }
                )
                # Add to slow requests list
                redis.lpush(
                    "api:slow_requests",
                    f"{request.method} {request.url.path} - {response_time_ms:.2f}ms"
                )
                redis.ltrim("api:slow_requests", 0, 99)  # Keep last 100
                redis.expire("api:slow_requests", 86400)  # 24 hours
            
            # Store recent response times for endpoint
            key = f"api_metrics:recent:{request.url.path}:{request.method}"
            redis.lpush(key, response_time_ms)
            redis.ltrim(key, 0, 99)  # Keep last 100 measurements
            redis.expire(key, 3600)  # 1 hour TTL
            
            # Queue database write (async task)
            # This will be picked up by a background task
            from app.tasks.monitoring_tasks import track_api_metric_task
            track_api_metric_task.delay(
                endpoint=request.url.path,
                method=request.method,
                status_code=response.status_code,
                response_time_ms=response_time_ms,
                user_id=str(user_id) if user_id else None,
                user_role=user_role,
            )
            
        except Exception as e:
            # Don't let tracking errors break the response
            logger.error(f"Error tracking response time: {e}")
        
        return response
