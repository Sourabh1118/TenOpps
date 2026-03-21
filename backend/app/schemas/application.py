"""
Application schemas for request/response validation.

This module provides Pydantic models for application-related API operations including
application submission, status updates, and responses.
"""
from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field, field_validator
from app.models.application import ApplicationStatus


class ApplicationSubmitRequest(BaseModel):
    """Schema for submitting a job application."""
    job_id: UUID = Field(..., description="Job ID to apply to")
    resume: str = Field(..., min_length=1, max_length=500, description="Resume file URL")
    cover_letter: Optional[str] = Field(None, description="Optional cover letter text")
    
    class Config:
        json_schema_extra = {
            "example": {
                "job_id": "123e4567-e89b-12d3-a456-426614174000",
                "resume": "https://storage.example.com/resumes/john-doe-resume.pdf",
                "cover_letter": "I am excited to apply for this position..."
            }
        }


class ApplicationStatusUpdateRequest(BaseModel):
    """Schema for updating application status (employer only)."""
    status: ApplicationStatus = Field(..., description="New application status")
    employer_notes: Optional[str] = Field(None, description="Optional employer notes")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "shortlisted",
                "employer_notes": "Strong candidate, schedule interview"
            }
        }


class ApplicationResponse(BaseModel):
    """Schema for application response."""
    id: UUID
    job_id: UUID
    job_seeker_id: UUID
    resume: str
    cover_letter: Optional[str]
    status: ApplicationStatus
    employer_notes: Optional[str]
    applied_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "job_id": "223e4567-e89b-12d3-a456-426614174000",
                "job_seeker_id": "323e4567-e89b-12d3-a456-426614174000",
                "resume": "https://storage.example.com/resumes/john-doe-resume.pdf",
                "cover_letter": "I am excited to apply...",
                "status": "submitted",
                "employer_notes": None,
                "applied_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-15T10:30:00Z"
            }
        }


class ApplicationWithJobSeekerInfo(BaseModel):
    """Schema for application with job seeker details (for employers)."""
    id: UUID
    job_id: UUID
    job_seeker_id: UUID
    applicant_name: str
    resume: str
    cover_letter: Optional[str]
    status: ApplicationStatus
    employer_notes: Optional[str]
    applied_at: datetime
    updated_at: datetime
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "job_id": "223e4567-e89b-12d3-a456-426614174000",
                "job_seeker_id": "323e4567-e89b-12d3-a456-426614174000",
                "applicant_name": "John Doe",
                "resume": "https://storage.example.com/resumes/john-doe-resume.pdf",
                "cover_letter": "I am excited to apply...",
                "status": "submitted",
                "employer_notes": None,
                "applied_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-15T10:30:00Z"
            }
        }


class ApplicationWithJobInfo(BaseModel):
    """Schema for application with job details (for job seekers)."""
    id: UUID
    job_id: UUID
    job_title: str
    company: str
    location: str
    resume: str
    cover_letter: Optional[str]
    status: ApplicationStatus
    applied_at: datetime
    updated_at: datetime
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "job_id": "223e4567-e89b-12d3-a456-426614174000",
                "job_title": "Senior Python Developer",
                "company": "Tech Corp",
                "location": "San Francisco, CA",
                "resume": "https://storage.example.com/resumes/john-doe-resume.pdf",
                "cover_letter": "I am excited to apply...",
                "status": "submitted",
                "applied_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-15T10:30:00Z"
            }
        }


class ApplicationSubmitResponse(BaseModel):
    """Schema for application submission response."""
    application_id: UUID
    message: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "application_id": "123e4567-e89b-12d3-a456-426614174000",
                "message": "Application submitted successfully"
            }
        }


class ApplicationListResponse(BaseModel):
    """Schema for list of applications."""
    applications: list[ApplicationWithJobSeekerInfo]
    total: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "applications": [],
                "total": 0
            }
        }


class MyApplicationsListResponse(BaseModel):
    """Schema for job seeker's applications list."""
    applications: list[ApplicationWithJobInfo]
    total: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "applications": [],
                "total": 0
            }
        }


class ErrorResponse(BaseModel):
    """Schema for error responses."""
    detail: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "detail": "Application not found"
            }
        }
