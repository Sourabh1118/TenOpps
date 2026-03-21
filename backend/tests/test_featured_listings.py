"""
Tests for featured listings functionality.

This module tests:
- Task 19.1: Featured listing endpoint
- Task 19.2: Featured jobs in search results
- Task 19.3: Featured listing expiration task

**Validates: Requirements 11.1, 11.2, 11.3, 11.4, 11.5, 11.6, 11.7**
"""
import pytest
from datetime import datetime, timedelta
from uuid import uuid4
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.models.job import Job, JobType, ExperienceLevel, SourceType, JobStatus
from app.models.employer import Employer, SubscriptionTier
from app.core.security import hash_password
from app.tasks.maintenance_tasks import remove_expired_featured_listings


client = TestClient(app)


@pytest.fixture
def test_employer_free(pg_db_session: Session):
    """Create a test employer with free tier."""
    employer = Employer(
        email="free@example.com",
        password_hash=hash_password("password123"),
        company_name="Free Company",
        subscription_tier=SubscriptionTier.FREE,
        subscription_start_date=datetime.utcnow(),
        subscription_end_date=datetime.utcnow() + timedelta(days=30),
        monthly_posts_used=0,
        featured_posts_used=0,
        verified=True
    )
    pg_db_session.add(employer)
    pg_db_session.commit()
    pg_db_session.refresh(employer)
    return employer


@pytest.fixture
def test_employer_basic(pg_db_session: Session):
    """Create a test employer with basic tier."""
    employer = Employer(
        email="basic@example.com",
        password_hash=hash_password("password123"),
        company_name="Basic Company",
        subscription_tier=SubscriptionTier.BASIC,
        subscription_start_date=datetime.utcnow(),
        subscription_end_date=datetime.utcnow() + timedelta(days=30),
        monthly_posts_used=0,
        featured_posts_used=0,
        verified=True
    )
    pg_db_session.add(employer)
    pg_db_session.commit()
    pg_db_session.refresh(employer)
    return employer


@pytest.fixture
def test_employer_premium(pg_db_session: Session):
    """Create a test employer with premium tier."""
    employer = Employer(
        email="premium@example.com",
        password_hash=hash_password("password123"),
        company_name="Premium Company",
        subscription_tier=SubscriptionTier.PREMIUM,
        subscription_start_date=datetime.utcnow(),
        subscription_end_date=datetime.utcnow() + timedelta(days=30),
        monthly_posts_used=0,
        featured_posts_used=0,
        verified=True
    )
    pg_db_session.add(employer)
    pg_db_session.commit()
    pg_db_session.refresh(employer)
    return employer


@pytest.fixture
def test_job(pg_db_session: Session, test_employer_basic):
    """Create a test job."""
    job = Job(
        title="Senior Python Developer",
        company=test_employer_basic.company_name,
        location="San Francisco, CA",
        remote=True,
        job_type=JobType.FULL_TIME,
        experience_level=ExperienceLevel.SENIOR,
        description="We are looking for an experienced Python developer to join our team.",
        source_type=SourceType.DIRECT,
        employer_id=test_employer_basic.id,
        quality_score=85.0,
        status=JobStatus.ACTIVE,
        posted_at=datetime.utcnow(),
        expires_at=datetime.utcnow() + timedelta(days=30),
        featured=False
    )
    pg_db_session.add(job)
    pg_db_session.commit()
    pg_db_session.refresh(job)
    return job


def get_auth_token(email: str, password: str) -> str:
    """Helper to get authentication token."""
    response = client.post(
        "/api/auth/login",
        json={"email": email, "password": password}
    )
    assert response.status_code == 200
    return response.json()["access_token"]


