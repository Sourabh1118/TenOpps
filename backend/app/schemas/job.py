"""
Job schemas for request/response validation.

This module provides Pydantic models for job-related API operations including
job creation, updates, and responses.
"""
from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field, field_validator, model_validator
from app.models.job import JobType, ExperienceLevel, JobStatus, SourceType


class JobCreateRequest(BaseModel):
    """Schema for creating a direct job post."""
    title: str = Field(..., min_length=10, max_length=200, description="Job title (10-200 characters)")
    company: str = Field(..., min_length=2, max_length=100, description="Company name (2-100 characters)")
    location: str = Field(..., description="Job location")
    remote: bool = Field(default=False, description="Whether the job is remote")
    job_type: JobType = Field(..., description="Type of employment")
    experience_level: ExperienceLevel = Field(..., description="Required experience level")
    description: str = Field(..., min_length=50, max_length=5000, description="Job description (50-5000 characters)")
    requirements: Optional[List[str]] = Field(default=None, description="Job requirements")
    responsibilities: Optional[List[str]] = Field(default=None, description="Job responsibilities")
    salary_min: Optional[int] = Field(default=None, ge=0, description="Minimum salary")
    salary_max: Optional[int] = Field(default=None, ge=0, description="Maximum salary")
    salary_currency: Optional[str] = Field(default="USD", max_length=3, description="Salary currency code")
    expires_at: datetime = Field(..., description="Job expiration date (within 90 days)")
    featured: bool = Field(default=False, description="Whether to feature this job")
    tags: Optional[List[str]] = Field(default=None, description="Job tags")

    @model_validator(mode='after')
    def validate_salary_range(self):
        """Validate that salary_min < salary_max if both provided."""
        if self.salary_min is not None and self.salary_max is not None:
            if self.salary_min >= self.salary_max:
                raise ValueError("salary_min must be less than salary_max")
        return self

    @field_validator('expires_at')
    @classmethod
    def validate_expiration_date(cls, v: datetime) -> datetime:
        """Validate that expiration date is within 90 days."""
        from datetime import timedelta
        now = datetime.utcnow()
        max_expiration = now + timedelta(days=90)
        
        if v <= now:
            raise ValueError("Expiration date must be in the future")
        
        if v > max_expiration:
            raise ValueError("Expiration date must be within 90 days from now")
        
        return v


class JobUpdateRequest(BaseModel):
    """Schema for updating a job post."""
    title: Optional[str] = Field(None, min_length=10, max_length=200, description="Job title (10-200 characters)")
    location: Optional[str] = Field(None, description="Job location")
    remote: Optional[bool] = Field(None, description="Whether the job is remote")
    job_type: Optional[JobType] = Field(None, description="Type of employment")
    experience_level: Optional[ExperienceLevel] = Field(None, description="Required experience level")
    description: Optional[str] = Field(None, min_length=50, max_length=5000, description="Job description (50-5000 characters)")
    requirements: Optional[List[str]] = Field(None, description="Job requirements")
    responsibilities: Optional[List[str]] = Field(None, description="Job responsibilities")
    salary_min: Optional[int] = Field(None, ge=0, description="Minimum salary")
    salary_max: Optional[int] = Field(None, ge=0, description="Maximum salary")
    salary_currency: Optional[str] = Field(None, max_length=3, description="Salary currency code")
    expires_at: Optional[datetime] = Field(None, description="Job expiration date (within 90 days)")
    tags: Optional[List[str]] = Field(None, description="Job tags")

    @model_validator(mode='after')
    def validate_salary_range(self):
        """Validate that salary_min < salary_max if both provided."""
        if self.salary_min is not None and self.salary_max is not None:
            if self.salary_min >= self.salary_max:
                raise ValueError("salary_min must be less than salary_max")
        return self

    @field_validator('expires_at')
    @classmethod
    def validate_expiration_date(cls, v: Optional[datetime]) -> Optional[datetime]:
        """Validate that expiration date is within 90 days."""
        if v is None:
            return v
        
        from datetime import timedelta
        now = datetime.utcnow()
        max_expiration = now + timedelta(days=90)
        
        if v <= now:
            raise ValueError("Expiration date must be in the future")
        
        if v > max_expiration:
            raise ValueError("Expiration date must be within 90 days from now")
        
        return v


class JobResponse(BaseModel):
    """Schema for job response."""
    id: UUID
    title: str
    company: str
    location: str
    remote: bool
    job_type: JobType
    experience_level: ExperienceLevel
    description: str
    requirements: Optional[List[str]]
    responsibilities: Optional[List[str]]
    salary_min: Optional[int]
    salary_max: Optional[int]
    salary_currency: Optional[str]
    source_type: SourceType
    source_url: Optional[str]
    source_platform: Optional[str]
    employer_id: Optional[UUID]
    quality_score: float
    status: JobStatus
    posted_at: datetime
    expires_at: datetime
    created_at: datetime
    updated_at: datetime
    application_count: int
    view_count: int
    featured: bool
    tags: Optional[List[str]]

    class Config:
        from_attributes = True


class JobListResponse(BaseModel):
    """Schema for list of jobs."""
    jobs: List[JobResponse]
    total: int
    page: int
    page_size: int


class JobCreateResponse(BaseModel):
    """Schema for job creation response."""
    job_id: UUID
    message: str


class JobReactivateRequest(BaseModel):
    """Schema for reactivating an expired job."""
    expires_at: datetime = Field(..., description="New expiration date (within 90 days)")

    @field_validator('expires_at')
    @classmethod
    def validate_expiration_date(cls, v: datetime) -> datetime:
        """Validate that expiration date is within 90 days."""
        from datetime import timedelta
        now = datetime.utcnow()
        max_expiration = now + timedelta(days=90)
        
        if v <= now:
            raise ValueError("Expiration date must be in the future")
        
        if v > max_expiration:
            raise ValueError("Expiration date must be within 90 days from now")
        
        return v


class ErrorResponse(BaseModel):
    """Schema for error responses."""
    detail: str
