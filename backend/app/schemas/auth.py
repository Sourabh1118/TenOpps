"""
Authentication and authorization schemas for the job aggregation platform.

This module defines Pydantic models for JWT tokens and authentication responses.
"""
from typing import Optional
from pydantic import BaseModel, Field, EmailStr, field_validator


class Token(BaseModel):
    """
    JWT token response schema.
    
    Returned on successful login or token refresh.
    """
    access_token: str = Field(..., description="JWT access token valid for 15 minutes")
    refresh_token: str = Field(..., description="JWT refresh token valid for 7 days")
    token_type: str = Field(default="bearer", description="Token type (always 'bearer')")
    
    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer"
            }
        }


class EmployerRegistrationRequest(BaseModel):
    """
    Request schema for employer registration.
    
    Validates employer registration data including email, password, and company information.
    """
    email: EmailStr = Field(..., description="Employer email address")
    password: str = Field(..., min_length=8, description="Password (min 8 characters)")
    company_name: str = Field(..., min_length=2, max_length=100, description="Company name")
    company_website: Optional[str] = Field(None, description="Company website URL")
    company_description: Optional[str] = Field(None, description="Company description")
    
    @field_validator('company_website')
    @classmethod
    def validate_website(cls, v: Optional[str]) -> Optional[str]:
        """Validate company website URL format."""
        if v and not (v.startswith('http://') or v.startswith('https://')):
            raise ValueError('Company website must start with http:// or https://')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "employer@company.com",
                "password": "SecurePass123!",
                "company_name": "Tech Corp",
                "company_website": "https://techcorp.com",
                "company_description": "Leading technology company"
            }
        }


class JobSeekerRegistrationRequest(BaseModel):
    """
    Request schema for job seeker registration.
    
    Validates job seeker registration data including email, password, and profile information.
    """
    email: EmailStr = Field(..., description="Job seeker email address")
    password: str = Field(..., min_length=8, description="Password (min 8 characters)")
    full_name: str = Field(..., min_length=2, max_length=100, description="Full name")
    phone: Optional[str] = Field(None, description="Phone number")
    
    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        """Validate phone number format."""
        if v:
            # Remove common formatting characters
            cleaned = ''.join(c for c in v if c.isdigit() or c == '+')
            if len(cleaned) < 7 or len(cleaned) > 20:
                raise ValueError('Phone number must be between 7 and 20 digits')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "jobseeker@example.com",
                "password": "SecurePass123!",
                "full_name": "John Doe",
                "phone": "+1234567890"
            }
        }


class RegistrationResponse(BaseModel):
    """
    Response schema for successful registration.
    
    Returns user ID, role, and JWT tokens.
    """
    user_id: str = Field(..., description="User UUID")
    role: str = Field(..., description="User role (employer or job_seeker)")
    access_token: str = Field(..., description="JWT access token valid for 15 minutes")
    refresh_token: str = Field(..., description="JWT refresh token valid for 7 days")
    token_type: str = Field(default="bearer", description="Token type (always 'bearer')")
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "123e4567-e89b-12d3-a456-426614174000",
                "role": "employer",
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer"
            }
        }


class TokenData(BaseModel):
    """
    Decoded JWT token data schema.
    
    Represents the claims extracted from a validated JWT token.
    """
    user_id: str = Field(..., description="User ID from token subject")
    role: Optional[str] = Field(None, description="User role (employer, job_seeker, admin)")
    token_type: str = Field(..., description="Token type (access or refresh)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "123e4567-e89b-12d3-a456-426614174000",
                "role": "employer",
                "token_type": "access"
            }
        }


class RefreshTokenRequest(BaseModel):
    """
    Request schema for token refresh endpoint.
    """
    refresh_token: str = Field(..., description="Valid refresh token")
    
    class Config:
        json_schema_extra = {
            "example": {
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
            }
        }


class AccessTokenResponse(BaseModel):
    """
    Response schema for token refresh endpoint.
    
    Returns only a new access token (refresh token remains valid).
    """
    access_token: str = Field(..., description="New JWT access token valid for 15 minutes")
    token_type: str = Field(default="bearer", description="Token type (always 'bearer')")
    
    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer"
            }
        }


class LoginRequest(BaseModel):
    """
    Request schema for login endpoint.
    
    Accepts email and password for authentication.
    """
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="User password")
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "SecurePass123!"
            }
        }


class LoginResponse(BaseModel):
    """
    Response schema for successful login.
    
    Returns user ID, role, and JWT tokens.
    """
    user_id: str = Field(..., description="User UUID")
    role: str = Field(..., description="User role (employer or job_seeker)")
    access_token: str = Field(..., description="JWT access token valid for 15 minutes")
    refresh_token: str = Field(..., description="JWT refresh token valid for 7 days")
    token_type: str = Field(default="bearer", description="Token type (always 'bearer')")
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "123e4567-e89b-12d3-a456-426614174000",
                "role": "employer",
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer"
            }
        }


class LogoutRequest(BaseModel):
    """
    Request schema for logout endpoint.
    
    Accepts refresh token to be blacklisted.
    """
    refresh_token: str = Field(..., description="Refresh token to invalidate")
    
    class Config:
        json_schema_extra = {
            "example": {
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
            }
        }


class ErrorResponse(BaseModel):
    """
    Error response schema for authentication endpoints.
    """
    detail: str = Field(..., description="Error message")
    
    class Config:
        json_schema_extra = {
            "example": {
                "detail": "Email already registered"
            }
        }
