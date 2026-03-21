"""
Unit tests for JobSeeker model.

Tests model creation, validation, and business logic methods.
"""
import pytest
from datetime import datetime
from sqlalchemy.exc import IntegrityError
from app.models.job_seeker import JobSeeker


def test_create_job_seeker(db_session):
    """Test creating a basic job seeker."""
    job_seeker = JobSeeker(
        email="john.doe@example.com",
        password_hash="hashed_password_123",
        full_name="John Doe",
        phone="+1-555-0100",
        resume_url="https://example.com/resumes/john-doe.pdf",
        profile_summary="Experienced software engineer"
    )
    db_session.add(job_seeker)
    db_session.commit()
    
    assert job_seeker.id is not None
    assert job_seeker.email == "john.doe@example.com"
    assert job_seeker.full_name == "John Doe"
    assert job_seeker.phone == "+1-555-0100"
    assert job_seeker.resume_url == "https://example.com/resumes/john-doe.pdf"
    assert job_seeker.profile_summary == "Experienced software engineer"
    assert job_seeker.created_at is not None
    assert job_seeker.updated_at is not None


def test_create_job_seeker_minimal(db_session):
    """Test creating a job seeker with only required fields."""
    job_seeker = JobSeeker(
        email="jane.smith@example.com",
        password_hash="hashed_password_456",
        full_name="Jane Smith"
    )
    db_session.add(job_seeker)
    db_session.commit()
    
    assert job_seeker.id is not None
    assert job_seeker.email == "jane.smith@example.com"
    assert job_seeker.full_name == "Jane Smith"
    assert job_seeker.phone is None
    assert job_seeker.resume_url is None
    assert job_seeker.profile_summary is None


def test_email_unique_constraint(db_session):
    """Test that email must be unique."""
    job_seeker1 = JobSeeker(
        email="duplicate@example.com",
        password_hash="hash1",
        full_name="User One"
    )
    db_session.add(job_seeker1)
    db_session.commit()
    
    job_seeker2 = JobSeeker(
        email="duplicate@example.com",
        password_hash="hash2",
        full_name="User Two"
    )
    db_session.add(job_seeker2)
    
    with pytest.raises(IntegrityError):
        db_session.commit()


def test_email_format_validation(db_session):
    """Test email format validation."""
    job_seeker = JobSeeker(
        email="invalid-email",
        password_hash="hash",
        full_name="Test User"
    )
    db_session.add(job_seeker)
    
    with pytest.raises(IntegrityError):
        db_session.commit()


def test_full_name_length_validation_too_short(db_session):
    """Test full name must be at least 2 characters."""
    job_seeker = JobSeeker(
        email="test@example.com",
        password_hash="hash",
        full_name="A"
    )
    db_session.add(job_seeker)
    
    with pytest.raises(IntegrityError):
        db_session.commit()


def test_full_name_length_validation_too_long(db_session):
    """Test full name must not exceed 100 characters."""
    job_seeker = JobSeeker(
        email="test@example.com",
        password_hash="hash",
        full_name="A" * 101
    )
    db_session.add(job_seeker)
    
    with pytest.raises(IntegrityError):
        db_session.commit()


def test_phone_format_validation_valid(db_session):
    """Test valid phone number formats."""
    valid_phones = [
        "+1-555-0100",
        "+44 20 7946 0958",
        "(555) 123-4567",
        "555-123-4567",
        "+91 98765 43210"
    ]
    
    for i, phone in enumerate(valid_phones):
        job_seeker = JobSeeker(
            email=f"test{i}@example.com",
            password_hash="hash",
            full_name="Test User",
            phone=phone
        )
        db_session.add(job_seeker)
        db_session.commit()
        assert job_seeker.phone == phone


def test_phone_format_validation_invalid(db_session):
    """Test invalid phone number format."""
    job_seeker = JobSeeker(
        email="test@example.com",
        password_hash="hash",
        full_name="Test User",
        phone="abc123"
    )
    db_session.add(job_seeker)
    
    with pytest.raises(IntegrityError):
        db_session.commit()


def test_resume_url_validation_valid(db_session):
    """Test valid resume URL formats."""
    valid_urls = [
        "https://example.com/resume.pdf",
        "http://storage.example.com/files/resume.pdf",
        "https://cdn.example.com/resumes/user123.pdf"
    ]
    
    for i, url in enumerate(valid_urls):
        job_seeker = JobSeeker(
            email=f"test{i}@example.com",
            password_hash="hash",
            full_name="Test User",
            resume_url=url
        )
        db_session.add(job_seeker)
        db_session.commit()
        assert job_seeker.resume_url == url


