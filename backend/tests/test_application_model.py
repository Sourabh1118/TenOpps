"""
Unit tests for the Application model.

Tests cover:
- Model creation and field validation
- Status enum values
- Helper methods (is_pending, is_active, is_final)
- Timestamps and defaults
- Foreign key relationships
"""
import pytest
from datetime import datetime, timedelta
import uuid
from sqlalchemy.exc import IntegrityError

from app.models.application import Application, ApplicationStatus
from app.models.job import Job, JobType, ExperienceLevel, SourceType, JobStatus
from app.models.employer import Employer, SubscriptionTier


class TestApplicationModel:
    """Test suite for Application model."""

    def test_create_application_with_required_fields(self, db_session):
        """Test creating an application with all required fields."""
        # Create a job first
        employer = Employer(
            id=uuid.uuid4(),
            email="employer@test.com",
            password_hash="hashed_password",
            company_name="Test Company",
            subscription_tier=SubscriptionTier.FREE,
            subscription_start_date=datetime.now(),
            subscription_end_date=datetime.now() + timedelta(days=30)
        )
        db_session.add(employer)
        
        job = Job(
            id=uuid.uuid4(),
            title="Software Engineer",
            company="Test Company",
            location="San Francisco, CA",
            remote=True,
            job_type=JobType.FULL_TIME,
            experience_level=ExperienceLevel.MID,
            description="A great opportunity for a software engineer.",
            source_type=SourceType.DIRECT,
            employer_id=employer.id,
            quality_score=75.0,
            status=JobStatus.ACTIVE,
            posted_at=datetime.now(),
            expires_at=datetime.now() + timedelta(days=30)
        )
        db_session.add(job)
        db_session.commit()

        # Create application
        application = Application(
            id=uuid.uuid4(),
            job_id=job.id,
            job_seeker_id=uuid.uuid4(),
            resume="https://storage.example.com/resumes/resume.pdf",
            status=ApplicationStatus.SUBMITTED
        )
        db_session.add(application)
        db_session.commit()

        # Verify application was created
        assert application.id is not None
        assert application.job_id == job.id
        assert application.resume == "https://storage.example.com/resumes/resume.pdf"
        assert application.status == ApplicationStatus.SUBMITTED
        assert application.applied_at is not None
        assert application.updated_at is not None

    def test_application_with_cover_letter(self, db_session):
        """Test creating an application with optional cover letter."""
        # Create job
        job = Job(
            id=uuid.uuid4(),
            title="Data Scientist",
            company="Tech Corp",
            location="Remote",
            remote=True,
            job_type=JobType.FULL_TIME,
            experience_level=ExperienceLevel.SENIOR,
            description="Looking for an experienced data scientist.",
            source_type=SourceType.DIRECT,
            quality_score=80.0,
            status=JobStatus.ACTIVE,
            posted_at=datetime.now(),
            expires_at=datetime.now() + timedelta(days=30)
        )
        db_session.add(job)
        db_session.commit()

        # Create application with cover letter
        cover_letter = "I am very interested in this position..."
        application = Application(
            id=uuid.uuid4(),
            job_id=job.id,
            job_seeker_id=uuid.uuid4(),
            resume="https://storage.example.com/resumes/resume.pdf",
            cover_letter=cover_letter,
            status=ApplicationStatus.SUBMITTED
        )
        db_session.add(application)
        db_session.commit()

        assert application.cover_letter == cover_letter

    def test_application_status_enum_values(self, db_session):
        """Test all valid application status enum values."""
        job = Job(
            id=uuid.uuid4(),
            title="Product Manager",
            company="Startup Inc",
            location="New York, NY",
            remote=False,
            job_type=JobType.FULL_TIME,
            experience_level=ExperienceLevel.MID,
            description="Product manager role at a growing startup.",
            source_type=SourceType.DIRECT,
            quality_score=70.0,
            status=JobStatus.ACTIVE,
            posted_at=datetime.now(),
            expires_at=datetime.now() + timedelta(days=30)
        )
        db_session.add(job)
        db_session.commit()

        statuses = [
            ApplicationStatus.SUBMITTED,
            ApplicationStatus.REVIEWED,
            ApplicationStatus.SHORTLISTED,
            ApplicationStatus.REJECTED,
            ApplicationStatus.ACCEPTED
        ]

        for status in statuses:
            application = Application(
                id=uuid.uuid4(),
                job_id=job.id,
                job_seeker_id=uuid.uuid4(),
                resume="https://storage.example.com/resumes/resume.pdf",
                status=status
            )
            db_session.add(application)
            db_session.commit()
            assert application.status == status

    def test_application_default_status(self, db_session):
        """Test that default status is SUBMITTED."""
        job = Job(
            id=uuid.uuid4(),
            title="Designer",
            company="Design Studio",
            location="Los Angeles, CA",
            remote=True,
            job_type=JobType.FULL_TIME,
            experience_level=ExperienceLevel.ENTRY,
            description="Entry-level designer position.",
            source_type=SourceType.DIRECT,
            quality_score=65.0,
            status=JobStatus.ACTIVE,
            posted_at=datetime.now(),
            expires_at=datetime.now() + timedelta(days=30)
        )
        db_session.add(job)
        db_session.commit()

        application = Application(
            id=uuid.uuid4(),
            job_id=job.id,
            job_seeker_id=uuid.uuid4(),
            resume="https://storage.example.com/resumes/resume.pdf"
        )
        db_session.add(application)
        db_session.commit()

        assert application.status == ApplicationStatus.SUBMITTED

    def test_application_with_employer_notes(self, db_session):
        """Test adding employer notes to an application."""
        job = Job(
            id=uuid.uuid4(),
            title="Marketing Manager",
            company="Marketing Agency",
            location="Chicago, IL",
            remote=False,
            job_type=JobType.FULL_TIME,
            experience_level=ExperienceLevel.SENIOR,
            description="Senior marketing manager position.",
            source_type=SourceType.DIRECT,
            quality_score=75.0,
            status=JobStatus.ACTIVE,
            posted_at=datetime.now(),
            expires_at=datetime.now() + timedelta(days=30)
        )
        db_session.add(job)
        db_session.commit()

        application = Application(
            id=uuid.uuid4(),
            job_id=job.id,
            job_seeker_id=uuid.uuid4(),
            resume="https://storage.example.com/resumes/resume.pdf",
            employer_notes="Strong candidate, schedule interview"
        )
        db_session.add(application)
        db_session.commit()

        assert application.employer_notes == "Strong candidate, schedule interview"

    def test_application_missing_required_fields(self, db_session):
        """Test that creating an application without required fields fails."""
        with pytest.raises(IntegrityError):
            application = Application(
                id=uuid.uuid4(),
                job_seeker_id=uuid.uuid4(),
                # Missing job_id and resume
            )
            db_session.add(application)
            db_session.commit()

    def test_application_foreign_key_constraint(self, db_session):
        """Test that foreign key constraint is enforced."""
        with pytest.raises(IntegrityError):
            application = Application(
                id=uuid.uuid4(),
                job_id=uuid.uuid4(),  # Non-existent job
                job_seeker_id=uuid.uuid4(),
                resume="https://storage.example.com/resumes/resume.pdf"
            )
            db_session.add(application)
            db_session.commit()

    def test_is_pending_method(self, db_session):
        """Test is_pending() helper method."""
        job = Job(
            id=uuid.uuid4(),
            title="Developer",
            company="Tech Company",
            location="Remote",
            remote=True,
            job_type=JobType.FULL_TIME,
            experience_level=ExperienceLevel.MID,
            description="Developer position.",
            source_type=SourceType.DIRECT,
            quality_score=70.0,
            status=JobStatus.ACTIVE,
            posted_at=datetime.now(),
            expires_at=datetime.now() + timedelta(days=30)
        )
        db_session.add(job)
        db_session.commit()

        application = Application(
            id=uuid.uuid4(),
            job_id=job.id,
            job_seeker_id=uuid.uuid4(),
            resume="https://storage.example.com/resumes/resume.pdf",
            status=ApplicationStatus.SUBMITTED
        )
        db_session.add(application)
        db_session.commit()

        assert application.is_pending() is True

        application.status = ApplicationStatus.REVIEWED
        db_session.commit()
        assert application.is_pending() is False

    def test_is_active_method(self, db_session):
        """Test is_active() helper method."""
        job = Job(
            id=uuid.uuid4(),
            title="Analyst",
            company="Finance Corp",
            location="Boston, MA",
            remote=False,
            job_type=JobType.FULL_TIME,
            experience_level=ExperienceLevel.ENTRY,
            description="Entry-level analyst position.",
            source_type=SourceType.DIRECT,
            quality_score=65.0,
            status=JobStatus.ACTIVE,
            posted_at=datetime.now(),
            expires_at=datetime.now() + timedelta(days=30)
        )
        db_session.add(job)
        db_session.commit()

        application = Application(
            id=uuid.uuid4(),
            job_id=job.id,
            job_seeker_id=uuid.uuid4(),
            resume="https://storage.example.com/resumes/resume.pdf",
            status=ApplicationStatus.SUBMITTED
        )
        db_session.add(application)
        db_session.commit()

        # Active statuses
        assert application.is_active() is True
        
        application.status = ApplicationStatus.REVIEWED
        db_session.commit()
        assert application.is_active() is True
        
        application.status = ApplicationStatus.SHORTLISTED
        db_session.commit()
        assert application.is_active() is True

        # Inactive statuses
        application.status = ApplicationStatus.REJECTED
        db_session.commit()
        assert application.is_active() is False
        
        application.status = ApplicationStatus.ACCEPTED
        db_session.commit()
        assert application.is_active() is False

    def test_is_final_method(self, db_session):
        """Test is_final() helper method."""
        job = Job(
            id=uuid.uuid4(),
            title="Engineer",
            company="Engineering Firm",
            location="Seattle, WA",
            remote=True,
            job_type=JobType.FULL_TIME,
            experience_level=ExperienceLevel.SENIOR,
            description="Senior engineer position.",
            source_type=SourceType.DIRECT,
            quality_score=80.0,
            status=JobStatus.ACTIVE,
            posted_at=datetime.now(),
            expires_at=datetime.now() + timedelta(days=30)
        )
        db_session.add(job)
        db_session.commit()

        application = Application(
            id=uuid.uuid4(),
            job_id=job.id,
            job_seeker_id=uuid.uuid4(),
            resume="https://storage.example.com/resumes/resume.pdf",
            status=ApplicationStatus.SUBMITTED
        )
        db_session.add(application)
        db_session.commit()

        # Non-final statuses
        assert application.is_final() is False
        
        application.status = ApplicationStatus.REVIEWED
        db_session.commit()
        assert application.is_final() is False

        # Final statuses
        application.status = ApplicationStatus.REJECTED
        db_session.commit()
        assert application.is_final() is True
        
        application.status = ApplicationStatus.ACCEPTED
        db_session.commit()
        assert application.is_final() is True

    def test_application_repr(self, db_session):
        """Test string representation of Application."""
        job = Job(
            id=uuid.uuid4(),
            title="Writer",
            company="Media Company",
            location="Austin, TX",
            remote=True,
            job_type=JobType.FULL_TIME,
            experience_level=ExperienceLevel.MID,
            description="Content writer position.",
            source_type=SourceType.DIRECT,
            quality_score=70.0,
            status=JobStatus.ACTIVE,
            posted_at=datetime.now(),
            expires_at=datetime.now() + timedelta(days=30)
        )
        db_session.add(job)
        db_session.commit()

        application = Application(
            id=uuid.uuid4(),
            job_id=job.id,
            job_seeker_id=uuid.uuid4(),
            resume="https://storage.example.com/resumes/resume.pdf",
            status=ApplicationStatus.SUBMITTED
        )
        db_session.add(application)
        db_session.commit()

        repr_str = repr(application)
        assert "Application" in repr_str
        assert str(application.id) in repr_str
        assert str(application.job_id) in repr_str
        assert "submitted" in repr_str

    def test_application_cascade_delete(self, db_session):
        """Test that applications are deleted when job is deleted."""
        job = Job(
            id=uuid.uuid4(),
            title="Consultant",
            company="Consulting Firm",
            location="Washington, DC",
            remote=False,
            job_type=JobType.CONTRACT,
            experience_level=ExperienceLevel.SENIOR,
            description="Senior consultant position.",
            source_type=SourceType.DIRECT,
            quality_score=75.0,
            status=JobStatus.ACTIVE,
            posted_at=datetime.now(),
            expires_at=datetime.now() + timedelta(days=30)
        )
        db_session.add(job)
        db_session.commit()

        application = Application(
            id=uuid.uuid4(),
            job_id=job.id,
            job_seeker_id=uuid.uuid4(),
            resume="https://storage.example.com/resumes/resume.pdf",
            status=ApplicationStatus.SUBMITTED
        )
        db_session.add(application)
        db_session.commit()

        application_id = application.id

        # Delete the job
        db_session.delete(job)
        db_session.commit()

        # Verify application was also deleted
        deleted_application = db_session.query(Application).filter_by(id=application_id).first()
        assert deleted_application is None
