"""
Unit tests for JobSource model.

Tests cover:
- Model creation and field validation
- Foreign key relationships
- Timestamp tracking
- Status management
- Helper methods
"""
import pytest
from datetime import datetime, timedelta
from sqlalchemy.exc import IntegrityError
import uuid

from app.models.job_source import JobSource
from app.models.job import Job, JobType, ExperienceLevel, SourceType, JobStatus


class TestJobSourceModel:
    """Test suite for JobSource model."""

    def test_create_job_source_with_required_fields(self, db_session):
        """Test creating a job source with all required fields."""
        # Create a job first
        job = Job(
            title="Software Engineer",
            company="Tech Corp",
            location="San Francisco, CA",
            remote=False,
            job_type=JobType.FULL_TIME,
            experience_level=ExperienceLevel.MID,
            description="A great opportunity for a software engineer.",
            source_type=SourceType.AGGREGATED,
            quality_score=50.0,
            status=JobStatus.ACTIVE,
            posted_at=datetime.now(),
            expires_at=datetime.now() + timedelta(days=30)
        )
        db_session.add(job)
        db_session.commit()

        # Create job source
        job_source = JobSource(
            job_id=job.id,
            source_platform="LinkedIn",
            source_url="https://www.linkedin.com/jobs/view/123456"
        )
        db_session.add(job_source)
        db_session.commit()

        # Verify
        assert job_source.id is not None
        assert job_source.job_id == job.id
        assert job_source.source_platform == "LinkedIn"
        assert job_source.source_url == "https://www.linkedin.com/jobs/view/123456"
        assert job_source.is_active is True
        assert job_source.scraped_at is not None
        assert job_source.last_verified_at is not None

    def test_create_job_source_with_optional_fields(self, db_session):
        """Test creating a job source with optional fields."""
        # Create a job first
        job = Job(
            title="Data Scientist",
            company="Data Inc",
            location="Remote",
            remote=True,
            job_type=JobType.FULL_TIME,
            experience_level=ExperienceLevel.SENIOR,
            description="Looking for an experienced data scientist.",
            source_type=SourceType.AGGREGATED,
            quality_score=60.0,
            status=JobStatus.ACTIVE,
            posted_at=datetime.now(),
            expires_at=datetime.now() + timedelta(days=45)
        )
        db_session.add(job)
        db_session.commit()

        # Create job source with optional fields
        job_source = JobSource(
            job_id=job.id,
            source_platform="Indeed",
            source_url="https://www.indeed.com/viewjob?jk=abc123",
            source_job_id="abc123",
            is_active=False
        )
        db_session.add(job_source)
        db_session.commit()

        # Verify
        assert job_source.source_job_id == "abc123"
        assert job_source.is_active is False

    def test_job_source_foreign_key_constraint(self, db_session):
        """Test that job_id must reference an existing job."""
        # Try to create job source with non-existent job_id
        job_source = JobSource(
            job_id=uuid.uuid4(),
            source_platform="Monster",
            source_url="https://www.monster.com/job/12345"
        )
        db_session.add(job_source)

        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_job_source_cascade_delete(self, db_session):
        """Test that job sources are deleted when parent job is deleted."""
        # Create a job
        job = Job(
            title="Product Manager",
            company="Product Co",
            location="New York, NY",
            remote=False,
            job_type=JobType.FULL_TIME,
            experience_level=ExperienceLevel.LEAD,
            description="Lead product management role.",
            source_type=SourceType.AGGREGATED,
            quality_score=70.0,
            status=JobStatus.ACTIVE,
            posted_at=datetime.now(),
            expires_at=datetime.now() + timedelta(days=60)
        )
        db_session.add(job)
        db_session.commit()

        # Create multiple job sources
        source1 = JobSource(
            job_id=job.id,
            source_platform="LinkedIn",
            source_url="https://www.linkedin.com/jobs/view/111"
        )
        source2 = JobSource(
            job_id=job.id,
            source_platform="Indeed",
            source_url="https://www.indeed.com/viewjob?jk=222"
        )
        db_session.add_all([source1, source2])
        db_session.commit()

        source1_id = source1.id
        source2_id = source2.id

        # Delete the job
        db_session.delete(job)
        db_session.commit()

        # Verify job sources are also deleted
        assert db_session.query(JobSource).filter_by(id=source1_id).first() is None
        assert db_session.query(JobSource).filter_by(id=source2_id).first() is None

    def test_multiple_sources_per_job(self, db_session):
        """Test that a job can have multiple sources (deduplication scenario)."""
        # Create a job
        job = Job(
            title="DevOps Engineer",
            company="Cloud Systems",
            location="Austin, TX",
            remote=True,
            job_type=JobType.FULL_TIME,
            experience_level=ExperienceLevel.MID,
            description="DevOps engineer needed for cloud infrastructure.",
            source_type=SourceType.AGGREGATED,
            quality_score=55.0,
            status=JobStatus.ACTIVE,
            posted_at=datetime.now(),
            expires_at=datetime.now() + timedelta(days=30)
        )
        db_session.add(job)
        db_session.commit()

        # Create multiple sources for the same job
        sources = [
            JobSource(
                job_id=job.id,
                source_platform="LinkedIn",
                source_url="https://www.linkedin.com/jobs/view/aaa"
            ),
            JobSource(
                job_id=job.id,
                source_platform="Indeed",
                source_url="https://www.indeed.com/viewjob?jk=bbb"
            ),
            JobSource(
                job_id=job.id,
                source_platform="Naukri",
                source_url="https://www.naukri.com/job-listings/ccc"
            ),
        ]
        db_session.add_all(sources)
        db_session.commit()

        # Verify all sources are linked to the same job
        job_sources = db_session.query(JobSource).filter_by(job_id=job.id).all()
        assert len(job_sources) == 3
        assert set(s.source_platform for s in job_sources) == {"LinkedIn", "Indeed", "Naukri"}

    def test_is_stale_method(self, db_session):
        """Test the is_stale helper method."""
        # Create a job
        job = Job(
            title="QA Engineer",
            company="Test Corp",
            location="Seattle, WA",
            remote=False,
            job_type=JobType.FULL_TIME,
            experience_level=ExperienceLevel.ENTRY,
            description="Quality assurance engineer position.",
            source_type=SourceType.AGGREGATED,
            quality_score=45.0,
            status=JobStatus.ACTIVE,
            posted_at=datetime.now(),
            expires_at=datetime.now() + timedelta(days=30)
        )
        db_session.add(job)
        db_session.commit()

        # Create job source with recent verification
        recent_source = JobSource(
            job_id=job.id,
            source_platform="Monster",
            source_url="https://www.monster.com/job/recent",
            last_verified_at=datetime.now() - timedelta(days=3)
        )
        db_session.add(recent_source)
        db_session.commit()

        # Create job source with old verification
        stale_source = JobSource(
            job_id=job.id,
            source_platform="Indeed",
            source_url="https://www.indeed.com/viewjob?jk=old",
            last_verified_at=datetime.now() - timedelta(days=10)
        )
        db_session.add(stale_source)
        db_session.commit()

        # Test is_stale with default threshold (7 days)
        assert recent_source.is_stale() is False
        assert stale_source.is_stale() is True

        # Test is_stale with custom threshold
        assert recent_source.is_stale(days=2) is True
        assert stale_source.is_stale(days=15) is False

    def test_mark_verified_method(self, db_session):
        """Test the mark_verified helper method."""
        # Create a job
        job = Job(
            title="Frontend Developer",
            company="Web Solutions",
            location="Boston, MA",
            remote=True,
            job_type=JobType.CONTRACT,
            experience_level=ExperienceLevel.MID,
            description="Frontend developer for web applications.",
            source_type=SourceType.AGGREGATED,
            quality_score=50.0,
            status=JobStatus.ACTIVE,
            posted_at=datetime.now(),
            expires_at=datetime.now() + timedelta(days=30)
        )
        db_session.add(job)
        db_session.commit()

        # Create job source with old verification
        job_source = JobSource(
            job_id=job.id,
            source_platform="LinkedIn",
            source_url="https://www.linkedin.com/jobs/view/xyz",
            last_verified_at=datetime.now() - timedelta(days=5)
        )
        db_session.add(job_source)
        db_session.commit()

        old_verified_at = job_source.last_verified_at

        # Mark as verified
        job_source.mark_verified()
        db_session.commit()

        # Verify timestamp was updated
        assert job_source.last_verified_at > old_verified_at

    def test_mark_inactive_method(self, db_session):
        """Test the mark_inactive helper method."""
        # Create a job
        job = Job(
            title="Backend Developer",
            company="API Systems",
            location="Denver, CO",
            remote=False,
            job_type=JobType.FULL_TIME,
            experience_level=ExperienceLevel.SENIOR,
            description="Backend developer for API development.",
            source_type=SourceType.AGGREGATED,
            quality_score=65.0,
            status=JobStatus.ACTIVE,
            posted_at=datetime.now(),
            expires_at=datetime.now() + timedelta(days=30)
        )
        db_session.add(job)
        db_session.commit()

        # Create active job source
        job_source = JobSource(
            job_id=job.id,
            source_platform="Indeed",
            source_url="https://www.indeed.com/viewjob?jk=active",
            is_active=True
        )
        db_session.add(job_source)
        db_session.commit()

        assert job_source.is_active is True

        # Mark as inactive
        job_source.mark_inactive()
        db_session.commit()

        # Verify status changed
        assert job_source.is_active is False

    def test_job_source_repr(self, db_session):
        """Test the string representation of JobSource."""
        # Create a job
        job = Job(
            title="ML Engineer",
            company="AI Labs",
            location="San Jose, CA",
            remote=True,
            job_type=JobType.FULL_TIME,
            experience_level=ExperienceLevel.SENIOR,
            description="Machine learning engineer position.",
            source_type=SourceType.AGGREGATED,
            quality_score=75.0,
            status=JobStatus.ACTIVE,
            posted_at=datetime.now(),
            expires_at=datetime.now() + timedelta(days=30)
        )
        db_session.add(job)
        db_session.commit()

        # Create job source
        job_source = JobSource(
            job_id=job.id,
            source_platform="LinkedIn",
            source_url="https://www.linkedin.com/jobs/view/ml123"
        )
        db_session.add(job_source)
        db_session.commit()

        # Test repr
        repr_str = repr(job_source)
        assert "JobSource" in repr_str
        assert str(job_source.id) in repr_str
        assert str(job.id) in repr_str
        assert "LinkedIn" in repr_str

    def test_source_platform_tracking(self, db_session):
        """Test tracking different source platforms."""
        # Create a job
        job = Job(
            title="Security Engineer",
            company="SecureTech",
            location="Washington, DC",
            remote=False,
            job_type=JobType.FULL_TIME,
            experience_level=ExperienceLevel.LEAD,
            description="Security engineer for enterprise systems.",
            source_type=SourceType.AGGREGATED,
            quality_score=80.0,
            status=JobStatus.ACTIVE,
            posted_at=datetime.now(),
            expires_at=datetime.now() + timedelta(days=30)
        )
        db_session.add(job)
        db_session.commit()

        # Test various platforms
        platforms = ["LinkedIn", "Indeed", "Naukri", "Monster", "Glassdoor"]
        for platform in platforms:
            source = JobSource(
                job_id=job.id,
                source_platform=platform,
                source_url=f"https://www.{platform.lower()}.com/job/test"
            )
            db_session.add(source)
        db_session.commit()

        # Verify all platforms are tracked
        sources = db_session.query(JobSource).filter_by(job_id=job.id).all()
        assert len(sources) == len(platforms)
        assert set(s.source_platform for s in sources) == set(platforms)
