"""
FastAPI dependencies for authentication and authorization.

This module provides dependency functions for validating JWT tokens and
enforcing role-based access control.
"""
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError
from app.core.security import decode_token, verify_token_type
from app.schemas.auth import TokenData


# HTTP Bearer token security scheme
security = HTTPBearer()


async def get_current_user_from_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> TokenData:
    """
    Validate JWT access token and extract user information.
    
    This dependency validates the JWT token from the Authorization header,
    checks that it's an access token (not refresh), and extracts user data.
    
    Args:
        credentials: HTTP Bearer credentials from Authorization header
        
    Returns:
        TokenData containing user_id, role, and token_type
        
    Raises:
        HTTPException: 401 if token is invalid, expired, or not an access token
        
    Example:
        @app.get("/protected")
        async def protected_route(user: TokenData = Depends(get_current_user_from_token)):
            return {"user_id": user.user_id}
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        token = credentials.credentials
        payload = decode_token(token)
        
        # Verify this is an access token
        if not verify_token_type(payload, "access"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type. Access token required.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Extract user_id from 'sub' claim
        user_id: Optional[str] = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        
        # Extract role if present
        role: Optional[str] = payload.get("role")
        
        return TokenData(
            user_id=user_id,
            role=role,
            token_type=payload.get("type", "access")
        )
        
    except JWTError:
        raise credentials_exception


async def get_current_employer(
    current_user: TokenData = Depends(get_current_user_from_token)
) -> TokenData:
    """
    Verify that the current user has the employer role.
    
    This dependency ensures the authenticated user is an employer.
    Use this for employer-only endpoints like job posting and application management.
    
    Args:
        current_user: TokenData from get_current_user_from_token
        
    Returns:
        TokenData for the employer user
        
    Raises:
        HTTPException: 403 if user does not have employer role
        
    Example:
        @app.post("/jobs")
        async def create_job(employer: TokenData = Depends(get_current_employer)):
            return {"employer_id": employer.user_id}
    """
    if current_user.role != "employer":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This endpoint requires employer role"
        )
    
    return current_user


async def get_current_job_seeker(
    current_user: TokenData = Depends(get_current_user_from_token)
) -> TokenData:
    """
    Verify that the current user has the job_seeker role.
    
    This dependency ensures the authenticated user is a job seeker.
    Use this for job seeker-only endpoints like job applications.
    
    Args:
        current_user: TokenData from get_current_user_from_token
        
    Returns:
        TokenData for the job seeker user
        
    Raises:
        HTTPException: 403 if user does not have job_seeker role
        
    Example:
        @app.post("/applications")
        async def apply_to_job(job_seeker: TokenData = Depends(get_current_job_seeker)):
            return {"job_seeker_id": job_seeker.user_id}
    """
    if current_user.role != "job_seeker":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This endpoint requires job_seeker role"
        )
    
    return current_user


async def get_current_admin(
    current_user: TokenData = Depends(get_current_user_from_token)
) -> TokenData:
    """
    Verify that the current user has the admin role.
    
    This dependency ensures the authenticated user is an administrator.
    Use this for admin-only endpoints like system configuration and monitoring.
    
    Args:
        current_user: TokenData from get_current_user_from_token
        
    Returns:
        TokenData for the admin user
        
    Raises:
        HTTPException: 403 if user does not have admin role
        
    Example:
        @app.get("/admin/stats")
        async def get_stats(admin: TokenData = Depends(get_current_admin)):
            return {"admin_id": admin.user_id}
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This endpoint requires admin role"
        )
    
    return current_user


async def verify_refresh_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> TokenData:
    """
    Validate JWT refresh token for token refresh endpoint.
    
    This dependency validates that the provided token is a valid refresh token
    and checks if it has been blacklisted (logged out).
    Use this specifically for the token refresh endpoint.
    
    Args:
        credentials: HTTP Bearer credentials from Authorization header
        
    Returns:
        TokenData containing user information from refresh token
        
    Raises:
        HTTPException: 401 if token is invalid, expired, blacklisted, or not a refresh token
        
    Example:
        @app.post("/auth/refresh")
        async def refresh_access_token(user: TokenData = Depends(verify_refresh_token)):
            new_token = create_access_token({"sub": user.user_id, "role": user.role})
            return {"access_token": new_token}
    """
    from app.core.redis import redis_client
    from app.core.security import is_token_blacklisted
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate refresh token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        token = credentials.credentials
        
        # Check if token is blacklisted
        redis = redis_client.get_cache_client()
        if is_token_blacklisted(redis, token):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been revoked",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        payload = decode_token(token)
        
        # Verify this is a refresh token
        if not verify_token_type(payload, "refresh"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type. Refresh token required.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Extract user_id from 'sub' claim
        user_id: Optional[str] = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        
        # Extract role if present
        role: Optional[str] = payload.get("role")
        
        return TokenData(
            user_id=user_id,
            role=role,
            token_type=payload.get("type", "refresh")
        )
        
    except JWTError:
        raise credentials_exception
