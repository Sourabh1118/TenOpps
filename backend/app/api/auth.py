"""
Authentication API endpoints.

This module provides endpoints for user authentication, including:
- Employer registration
- Job seeker registration
- Login and logout
- Token refresh
- Token validation (for testing)
"""
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.api.dependencies import verify_refresh_token, get_current_user_from_token
from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    validate_password_strength,
)
from app.db.session import get_db
from app.models.employer import Employer, SubscriptionTier
from app.models.job_seeker import JobSeeker
from app.schemas.auth import (
    AccessTokenResponse,
    TokenData,
    EmployerRegistrationRequest,
    JobSeekerRegistrationRequest,
    RegistrationResponse,
    LoginRequest,
    LoginResponse,
    LogoutRequest,
    ErrorResponse,
)


router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post(
    "/register/employer",
    response_model=RegistrationResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid input or weak password"},
        409: {"model": ErrorResponse, "description": "Email already registered"},
    }
)
async def register_employer(
    registration_data: EmployerRegistrationRequest,
    db: Session = Depends(get_db)
):
    """
    Register a new employer account.
    
    This endpoint implements Requirements 8.1 and 12.1:
    - Assigns default free tier to new employers
    - Hashes passwords using bcrypt with cost factor 12
    - Validates password strength
    
    **Process:**
    1. Validate password strength
    2. Check if email is already registered
    3. Hash the password
    4. Create employer record with free tier
    5. Generate JWT tokens
    6. Return user ID, role, and tokens
    
    **Password Requirements:**
    - Minimum 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    - At least one special character
    
    **Example Request:**
    ```json
    {
      "email": "employer@company.com",
      "password": "SecurePass123!",
      "company_name": "Tech Corp",
      "company_website": "https://techcorp.com",
      "company_description": "Leading technology company"
    }
    ```
    
    **Example Response:**
    ```json
    {
      "user_id": "123e4567-e89b-12d3-a456-426614174000",
      "role": "employer",
      "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
      "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
      "token_type": "bearer"
    }
    ```
    """
    # Validate password strength
    is_valid, error_message = validate_password_strength(registration_data.password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_message
        )
    
    # Check if email already exists
    existing_employer = db.query(Employer).filter(
        Employer.email == registration_data.email
    ).first()
    
    if existing_employer:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered"
        )
    
    # Hash password
    password_hash = hash_password(registration_data.password)
    
    # Create employer with default free tier
    new_employer = Employer(
        email=registration_data.email,
        password_hash=password_hash,
        company_name=registration_data.company_name,
        company_website=registration_data.company_website,
        company_description=registration_data.company_description,
        subscription_tier=SubscriptionTier.FREE,
        subscription_start_date=datetime.utcnow(),
        subscription_end_date=datetime.utcnow() + timedelta(days=365),  # 1 year free tier
        monthly_posts_used=0,
        featured_posts_used=0,
        verified=False,
    )
    
    try:
        db.add(new_employer)
        db.commit()
        db.refresh(new_employer)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered"
        )
    
    # Generate JWT tokens
    access_token = create_access_token({
        "sub": str(new_employer.id),
        "role": "employer"
    })
    
    refresh_token = create_refresh_token({
        "sub": str(new_employer.id),
        "role": "employer"
    })
    
    return RegistrationResponse(
        user_id=str(new_employer.id),
        role="employer",
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer"
    )


