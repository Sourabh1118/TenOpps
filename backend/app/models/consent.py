"""
Consent model for GDPR compliance.

This module defines the Consent model that stores user consent
preferences for data processing, marketing, and third-party sharing.
"""
from datetime import datetime
from sqlalchemy import (
    Column,
    String,
    Boolean,
    DateTime,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid

from app.db.base import Base


class Consent(Base):
    """
    Consent model representing user consent preferences.
    
    Stores consent records for GDPR compliance, tracking when users
    agreed to various data processing activities.
    """
    __tablename__ = "consents"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)

    # User reference (can be job seeker or employer)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    user_type = Column(String(20), nullable=False)  # 'job_seeker' or 'employer'

    # Consent preferences
    marketing_emails = Column(Boolean, nullable=False, default=False)
    data_processing = Column(Boolean, nullable=False, default=True)
    third_party_sharing = Column(Boolean, nullable=False, default=False)

    # Timestamps
    consent_date = Column(DateTime(timezone=True), nullable=False, default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now())

    # Indexes for efficient querying
    __table_args__ = (
        Index("idx_consents_user", "user_id", "user_type"),
    )

    def __repr__(self) -> str:
        return f"<Consent(user_id={self.user_id}, user_type='{self.user_type}')>"