class TestFeaturedListingEndpoint:
    """Tests for Task 19.1: Featured listing endpoint."""
    
    def test_feature_job_success(self, pg_db_session: Session, test_employer_basic, test_job):
        """
        Test successfully featuring a job.
        
        **Validates: Requirements 11.1, 11.2, 11.3, 11.4**
        """
        # Get auth token
        token = get_auth_token("basic@example.com", "password123")
        
        # Feature the job
        response = client.post(
            f"/api/jobs/{test_job.id}/feature",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        assert response.json()["message"] == "Job featured successfully"
        
        # Verify job is featured in database
        pg_db_session.refresh(test_job)
        assert test_job.featured is True
        
        # Verify quota was consumed
        pg_db_session.refresh(test_employer_basic)
        assert test_employer_basic.featured_posts_used == 1
    
    def test_feature_job_not_owner(self, pg_db_session: Session, test_employer_basic, test_employer_premium, test_job):
        """
        Test that employer cannot feature another employer's job.
        
        **Validates: Requirement 11.1**
        """
        # Get auth token for different employer
        token = get_auth_token("premium@example.com", "password123")
        
        # Try to feature the job
        response = client.post(
            f"/api/jobs/{test_job.id}/feature",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 403
        assert "own jobs" in response.json()["detail"]
        
        # Verify job is not featured
        pg_db_session.refresh(test_job)
        assert test_job.featured is False
    
    def test_feature_job_quota_exceeded(self, pg_db_session: Session, test_employer_basic, test_job):
        """
        Test that featuring fails when quota is exceeded.
        
        **Validates: Requirement 11.2**
        """
        # Exhaust featured post quota (basic tier has 2 featured posts)
        test_employer_basic.featured_posts_used = 2
        pg_db_session.commit()
        
        # Get auth token
        token = get_auth_token("basic@example.com", "password123")
        
        # Try to feature the job
        response = client.post(
            f"/api/jobs/{test_job.id}/feature",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 403
        assert "quota exceeded" in response.json()["detail"].lower()
        
        # Verify job is not featured
        pg_db_session.refresh(test_job)
        assert test_job.featured is False
    
    def test_feature_job_free_tier_no_quota(self, pg_db_session: Session, test_employer_free):
        """
        Test that free tier employers cannot feature jobs.
        
        **Validates: Requirement 11.2**
        """
        # Create a job for free tier employer
        job = Job(
            title="Junior Developer",
            company=test_employer_free.company_name,
            location="Remote",
            remote=True,
            job_type=JobType.FULL_TIME,
            experience_level=ExperienceLevel.ENTRY,
            description="Entry level position for junior developers.",
            source_type=SourceType.DIRECT,
            employer_id=test_employer_free.id,
            quality_score=70.0,
            status=JobStatus.ACTIVE,
            posted_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(days=30),
            featured=False
        )
        pg_db_session.add(job)
        pg_db_session.commit()
        pg_db_session.refresh(job)
        
        # Get auth token
        token = get_auth_token("free@example.com", "password123")
        
        # Try to feature the job
        response = client.post(
            f"/api/jobs/{job.id}/feature",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 403
        assert "quota exceeded" in response.json()["detail"].lower()
        
        # Verify job is not featured
        pg_db_session.refresh(job)
        assert job.featured is False
    
    def test_feature_job_already_featured(self, pg_db_session: Session, test_employer_basic, test_job):
        """Test that featuring an already featured job returns error."""
        # Set job as featured
        test_job.featured = True
        pg_db_session.commit()
        
        # Get auth token
        token = get_auth_token("basic@example.com", "password123")
        
        # Try to feature the job again
        response = client.post(
            f"/api/jobs/{test_job.id}/feature",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 400
        assert "already featured" in response.json()["detail"].lower()
    
    def test_feature_job_not_found(self, pg_db_session: Session, test_employer_basic):
        """Test featuring a non-existent job."""
        # Get auth token
        token = get_auth_token("basic@example.com", "password123")
        
        # Try to feature non-existent job
        fake_job_id = uuid4()
        response = client.post(
            f"/api/jobs/{fake_job_id}/feature",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestFeaturedJobsInSearch:
    """Tests for Task 19.2: Featured jobs in search results."""
    
    def test_featured_jobs_prioritized(self, pg_db_session: Session, test_employer_basic):
        """
        Test that featured jobs appear before non-featured jobs in search.
        
        **Validates: Requirement 11.5**
        """
        # Create multiple jobs with different featured status
        jobs = []
        for i in range(5):
            job = Job(
                title=f"Software Engineer {i}",
                company=test_employer_basic.company_name,
                location="San Francisco, CA",
                remote=True,
                job_type=JobType.FULL_TIME,
                experience_level=ExperienceLevel.MID,
                description="Looking for a software engineer to join our team.",
                source_type=SourceType.DIRECT,
                employer_id=test_employer_basic.id,
                quality_score=80.0 + i,  # Varying quality scores
                status=JobStatus.ACTIVE,
                posted_at=datetime.utcnow() - timedelta(days=i),
                expires_at=datetime.utcnow() + timedelta(days=30),
                featured=(i % 2 == 0)  # Feature every other job
            )
            pg_db_session.add(job)
            jobs.append(job)
        
        pg_db_session.commit()
        
        # Search for jobs
        response = client.get("/api/jobs/search?query=software+engineer")
        
        assert response.status_code == 200
        results = response.json()
        
        # Verify featured jobs come first
        featured_jobs = [j for j in results["jobs"] if j["featured"]]
        non_featured_jobs = [j for j in results["jobs"] if not j["featured"]]
        
        assert len(featured_jobs) == 3  # Jobs 0, 2, 4
        assert len(non_featured_jobs) == 2  # Jobs 1, 3
        
        # Verify all featured jobs appear before non-featured jobs
        featured_indices = [i for i, j in enumerate(results["jobs"]) if j["featured"]]
        non_featured_indices = [i for i, j in enumerate(results["jobs"]) if not j["featured"]]
        
        if featured_indices and non_featured_indices:
            assert max(featured_indices) < min(non_featured_indices)
    
    def test_featured_flag_in_response(self, pg_db_session: Session, test_employer_basic, test_job):
        """
        Test that featured flag is included in search results.
        
        **Validates: Requirement 11.6**
        """
        # Set job as featured
        test_job.featured = True
        pg_db_session.commit()
        
        # Search for the job
        response = client.get(f"/api/jobs/search?query={test_job.title}")
        
        assert response.status_code == 200
        results = response.json()
        
        # Find the job in results
        job_result = next((j for j in results["jobs"] if j["id"] == str(test_job.id)), None)
        
        assert job_result is not None
        assert "featured" in job_result
        assert job_result["featured"] is True
    
    def test_featured_jobs_sorted_by_quality(self, pg_db_session: Session, test_employer_basic):
        """
        Test that featured jobs are sorted by quality score among themselves.
        
        **Validates: Requirement 11.5**
        """
        # Create multiple featured jobs with different quality scores
        jobs = []
        for i in range(3):
            job = Job(
                title=f"Featured Job {i}",
                company=test_employer_basic.company_name,
                location="Remote",
                remote=True,
                job_type=JobType.FULL_TIME,
                experience_level=ExperienceLevel.SENIOR,
                description="Featured job posting for senior developers.",
                source_type=SourceType.DIRECT,
                employer_id=test_employer_basic.id,
                quality_score=70.0 + (i * 10),  # 70, 80, 90
                status=JobStatus.ACTIVE,
                posted_at=datetime.utcnow(),
                expires_at=datetime.utcnow() + timedelta(days=30),
                featured=True
            )
            pg_db_session.add(job)
            jobs.append(job)
        
        pg_db_session.commit()
        
        # Search for jobs
        response = client.get("/api/jobs/search?query=featured+job")
        
        assert response.status_code == 200
        results = response.json()
        
        # Verify featured jobs are sorted by quality score descending
        featured_jobs = [j for j in results["jobs"] if j["featured"]]
        quality_scores = [j["qualityScore"] for j in featured_jobs]
        
        assert quality_scores == sorted(quality_scores, reverse=True)


class TestFeaturedListingExpiration:
    """Tests for Task 19.3: Featured listing expiration task."""
    
    def test_remove_expired_featured_listings(self, pg_db_session: Session, test_employer_basic):
        """
        Test that expired featured listings have featured flag removed.
        
        **Validates: Requirement 11.7**
        """
        # Create featured jobs with different expiration dates
        expired_job = Job(
            title="Expired Featured Job",
            company=test_employer_basic.company_name,
            location="San Francisco, CA",
            remote=True,
            job_type=JobType.FULL_TIME,
            experience_level=ExperienceLevel.SENIOR,
            description="This is an expired featured job posting.",
            source_type=SourceType.DIRECT,
            employer_id=test_employer_basic.id,
            quality_score=85.0,
            status=JobStatus.ACTIVE,
            posted_at=datetime.utcnow() - timedelta(days=35),
            expires_at=datetime.utcnow() - timedelta(days=5),  # Expired 5 days ago
            featured=True
        )
        
        active_job = Job(
            title="Active Featured Job",
            company=test_employer_basic.company_name,
            location="San Francisco, CA",
            remote=True,
            job_type=JobType.FULL_TIME,
            experience_level=ExperienceLevel.SENIOR,
            description="This is an active featured job posting.",
            source_type=SourceType.DIRECT,
            employer_id=test_employer_basic.id,
            quality_score=85.0,
            status=JobStatus.ACTIVE,
            posted_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(days=25),  # Still active
            featured=True
        )
        
        pg_db_session.add(expired_job)
        pg_db_session.add(active_job)
        pg_db_session.commit()
        
        # Run the expiration task
        result = remove_expired_featured_listings()
        
        assert result["status"] == "success"
        assert result["featured_removed"] == 1
        
        # Verify expired job is no longer featured
        pg_db_session.refresh(expired_job)
        assert expired_job.featured is False
        
        # Verify active job is still featured
        pg_db_session.refresh(active_job)
        assert active_job.featured is True
    
    def test_expiration_task_no_expired_jobs(self, pg_db_session: Session, test_employer_basic):
        """Test expiration task when there are no expired featured jobs."""
        # Create only active featured jobs
        job = Job(
            title="Active Featured Job",
            company=test_employer_basic.company_name,
            location="Remote",
            remote=True,
            job_type=JobType.FULL_TIME,
            experience_level=ExperienceLevel.MID,
            description="Active featured job posting.",
            source_type=SourceType.DIRECT,
            employer_id=test_employer_basic.id,
            quality_score=80.0,
            status=JobStatus.ACTIVE,
            posted_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(days=30),
            featured=True
        )
        pg_db_session.add(job)
        pg_db_session.commit()
        
        # Run the expiration task
        result = remove_expired_featured_listings()
        
        assert result["status"] == "success"
        assert result["featured_removed"] == 0
        
        # Verify job is still featured
        pg_db_session.refresh(job)
        assert job.featured is True
    
    def test_expiration_task_multiple_expired_jobs(self, pg_db_session: Session, test_employer_basic):
        """Test expiration task with multiple expired featured jobs."""
        # Create multiple expired featured jobs
        expired_jobs = []
        for i in range(3):
            job = Job(
                title=f"Expired Job {i}",
                company=test_employer_basic.company_name,
                location="Remote",
                remote=True,
                job_type=JobType.FULL_TIME,
                experience_level=ExperienceLevel.SENIOR,
                description=f"Expired featured job {i}.",
                source_type=SourceType.DIRECT,
                employer_id=test_employer_basic.id,
                quality_score=85.0,
                status=JobStatus.ACTIVE,
                posted_at=datetime.utcnow() - timedelta(days=40),
                expires_at=datetime.utcnow() - timedelta(days=i + 1),  # All expired
                featured=True
            )
            pg_db_session.add(job)
            expired_jobs.append(job)
        
        pg_db_session.commit()
        
        # Run the expiration task
        result = remove_expired_featured_listings()
        
        assert result["status"] == "success"
        assert result["featured_removed"] == 3
        
        # Verify all jobs are no longer featured
        for job in expired_jobs:
            pg_db_session.refresh(job)
            assert job.featured is False
    
    def test_expiration_task_ignores_non_featured_expired_jobs(self, pg_db_session: Session, test_employer_basic):
        """Test that expiration task only affects featured jobs."""
        # Create expired non-featured job
        non_featured_job = Job(
            title="Expired Non-Featured Job",
            company=test_employer_basic.company_name,
            location="Remote",
            remote=True,
            job_type=JobType.FULL_TIME,
            experience_level=ExperienceLevel.MID,
            description="Expired non-featured job.",
            source_type=SourceType.DIRECT,
            employer_id=test_employer_basic.id,
            quality_score=75.0,
            status=JobStatus.ACTIVE,
            posted_at=datetime.utcnow() - timedelta(days=35),
            expires_at=datetime.utcnow() - timedelta(days=5),  # Expired
            featured=False
        )
        
        # Create expired featured job
        featured_job = Job(
            title="Expired Featured Job",
            company=test_employer_basic.company_name,
            location="Remote",
            remote=True,
            job_type=JobType.FULL_TIME,
            experience_level=ExperienceLevel.SENIOR,
            description="Expired featured job.",
            source_type=SourceType.DIRECT,
            employer_id=test_employer_basic.id,
            quality_score=85.0,
            status=JobStatus.ACTIVE,
            posted_at=datetime.utcnow() - timedelta(days=35),
            expires_at=datetime.utcnow() - timedelta(days=5),  # Expired
            featured=True
        )
        
        pg_db_session.add(non_featured_job)
        pg_db_session.add(featured_job)
        pg_db_session.commit()
        
        # Run the expiration task
        result = remove_expired_featured_listings()
        
        assert result["status"] == "success"
        assert result["featured_removed"] == 1
        
        # Verify featured job is no longer featured
        pg_db_session.refresh(featured_job)
        assert featured_job.featured is False
        
        # Verify non-featured job remains unchanged
        pg_db_session.refresh(non_featured_job)
        assert non_featured_job.featured is False