@router.post(
    "/register/job-seeker",
    response_model=RegistrationResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid input or weak password"},
        409: {"model": ErrorResponse, "description": "Email already registered"},
    }
)
async def register_job_seeker(
    registration_data: JobSeekerRegistrationRequest,
    db: Session = Depends(get_db)
):
    """
    Register a new job seeker account.
    
    This endpoint implements Requirement 12.1:
    - Hashes passwords using bcrypt with cost factor 12
    - Validates password strength
    
    **Process:**
    1. Validate password strength
    2. Check if email is already registered
    3. Hash the password
    4. Create job seeker record
    5. Generate JWT tokens
    6. Return user ID, role, and tokens
    
    **Password Requirements:**
    - Minimum 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    - At least one special character
    
    **Example Request:**
    ```json
    {
      "email": "jobseeker@example.com",
      "password": "SecurePass123!",
      "full_name": "John Doe",
      "phone": "+1234567890"
    }
    ```
    
    **Example Response:**
    ```json
    {
      "user_id": "123e4567-e89b-12d3-a456-426614174000",
      "role": "job_seeker",
      "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
      "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
      "token_type": "bearer"
    }
    ```
    """
    # Validate password strength
    is_valid, error_message = validate_password_strength(registration_data.password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_message
        )
    
    # Check if email already exists
    existing_job_seeker = db.query(JobSeeker).filter(
        JobSeeker.email == registration_data.email
    ).first()
    
    if existing_job_seeker:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered"
        )
    
    # Hash password
    password_hash = hash_password(registration_data.password)
    
    # Create job seeker
    new_job_seeker = JobSeeker(
        email=registration_data.email,
        password_hash=password_hash,
        full_name=registration_data.full_name,
        phone=registration_data.phone,
    )
    
    try:
        db.add(new_job_seeker)
        db.commit()
        db.refresh(new_job_seeker)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered"
        )
    
    # Generate JWT tokens
    access_token = create_access_token({
        "sub": str(new_job_seeker.id),
        "role": "job_seeker"
    })
    
    refresh_token = create_refresh_token({
        "sub": str(new_job_seeker.id),
        "role": "job_seeker"
    })
    
    return RegistrationResponse(
        user_id=str(new_job_seeker.id),
        role="job_seeker",
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer"
    )


@router.post("/refresh", response_model=AccessTokenResponse)
async def refresh_access_token(
    user: TokenData = Depends(verify_refresh_token)
):
    """
    Refresh access token using a valid refresh token.
    
    This endpoint implements Requirement 12.9: System shall issue new access token
    when refresh token is used.
    
    **Process:**
    1. Validate the provided refresh token
    2. Extract user information from the token
    3. Generate a new access token with 15-minute expiration
    4. Return the new access token
    
    **Note:** The refresh token remains valid and is not rotated in this implementation.
    For enhanced security, consider implementing refresh token rotation.
    
    **Example Request:**
    ```
    POST /auth/refresh
    Authorization: Bearer <refresh_token>
    ```
    
    **Example Response:**
    ```json
    {
      "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
      "token_type": "bearer"
    }
    ```
    """
    # Generate new access token with user data from refresh token
    new_access_token = create_access_token({
        "sub": user.user_id,
        "role": user.role
    })
    
    return AccessTokenResponse(
        access_token=new_access_token,
        token_type="bearer"
    )


@router.get("/validate")
async def validate_token(
    current_user: TokenData = Depends(get_current_user_from_token)
):
    """
    Validate the current access token and return user information.
    
    This endpoint is useful for:
    - Testing token validity
    - Retrieving current user information
    - Debugging authentication issues
    
    **Example Request:**
    ```
    GET /auth/validate
    Authorization: Bearer <access_token>
    ```
    
    **Example Response:**
    ```json
    {
      "valid": true,
      "user_id": "123e4567-e89b-12d3-a456-426614174000",
      "role": "employer",
      "token_type": "access"
    }
    ```
    """
    return {
        "valid": True,
        "user_id": current_user.user_id,
        "role": current_user.role,
        "token_type": current_user.token_type
    }



