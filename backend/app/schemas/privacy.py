"""
Pydantic schemas for privacy and consent management.

This module defines request/response schemas for:
- Consent management
- Data export
- Account deletion
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime


class ConsentRequest(BaseModel):
    """Request schema for updating consent preferences."""
    
    marketing_emails: bool = Field(
        ...,
        description="Consent to receive marketing emails"
    )
    data_processing: bool = Field(
        ...,
        description="Consent to data processing for service improvement"
    )
    third_party_sharing: bool = Field(
        default=False,
        description="Consent to share data with third parties"
    )


class ConsentResponse(BaseModel):
    """Response schema for consent preferences."""
    
    user_id: str
    marketing_emails: bool
    data_processing: bool
    third_party_sharing: bool
    consent_date: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class DataExportResponse(BaseModel):
    """Response schema for data export."""
    
    user_type: str
    export_date: str
    personal_data: Dict[str, Any]
    activity: Dict[str, Any]


class AccountDeletionResponse(BaseModel):
    """Response schema for account deletion."""
    
    message: str
    deletion_date: str
    note: str
    applications_anonymized: Optional[int] = None
    jobs_marked_deleted: Optional[int] = None
