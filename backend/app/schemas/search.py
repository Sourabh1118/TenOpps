"""
Search schemas for job search and filtering.

This module provides Pydantic models for job search filters and results.
"""
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator
from app.models.job import JobType, ExperienceLevel, SourceType


class SearchFilters(BaseModel):
    """
    Schema for job search filters.
    
    All filters are optional and can be combined. When multiple filters are
    provided, they are combined with AND logic (all filters must match).
    """
    query: Optional[str] = Field(
        default=None,
        description="Full-text search query for job title and description",
        max_length=200
    )
    location: Optional[str] = Field(
        default=None,
        description="Job location filter (exact match)",
        max_length=200
    )
    jobType: Optional[List[JobType]] = Field(
        default=None,
        description="Filter by job types (FULL_TIME, PART_TIME, CONTRACT, etc.)"
    )
    experienceLevel: Optional[List[ExperienceLevel]] = Field(
        default=None,
        description="Filter by experience levels (ENTRY, MID, SENIOR, LEAD, EXECUTIVE)"
    )
    salaryMin: Optional[int] = Field(
        default=None,
        ge=0,
        description="Minimum salary filter (jobs with salary >= this value)"
    )
    salaryMax: Optional[int] = Field(
        default=None,
        ge=0,
        description="Maximum salary filter (jobs with salary <= this value)"
    )
    remote: Optional[bool] = Field(
        default=None,
        description="Filter for remote jobs only (true) or all jobs (null/false)"
    )
    postedWithin: Optional[int] = Field(
        default=None,
        ge=1,
        le=365,
        description="Filter jobs posted within this many days (1-365)"
    )
    sourceType: Optional[List[SourceType]] = Field(
        default=None,
        description="Filter by source types (DIRECT, URL_IMPORT, AGGREGATED)"
    )

    @field_validator('salaryMax')
    @classmethod
    def validate_salary_range(cls, v: Optional[int], info) -> Optional[int]:
        """Validate that salaryMax >= salaryMin if both provided."""
        if v is not None and info.data.get('salaryMin') is not None:
            if v < info.data['salaryMin']:
                raise ValueError("salaryMax must be greater than or equal to salaryMin")
        return v

    @field_validator('jobType', 'experienceLevel', 'sourceType')
    @classmethod
    def validate_non_empty_lists(cls, v: Optional[List]) -> Optional[List]:
        """Ensure filter lists are not empty if provided."""
        if v is not None and len(v) == 0:
            raise ValueError("Filter list cannot be empty")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "query": "software engineer",
                "location": "San Francisco",
                "jobType": ["FULL_TIME"],
                "experienceLevel": ["MID", "SENIOR"],
                "salaryMin": 100000,
                "salaryMax": 200000,
                "remote": True,
                "postedWithin": 7,
                "sourceType": ["DIRECT", "URL_IMPORT"]
            }
        }