@router.post(
    "/login",
    response_model=LoginResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Invalid credentials"},
        429: {"model": ErrorResponse, "description": "Too many login attempts"},
    }
)
async def login(
    login_data: LoginRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Login endpoint with credential validation and rate limiting.
    
    This endpoint implements Requirements 12.2, 12.3, 12.4, 12.10, and 14.2:
    - Validates credentials against stored hash
    - Issues JWT access token (15 minutes) and refresh token (7 days)
    - Applies rate limiting (5 attempts per 15 minutes per IP)
    - Checks both Employer and JobSeeker tables
    
    **Process:**
    1. Check rate limit for IP address
    2. Search for user in both Employer and JobSeeker tables
    3. Verify password using bcrypt
    4. Generate JWT tokens on success
    5. Return user ID, role, and tokens
    
    **Rate Limiting:**
    - Maximum 5 failed attempts per 15 minutes per IP
    - Returns 429 with Retry-After header when exceeded
    
    **Example Request:**
    ```json
    {
      "email": "user@example.com",
      "password": "SecurePass123!"
    }
    ```
    
    **Example Response:**
    ```json
    {
      "user_id": "123e4567-e89b-12d3-a456-426614174000",
      "role": "employer",
      "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
      "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
      "token_type": "bearer"
    }
    ```
    """
    from app.core.redis import redis_client
    from app.core.security import check_rate_limit, verify_password
    
    # Get client IP address
    client_ip = request.client.host if request.client else "unknown"
    
    # Check rate limit
    redis = redis_client.get_cache_client()
    is_allowed, retry_after = check_rate_limit(redis, client_ip)
    
    if not is_allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Please try again later.",
            headers={"Retry-After": str(retry_after)}
        )
    
    # Search for user in Employer table
    employer = db.query(Employer).filter(Employer.email == login_data.email).first()
    
    if employer:
        # Verify password
        if verify_password(login_data.password, employer.password_hash):
            # Generate JWT tokens
            access_token = create_access_token({
                "sub": str(employer.id),
                "role": "employer"
            })
            
            refresh_token = create_refresh_token({
                "sub": str(employer.id),
                "role": "employer"
            })
            
            return LoginResponse(
                user_id=str(employer.id),
                role="employer",
                access_token=access_token,
                refresh_token=refresh_token,
                token_type="bearer"
            )
    
    # Search for user in JobSeeker table
    job_seeker = db.query(JobSeeker).filter(JobSeeker.email == login_data.email).first()
    
    if job_seeker:
        # Verify password
        if verify_password(login_data.password, job_seeker.password_hash):
            # Generate JWT tokens
            access_token = create_access_token({
                "sub": str(job_seeker.id),
                "role": "job_seeker"
            })
            
            refresh_token = create_refresh_token({
                "sub": str(job_seeker.id),
                "role": "job_seeker"
            })
            
            return LoginResponse(
                user_id=str(job_seeker.id),
                role="job_seeker",
                access_token=access_token,
                refresh_token=refresh_token,
                token_type="bearer"
            )
    
    # Invalid credentials - return 401
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid email or password"
    )


@router.post(
    "/logout",
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Successfully logged out"},
        401: {"model": ErrorResponse, "description": "Invalid or expired token"},
    }
)
async def logout(
    logout_data: LogoutRequest,
    db: Session = Depends(get_db)
):
    """
    Logout endpoint to invalidate refresh tokens.
    
    This endpoint implements Requirement 12.10:
    - Accepts refresh token in request body
    - Adds refresh token to Redis blacklist
    - Token remains blacklisted until its natural expiration
    
    **Process:**
    1. Validate the refresh token format
    2. Decode token to get expiration time
    3. Add token to Redis blacklist with TTL matching token expiry
    4. Return success confirmation
    
    **Note:** Access tokens cannot be invalidated server-side due to their stateless
    nature. They will expire naturally after 15 minutes. For enhanced security,
    clients should delete both tokens from local storage on logout.
    
    **Example Request:**
    ```json
    {
      "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    }
    ```
    
    **Example Response:**
    ```json
    {
      "message": "Successfully logged out",
      "detail": "Refresh token has been invalidated"
    }
    ```
    """
    from app.core.redis import redis_client
    from app.core.security import decode_token, add_token_to_blacklist
    from jose import JWTError
    
    try:
        # Decode token to verify it's valid and get expiration
        payload = decode_token(logout_data.refresh_token)
        
        # Verify it's a refresh token
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid token type. Refresh token required."
            )
        
        # Calculate remaining TTL (time until token expires)
        exp_timestamp = payload.get("exp")
        if exp_timestamp:
            from datetime import datetime
            current_timestamp = datetime.utcnow().timestamp()
            ttl_seconds = int(exp_timestamp - current_timestamp)
            
            # Only blacklist if token hasn't expired yet
            if ttl_seconds > 0:
                redis = redis_client.get_cache_client()
                add_token_to_blacklist(redis, logout_data.refresh_token, ttl_seconds)
        
        return {
            "message": "Successfully logged out",
            "detail": "Refresh token has been invalidated"
        }
        
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