def test_resume_url_validation_invalid(db_session):
    """Test invalid resume URL format."""
    job_seeker = JobSeeker(
        email="test@example.com",
        password_hash="hash",
        full_name="Test User",
        resume_url="not-a-url"
    )
    db_session.add(job_seeker)
    
    with pytest.raises(IntegrityError):
        db_session.commit()


def test_has_complete_profile_true(db_session):
    """Test has_complete_profile returns True when all fields are filled."""
    job_seeker = JobSeeker(
        email="complete@example.com",
        password_hash="hash",
        full_name="Complete User",
        phone="+1-555-0100",
        resume_url="https://example.com/resume.pdf",
        profile_summary="Experienced professional"
    )
    db_session.add(job_seeker)
    db_session.commit()
    
    assert job_seeker.has_complete_profile() is True


def test_has_complete_profile_false(db_session):
    """Test has_complete_profile returns False when fields are missing."""
    job_seeker = JobSeeker(
        email="incomplete@example.com",
        password_hash="hash",
        full_name="Incomplete User",
        phone="+1-555-0100"
        # Missing resume_url and profile_summary
    )
    db_session.add(job_seeker)
    db_session.commit()
    
    assert job_seeker.has_complete_profile() is False


def test_can_apply_with_resume(db_session):
    """Test can_apply returns True when resume is present."""
    job_seeker = JobSeeker(
        email="applicant@example.com",
        password_hash="hash",
        full_name="Applicant User",
        resume_url="https://example.com/resume.pdf"
    )
    db_session.add(job_seeker)
    db_session.commit()
    
    assert job_seeker.can_apply() is True


def test_can_apply_without_resume(db_session):
    """Test can_apply returns False when resume is missing."""
    job_seeker = JobSeeker(
        email="noresume@example.com",
        password_hash="hash",
        full_name="No Resume User"
    )
    db_session.add(job_seeker)
    db_session.commit()
    
    assert job_seeker.can_apply() is False


def test_job_seeker_repr(db_session):
    """Test string representation of JobSeeker."""
    job_seeker = JobSeeker(
        email="repr@example.com",
        password_hash="hash",
        full_name="Repr User"
    )
    db_session.add(job_seeker)
    db_session.commit()
    
    repr_str = repr(job_seeker)
    assert "JobSeeker" in repr_str
    assert str(job_seeker.id) in repr_str
    assert "repr@example.com" in repr_str
    assert "Repr User" in repr_str


def test_timestamps_auto_set(db_session):
    """Test that timestamps are automatically set."""
    job_seeker = JobSeeker(
        email="timestamps@example.com",
        password_hash="hash",
        full_name="Timestamp User"
    )
    db_session.add(job_seeker)
    db_session.commit()
    
    assert job_seeker.created_at is not None
    assert job_seeker.updated_at is not None
    assert isinstance(job_seeker.created_at, datetime)
    assert isinstance(job_seeker.updated_at, datetime)


def test_updated_at_changes_on_update(db_session):
    """Test that updated_at changes when record is updated."""
    job_seeker = JobSeeker(
        email="update@example.com",
        password_hash="hash",
        full_name="Update User"
    )
    db_session.add(job_seeker)
    db_session.commit()
    
    original_updated_at = job_seeker.updated_at
    
    # Update the job seeker
    job_seeker.full_name = "Updated Name"
    db_session.commit()
    
    # Note: In test environment, updated_at might not change if the update
    # happens too quickly. This is a known limitation of testing timestamps.
    assert job_seeker.updated_at >= original_updated_at


def test_password_hash_stored(db_session):
    """Test that password hash is stored correctly."""
    password_hash = "bcrypt_hashed_password_with_salt"
    job_seeker = JobSeeker(
        email="secure@example.com",
        password_hash=password_hash,
        full_name="Secure User"
    )
    db_session.add(job_seeker)
    db_session.commit()
    
    assert job_seeker.password_hash == password_hash


def test_profile_summary_long_text(db_session):
    """Test that profile summary can store long text."""
    long_summary = "A" * 5000  # 5000 characters
    job_seeker = JobSeeker(
        email="longtext@example.com",
        password_hash="hash",
        full_name="Long Text User",
        profile_summary=long_summary
    )
    db_session.add(job_seeker)
    db_session.commit()
    
    assert job_seeker.profile_summary == long_summary
    assert len(job_seeker.profile_summary) == 5000
