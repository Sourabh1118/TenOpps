"""
Main FastAPI application entry point.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
import sentry_sdk
from typing import Optional, Dict, Any

from app.core.config import settings
from app.core.logging import setup_logging, get_logger, sanitize_log_data
from app.core.middleware import (
    SecurityHeadersMiddleware,
    HTTPSRedirectMiddleware,
    CSRFProtectionMiddleware,
)
from app.core.rate_limiting import RateLimitMiddleware
from app.core.error_handlers import register_error_handlers
from app.db import check_db_health, get_db_info


# Initialize logging
setup_logging()
logger = get_logger(__name__)


def before_send_sentry(event: Dict[str, Any], hint: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Process Sentry events before sending to add context.
    
    Implements Requirement 19.1:
    - Add context (user ID, request data) to error reports
    - Sanitize sensitive data before sending
    
    Args:
        event: Sentry event dictionary
        hint: Additional context hints
        
    Returns:
        Modified event or None to drop the event
    """
    # Sanitize request data to remove sensitive information
    if 'request' in event:
        request_data = event['request']
        
        # Sanitize headers
        if 'headers' in request_data:
            request_data['headers'] = sanitize_log_data(request_data['headers'])
        
        # Sanitize cookies
        if 'cookies' in request_data:
            request_data['cookies'] = sanitize_log_data(request_data['cookies'])
        
        # Sanitize query string
        if 'query_string' in request_data:
            request_data['query_string'] = sanitize_log_data(request_data.get('query_string', {}))
        
        # Sanitize POST data
        if 'data' in request_data:
            request_data['data'] = sanitize_log_data(request_data['data'])
    
    # Add user context if available (without PII)
    if 'user' in event:
        user_data = event['user']
        # Keep only non-sensitive user info
        safe_user = {
            'id': user_data.get('id'),
            'role': user_data.get('role'),
        }
        event['user'] = safe_user
    
    return event


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info("Starting application", extra={"version": "0.1.0"})
    
    # Check database connection
    if check_db_health():
        logger.info("Database connection established")
        db_info = get_db_info()
        logger.info("Database pool info", extra=db_info)
    else:
        logger.error("Database connection failed")
    
    # Initialize Sentry if DSN is configured (Requirement 19.1)
    if settings.SENTRY_DSN:
        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            environment=settings.APP_ENV,
            traces_sample_rate=1.0 if settings.APP_ENV == "development" else 0.1,
            # Send all unhandled exceptions to Sentry (Requirement 19.1)
            send_default_pii=False,  # Don't send PII by default
            before_send=before_send_sentry,  # Add context to error reports
        )
        logger.info("Sentry monitoring initialized")
    
    yield
    
    # Shutdown
    logger.info("Shutting down application")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    description="A hybrid job marketplace platform combining automated job aggregation with direct employer posting",
    version="0.1.0",
    debug=settings.DEBUG,
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add gzip compression for API responses (Requirement 16.4)
# Compress responses larger than 1KB (1000 bytes)
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Add security middleware
# Note: Order matters - add in reverse order of execution
app.add_middleware(CSRFProtectionMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(HTTPSRedirectMiddleware)

# Register error handlers
register_error_handlers(app)


# Middleware to add user context to Sentry (Requirement 19.1)
@app.middleware("http")
async def add_sentry_context(request: Request, call_next):
    """
    Add user and request context to Sentry error reports.
    
    Implements Requirement 19.1:
    - Add context (user ID, request data) to error reports
    """
    # Extract user info from JWT token if present
    auth_header = request.headers.get("authorization", "")
    if auth_header.startswith("Bearer "):
        try:
            from app.api.dependencies import decode_access_token
            token = auth_header.split(" ")[1]
            payload = decode_access_token(token)
            
            # Set user context in Sentry
            if settings.SENTRY_DSN:
                sentry_sdk.set_user({
                    "id": payload.get("sub"),
                    "role": payload.get("role"),
                })
        except Exception:
            # Ignore token decode errors in middleware
            pass
    
    # Add request context
    if settings.SENTRY_DSN:
        sentry_sdk.set_context("request", {
            "method": request.method,
            "url": str(request.url),
            "path": request.url.path,
        })
    
    response = await call_next(request)
    return response


@app.get("/")
async def root():
    """Root endpoint - health check."""
    return {
        "name": settings.APP_NAME,
        "version": "0.1.0",
        "status": "running",
        "environment": settings.APP_ENV
    }


@app.get("/health")
async def health_check():
    """
    Health check endpoint with database and Redis status.
    
    Implements Requirement 19.7: Health check endpoints for monitoring.
    
    Returns:
        - 200 if all services are healthy
        - 503 if any critical service is unhealthy
    """
    from datetime import datetime
    from fastapi import status
    from fastapi.responses import JSONResponse
    
    # Check database connectivity
    db_healthy = check_db_health()
    db_info = get_db_info() if db_healthy else {}
    
    # Check Redis connectivity
    redis_healthy = False
    redis_info = {}
    try:
        from app.core.redis import get_redis_client
        redis_client = get_redis_client()
        redis_client.ping()
        redis_healthy = True
        redis_info = {
            "connected": True,
            "ping": "ok"
        }
    except Exception as e:
        logger.error(f"Redis health check failed: {str(e)}")
        redis_info = {
            "connected": False,
            "error": "Connection failed"
        }
    
    # Determine overall health status
    all_healthy = db_healthy and redis_healthy
    health_status = "healthy" if all_healthy else "unhealthy"
    status_code = status.HTTP_200_OK if all_healthy else status.HTTP_503_SERVICE_UNAVAILABLE
    
    response_data = {
        "status": health_status,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "services": {
            "database": {
                "status": "healthy" if db_healthy else "unhealthy",
                "connected": db_healthy,
                **db_info
            },
            "redis": {
                "status": "healthy" if redis_healthy else "unhealthy",
                **redis_info
            }
        }
    }
    
    return JSONResponse(
        status_code=status_code,
        content=response_data
    )


@app.get("/api/csrf-token")
async def get_csrf_token(authorization: str = None):
    """
    Get CSRF token for authenticated session.
    
    This endpoint generates a CSRF token that must be included in
    X-CSRF-Token header for all state-changing requests (POST, PUT, PATCH, DELETE).
    
    Implements Requirement 13.5: Generate CSRF tokens for state-changing operations.
    
    Returns:
        CSRF token and instructions for use
    """
    from fastapi import Header
    from app.core.middleware import generate_csrf_token
    
    if not authorization or not authorization.startswith("Bearer "):
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required to generate CSRF token"
        )
    
    # Extract token
    session_token = authorization.split(" ")[1]
    
    # Generate CSRF token
    csrf_token = generate_csrf_token(session_token)
    
    return {
        "csrf_token": csrf_token,
        "expires_in": 3600,  # 1 hour
        "usage": "Include this token in X-CSRF-Token header for POST, PUT, PATCH, DELETE requests"
    }


# Register API routers
from app.api.auth import router as auth_router
from app.api.subscription import router as subscription_router
from app.api.url_import import router as url_import_router
from app.api.applications import router as applications_router
from app.api.admin import router as admin_router
from app.api.analytics import router as analytics_router
from app.api.stripe_payment import router as stripe_router
from app.api.privacy import router as privacy_router

app.include_router(auth_router, prefix="/api")
app.include_router(subscription_router, prefix="/api")
app.include_router(url_import_router, prefix="/api")
app.include_router(jobs_router, prefix="/api")
app.include_router(applications_router, prefix="/api")
app.include_router(admin_router, prefix="/api")
app.include_router(analytics_router, prefix="/api")
app.include_router(stripe_router, prefix="/api")
app.include_router(privacy_router, prefix="/api")


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.API_RELOAD,
        log_level=settings.LOG_LEVEL.lower(),
    )
