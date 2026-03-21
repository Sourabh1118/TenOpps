"""
Tests for the Job model.

Tests cover:
- Model creation with valid data
- Validation constraints (title length, salary range, etc.)
- Enum values
- Helper methods (is_active, is_expired, etc.)
"""
import pytest
from datetime import datetime, timedelta
import uuid
from sqlalchemy.exc import IntegrityError
from app.models import Job, JobType, ExperienceLevel, SourceType, JobStatus


def test_job_model_creation():
    """Test creating a Job instance with valid data."""
    job = Job(
        id=uuid.uuid4(),
        title="Senior Software Engineer",
        company="Tech Corp",
        location="San Francisco, CA",
        remote=True,
        job_type=JobType.FULL_TIME,
        experience_level=ExperienceLevel.SENIOR,
        description="We are looking for a senior software engineer with 5+ years of experience in Python and web development.",
        source_type=SourceType.DIRECT,
        quality_score=85.0,
        status=JobStatus.ACTIVE,
        posted_at=datetime.now(),
        expires_at=datetime.now() + timedelta(days=30),
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    
    assert job.title == "Senior Software Engineer"
    assert job.company == "Tech Corp"
    assert job.remote is True
    assert job.job_type == JobType.FULL_TIME
    assert job.experience_level == ExperienceLevel.SENIOR
    assert job.source_type == SourceType.DIRECT
    assert job.status == JobStatus.ACTIVE
    assert job.quality_score == 85.0


def test_job_enums():
    """Test that all enum values are accessible."""
    # JobType enum
    assert JobType.FULL_TIME.value == "full_time"
    assert JobType.PART_TIME.value == "part_time"
    assert JobType.CONTRACT.value == "contract"
    assert JobType.FREELANCE.value == "freelance"
    assert JobType.INTERNSHIP.value == "internship"
    assert JobType.FELLOWSHIP.value == "fellowship"
    assert JobType.ACADEMIC.value == "academic"
    
    # ExperienceLevel enum
    assert ExperienceLevel.ENTRY.value == "entry"
    assert ExperienceLevel.MID.value == "mid"
    assert ExperienceLevel.SENIOR.value == "senior"
    assert ExperienceLevel.LEAD.value == "lead"
    assert ExperienceLevel.EXECUTIVE.value == "executive"
    
    # SourceType enum
    assert SourceType.DIRECT.value == "direct"
    assert SourceType.URL_IMPORT.value == "url_import"
    assert SourceType.AGGREGATED.value == "aggregated"
    
    # JobStatus enum
    assert JobStatus.ACTIVE.value == "active"
    assert JobStatus.EXPIRED.value == "expired"
    assert JobStatus.FILLED.value == "filled"
    assert JobStatus.DELETED.value == "deleted"


def test_job_is_active():
    """Test is_active method."""
    # Active job
    active_job = Job(
        id=uuid.uuid4(),
        title="Software Engineer",
        company="Tech Corp",
        location="Remote",
        job_type=JobType.FULL_TIME,
        experience_level=ExperienceLevel.MID,
        description="A great opportunity for a mid-level software engineer.",
        source_type=SourceType.DIRECT,
        status=JobStatus.ACTIVE,
        posted_at=datetime.now(),
        expires_at=datetime.now() + timedelta(days=30),
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    assert active_job.is_active() is True
    
    # Expired job
    expired_job = Job(
        id=uuid.uuid4(),
        title="Software Engineer",
        company="Tech Corp",
        location="Remote",
        job_type=JobType.FULL_TIME,
        experience_level=ExperienceLevel.MID,
        description="A great opportunity for a mid-level software engineer.",
        source_type=SourceType.DIRECT,
        status=JobStatus.ACTIVE,
        posted_at=datetime.now() - timedelta(days=60),
        expires_at=datetime.now() - timedelta(days=1),
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    assert expired_job.is_active() is False
    
    # Filled job
    filled_job = Job(
        id=uuid.uuid4(),
        title="Software Engineer",
        company="Tech Corp",
        location="Remote",
        job_type=JobType.FULL_TIME,
        experience_level=ExperienceLevel.MID,
        description="A great opportunity for a mid-level software engineer.",
        source_type=SourceType.DIRECT,
        status=JobStatus.FILLED,
        posted_at=datetime.now(),
        expires_at=datetime.now() + timedelta(days=30),
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    assert filled_job.is_active() is False


def test_job_is_expired():
    """Test is_expired method."""
    # Not expired
    job = Job(
        id=uuid.uuid4(),
        title="Software Engineer",
        company="Tech Corp",
        location="Remote",
        job_type=JobType.FULL_TIME,
        experience_level=ExperienceLevel.MID,
        description="A great opportunity for a mid-level software engineer.",
        source_type=SourceType.DIRECT,
        status=JobStatus.ACTIVE,
        posted_at=datetime.now(),
        expires_at=datetime.now() + timedelta(days=30),
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    assert job.is_expired() is False
    
    # Expired
    expired_job = Job(
        id=uuid.uuid4(),
        title="Software Engineer",
        company="Tech Corp",
        location="Remote",
        job_type=JobType.FULL_TIME,
        experience_level=ExperienceLevel.MID,
        description="A great opportunity for a mid-level software engineer.",
        source_type=SourceType.DIRECT,
        status=JobStatus.ACTIVE,
        posted_at=datetime.now() - timedelta(days=60),
        expires_at=datetime.now() - timedelta(days=1),
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    assert expired_job.is_expired() is True


def test_job_days_until_expiration():
    """Test days_until_expiration method."""
    # Job expiring in 30 days
    job = Job(
        id=uuid.uuid4(),
        title="Software Engineer",
        company="Tech Corp",
        location="Remote",
        job_type=JobType.FULL_TIME,
        experience_level=ExperienceLevel.MID,
        description="A great opportunity for a mid-level software engineer.",
        source_type=SourceType.DIRECT,
        status=JobStatus.ACTIVE,
        posted_at=datetime.now(),
        expires_at=datetime.now() + timedelta(days=30),
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    assert job.days_until_expiration() >= 29  # Allow for timing differences
    
    # Already expired
    expired_job = Job(
        id=uuid.uuid4(),
        title="Software Engineer",
        company="Tech Corp",
        location="Remote",
        job_type=JobType.FULL_TIME,
        experience_level=ExperienceLevel.MID,
        description="A great opportunity for a mid-level software engineer.",
        source_type=SourceType.DIRECT,
        status=JobStatus.ACTIVE,
        posted_at=datetime.now() - timedelta(days=60),
        expires_at=datetime.now() - timedelta(days=1),
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    assert expired_job.days_until_expiration() == 0


def test_job_is_direct_post():
    """Test is_direct_post method."""
    # Direct post
    direct_job = Job(
        id=uuid.uuid4(),
        title="Software Engineer",
        company="Tech Corp",
        location="Remote",
        job_type=JobType.FULL_TIME,
        experience_level=ExperienceLevel.MID,
        description="A great opportunity for a mid-level software engineer.",
        source_type=SourceType.DIRECT,
        status=JobStatus.ACTIVE,
        posted_at=datetime.now(),
        expires_at=datetime.now() + timedelta(days=30),
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    assert direct_job.is_direct_post() is True
    
    # Aggregated job
    aggregated_job = Job(
        id=uuid.uuid4(),
        title="Software Engineer",
        company="Tech Corp",
        location="Remote",
        job_type=JobType.FULL_TIME,
        experience_level=ExperienceLevel.MID,
        description="A great opportunity for a mid-level software engineer.",
        source_type=SourceType.AGGREGATED,
        status=JobStatus.ACTIVE,
        posted_at=datetime.now(),
        expires_at=datetime.now() + timedelta(days=30),
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    assert aggregated_job.is_direct_post() is False


def test_job_can_receive_applications():
    """Test can_receive_applications method."""
    # Direct post, active
    direct_active = Job(
        id=uuid.uuid4(),
        title="Software Engineer",
        company="Tech Corp",
        location="Remote",
        job_type=JobType.FULL_TIME,
        experience_level=ExperienceLevel.MID,
        description="A great opportunity for a mid-level software engineer.",
        source_type=SourceType.DIRECT,
        status=JobStatus.ACTIVE,
        posted_at=datetime.now(),
        expires_at=datetime.now() + timedelta(days=30),
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    assert direct_active.can_receive_applications() is True
    
    # Direct post, expired
    direct_expired = Job(
        id=uuid.uuid4(),
        title="Software Engineer",
        company="Tech Corp",
        location="Remote",
        job_type=JobType.FULL_TIME,
        experience_level=ExperienceLevel.MID,
        description="A great opportunity for a mid-level software engineer.",
        source_type=SourceType.DIRECT,
        status=JobStatus.ACTIVE,
        posted_at=datetime.now() - timedelta(days=60),
        expires_at=datetime.now() - timedelta(days=1),
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    assert direct_expired.can_receive_applications() is False
    
    # Aggregated job, active
    aggregated_active = Job(
        id=uuid.uuid4(),
        title="Software Engineer",
        company="Tech Corp",
        location="Remote",
        job_type=JobType.FULL_TIME,
        experience_level=ExperienceLevel.MID,
        description="A great opportunity for a mid-level software engineer.",
        source_type=SourceType.AGGREGATED,
        status=JobStatus.ACTIVE,
        posted_at=datetime.now(),
        expires_at=datetime.now() + timedelta(days=30),
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    assert aggregated_active.can_receive_applications() is False


def test_job_with_salary_range():
    """Test job with salary information."""
    job = Job(
        id=uuid.uuid4(),
        title="Senior Software Engineer",
        company="Tech Corp",
        location="San Francisco, CA",
        job_type=JobType.FULL_TIME,
        experience_level=ExperienceLevel.SENIOR,
        description="We are looking for a senior software engineer with 5+ years of experience.",
        source_type=SourceType.DIRECT,
        salary_min=120000,
        salary_max=180000,
        salary_currency="USD",
        status=JobStatus.ACTIVE,
        posted_at=datetime.now(),
        expires_at=datetime.now() + timedelta(days=30),
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    
    assert job.salary_min == 120000
    assert job.salary_max == 180000
    assert job.salary_currency == "USD"


def test_job_with_arrays():
    """Test job with requirements and responsibilities arrays."""
    job = Job(
        id=uuid.uuid4(),
        title="Software Engineer",
        company="Tech Corp",
        location="Remote",
        job_type=JobType.FULL_TIME,
        experience_level=ExperienceLevel.MID,
        description="A great opportunity for a mid-level software engineer.",
        requirements=["Python", "FastAPI", "PostgreSQL", "5+ years experience"],
        responsibilities=["Design APIs", "Write tests", "Code reviews"],
        tags=["python", "backend", "remote"],
        source_type=SourceType.DIRECT,
        status=JobStatus.ACTIVE,
        posted_at=datetime.now(),
        expires_at=datetime.now() + timedelta(days=30),
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    
    assert len(job.requirements) == 4
    assert "Python" in job.requirements
    assert len(job.responsibilities) == 3
    assert "Design APIs" in job.responsibilities
    assert len(job.tags) == 3
    assert "python" in job.tags


def test_job_repr():
    """Test string representation of Job."""
    job = Job(
        id=uuid.uuid4(),
        title="Software Engineer",
        company="Tech Corp",
        location="Remote",
        job_type=JobType.FULL_TIME,
        experience_level=ExperienceLevel.MID,
        description="A great opportunity for a mid-level software engineer.",
        source_type=SourceType.DIRECT,
        status=JobStatus.ACTIVE,
        posted_at=datetime.now(),
        expires_at=datetime.now() + timedelta(days=30),
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    
    repr_str = repr(job)
    assert "Job" in repr_str
    assert "Software Engineer" in repr_str
    assert "Tech Corp" in repr_str
    assert "active" in repr_str
