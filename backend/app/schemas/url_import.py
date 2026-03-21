"""
URL import schemas for request/response validation.

This module provides Pydantic models for URL import operations.
"""
from pydantic import BaseModel, Field, field_validator
from uuid import UUID
from typing import Optional


class URLImportRequest(BaseModel):
    """Schema for URL import request."""
    url: str = Field(..., min_length=10, max_length=2000, description="Job URL to import")
    
    @field_validator('url')
    @classmethod
    def validate_url_format(cls, v: str) -> str:
        """Validate that URL starts with http:// or https://."""
        if not v.startswith(('http://', 'https://')):
            raise ValueError("URL must start with http:// or https://")
        return v


class URLImportResponse(BaseModel):
    """Schema for URL import response."""
    task_id: UUID = Field(..., description="Import task ID for polling")
    message: str = Field(..., description="Status message")


class ImportStatusResponse(BaseModel):
    """Schema for import status response."""
    task_id: UUID = Field(..., description="Import task ID")
    status: str = Field(..., description="Task status (PENDING, RUNNING, COMPLETED, FAILED)")
    job_id: Optional[UUID] = Field(None, description="Job ID if import completed")
    error_message: Optional[str] = Field(None, description="Error message if import failed")
    created_at: str = Field(..., description="Task creation timestamp")
    completed_at: Optional[str] = Field(None, description="Task completion timestamp")


class ErrorResponse(BaseModel):
    """Schema for error responses."""
    detail: str
