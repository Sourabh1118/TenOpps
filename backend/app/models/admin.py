"""
Admin model for system administrators.
"""
import uuid
from sqlalchemy import Column, String, DateTime, Index, CheckConstraint
from sqlalchemy.sql import func
from app.db.base import Base, GUID


class Admin(Base):
    """
    Admin model representing system administrators with full access.
    
    Supports authentication and identifies users with the 'admin' role.
    """
    __tablename__ = "admins"

    # Primary key
    id = Column(GUID(), primary_key=True, default=uuid.uuid4, index=True)

    # Authentication
    email = Column(String(255), nullable=False, unique=True, index=True)
    password_hash = Column(String(255), nullable=False)
    
    # Profile information
    full_name = Column(String(100), nullable=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now())

    # Check constraints for validation
    __table_args__ = (
        # Email format validation
        CheckConstraint(
            "email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}$'",
            name="check_admin_email_format"
        ),
        # Full name length validation
        CheckConstraint(
            "char_length(full_name) >= 2 AND char_length(full_name) <= 100",
            name="check_admin_full_name_length"
        ),
    )

    def __repr__(self) -> str:
        return f"<Admin(id={self.id}, email='{self.email}', name='{self.full_name}')>"
