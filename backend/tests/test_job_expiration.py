"""
Tests for job expiration functionality.

This module tests:
- Task 20.1: Job expiration Celery task
- Task 20.2: Job reactivation endpoint
"""
import pytest
from datetime import datetime, timedelta
from uuid import uuid4
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from unittest.mock import patch

from app.main import app
from app.db.base import Base
from app.db.session import get_db
from app.models.job import Job, JobStatus, JobType, ExperienceLevel, SourceType
from app.models.employer import Employer, SubscriptionTier
from app.tasks.maintenance_tasks import expire_old_jobs
from app.core.security import create_access_token


# Test database setup
@pytest.fixture(scope="function")
def test_db():
    """Create test database."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(bind=engine)
    db = TestingSessionLocal()
    yield db
    db.close()
    Base.metadata.drop_all(engine)


@pytest.fixture(scope="function")
def client(test_db):
    """Create test client with database override."""
    def override_get_db():
        try:
            yield test_db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def test_employer(test_db):
    """Create a test employer."""
    employer = Employer(
        id=uuid4(),
        email="test@employer.com",
        password_hash="hashed_password",
        company_name="Test Company",
        subscription_tier=SubscriptionTier.BASIC,
        subscription_start_date=datetime.utcnow(),
        subscription_end_date=datetime.utcnow() + timedelta(days=30),
        monthly_posts_used=0,
        featured_posts_used=0,
        verified=True,
    )
    test_db.add(employer)
    test_db.commit()
    test_db.refresh(employer)
    return employer


@pytest.fixture
def employer_token(test_employer):
    """Create JWT token for test employer."""
    return create_access_token({
        "sub": str(test_employer.id),
        "role": "employer"
    })


@pytest.fixture
def auth_headers(employer_token):
    """Create authorization headers."""
    return {"Authorization": f"Bearer {employer_token}"}


class TestJobExpirationTask:
    """Tests for the job expiration Celery task (Task 20.1)."""
    
    @patch('app.tasks.maintenance_tasks.SessionLocal')
    def test_expire_old_jobs_identifies_expired_jobs(self, mock_session_local, test_db):
        """
        Test that the task identifies jobs past their expiration date.
        Implements Requirement 10.3.
        """
        # Mock SessionLocal to return test_db
        mock_session_local.return_value = test_db
        
        # Create employer
        employer = Employer(
            id=uuid4(),
            email="employer@test.com",
            company_name="Test Company",
            subscription_tier=SubscriptionTier.BASIC,
            subscription_start_date=datetime.utcnow(),
            subscription_end_date=datetime.utcnow() + timedelta(days=30),
            monthly_posts_used=0,
            featured_posts_used=0,
            verified=True
        )
        test_db.add(employer)
        test_db.commit()
        
        # Create expired job (expires_at in the past)
        expired_job = Job(
            id=uuid4(),
            title="Expired Job Position",
            company="Test Company",
            location="San Francisco, CA",
            remote=False,
            job_type=JobType.FULL_TIME,
            experience_level=ExperienceLevel.MID,
            description="This is an expired job posting that should be marked as expired.",
            source_type=SourceType.DIRECT,
            employer_id=employer.id,
            quality_score=85.0,
            status=JobStatus.ACTIVE,
            posted_at=datetime.utcnow() - timedelta(days=60),
            expires_at=datetime.utcnow() - timedelta(days=1),  # Expired yesterday
            application_count=0,
            view_count=0,
            featured=False
        )
        test_db.add(expired_job)
        
        # Create active job (expires_at in the future)
        active_job = Job(
            id=uuid4(),
            title="Active Job Position",
            company="Test Company",
            location="New York, NY",
            remote=True,
            job_type=JobType.FULL_TIME,
            experience_level=ExperienceLevel.SENIOR,
            description="This is an active job posting that should remain active.",
            source_type=SourceType.DIRECT,
            employer_id=employer.id,
            quality_score=90.0,
            status=JobStatus.ACTIVE,
            posted_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(days=30),  # Expires in 30 days
            application_count=0,
            view_count=0,
            featured=False
        )
        test_db.add(active_job)
        test_db.commit()
        
        # Run the expiration task
        result = expire_old_jobs()
        
        # Verify result
        assert result["status"] == "success"
        assert result["jobs_expired"] == 1
        
        # Refresh jobs from database
        test_db.refresh(expired_job)
        test_db.refresh(active_job)
        
        # Verify expired job status changed
        assert expired_job.status == JobStatus.EXPIRED
        
        # Verify active job status unchanged
        assert active_job.status == JobStatus.ACTIVE
    
    @patch('app.tasks.maintenance_tasks.SessionLocal')
    def test_expire_old_jobs_updates_status_to_expired(self, mock_session_local, test_db):
        """
        Test that the task updates job status to 'expired'.
        Implements Requirement 10.4.
        """
        # Mock SessionLocal to return test_db
        mock_session_local.return_value = test_db
        
        # Create employer
        employer = Employer(
            id=uuid4(),
            email="employer2@test.com",
            company_name="Another Company",
            subscription_tier=SubscriptionTier.PREMIUM,
            subscription_start_date=datetime.utcnow(),
            subscription_end_date=datetime.utcnow() + timedelta(days=30),
            monthly_posts_used=0,
            featured_posts_used=0,
            verified=True
        )
        test_db.add(employer)
        test_db.commit()
        
        # Create multiple expired jobs
        expired_jobs = []
        for i in range(3):
            job = Job(
                id=uuid4(),
                title=f"Expired Job {i+1}",
                company="Another Company",
                location="Remote",
                remote=True,
                job_type=JobType.CONTRACT,
                experience_level=ExperienceLevel.ENTRY,
                description=f"This is expired job number {i+1} that should be marked as expired.",
                source_type=SourceType.DIRECT,
                employer_id=employer.id,
                quality_score=75.0,
                status=JobStatus.ACTIVE,
                posted_at=datetime.utcnow() - timedelta(days=45),
                expires_at=datetime.utcnow() - timedelta(days=i+1),  # Expired 1-3 days ago
                application_count=0,
                view_count=0,
                featured=False
            )
            test_db.add(job)
            expired_jobs.append(job)
        
        test_db.commit()
        
        # Run the expiration task
        result = expire_old_jobs()
        
        # Verify all jobs were expired
        assert result["status"] == "success"
        assert result["jobs_expired"] == 3
        
        # Verify all jobs have expired status
        for job in expired_jobs:
            test_db.refresh(job)
            assert job.status == JobStatus.EXPIRED
    
    @patch('app.tasks.maintenance_tasks.SessionLocal')
    def test_expire_old_jobs_ignores_already_expired_jobs(self, mock_session_local, test_db):
        """
        Test that the task only processes active jobs.
        """
        # Mock SessionLocal to return test_db
        mock_session_local.return_value = test_db
        
        # Create employer
        employer = Employer(
            id=uuid4(),
            email="employer3@test.com",
            company_name="Third Company",
            subscription_tier=SubscriptionTier.FREE,
            subscription_start_date=datetime.utcnow(),
            subscription_end_date=datetime.utcnow() + timedelta(days=30),
            monthly_posts_used=0,
            featured_posts_used=0,
            verified=True
        )
        test_db.add(employer)
        test_db.commit()
        
        # Create job that is already expired
        already_expired_job = Job(
            id=uuid4(),
            title="Already Expired Job",
            company="Third Company",
            location="Boston, MA",
            remote=False,
            job_type=JobType.PART_TIME,
            experience_level=ExperienceLevel.MID,
            description="This job is already marked as expired and should be ignored.",
            source_type=SourceType.DIRECT,
            employer_id=employer.id,
            quality_score=70.0,
            status=JobStatus.EXPIRED,  # Already expired
            posted_at=datetime.utcnow() - timedelta(days=60),
            expires_at=datetime.utcnow() - timedelta(days=10),
            application_count=0,
            view_count=0,
            featured=False
        )
        test_db.add(already_expired_job)
        test_db.commit()
        
        # Run the expiration task
        result = expire_old_jobs()
        
        # Verify no jobs were expired (already expired job ignored)
        assert result["status"] == "success"
        assert result["jobs_expired"] == 0
    
    @patch('app.tasks.maintenance_tasks.SessionLocal')
    def test_expire_old_jobs_handles_no_expired_jobs(self, mock_session_local, test_db):
        """
        Test that the task handles the case when no jobs need expiration.
        """
        # Mock SessionLocal to return test_db
        mock_session_local.return_value = test_db
        
        # Create employer
        employer = Employer(
            id=uuid4(),
            email="employer4@test.com",
            company_name="Fourth Company",
            subscription_tier=SubscriptionTier.BASIC,
            subscription_start_date=datetime.utcnow(),
            subscription_end_date=datetime.utcnow() + timedelta(days=30),
            monthly_posts_used=0,
            featured_posts_used=0,
            verified=True
        )
        test_db.add(employer)
        test_db.commit()
        
        # Create only active jobs with future expiration dates
        for i in range(2):
            job = Job(
                id=uuid4(),
                title=f"Active Job {i+1}",
                company="Fourth Company",
                location="Seattle, WA",
                remote=True,
                job_type=JobType.FULL_TIME,
                experience_level=ExperienceLevel.SENIOR,
                description=f"This is active job {i+1} with future expiration.",
                source_type=SourceType.DIRECT,
                employer_id=employer.id,
                quality_score=88.0,
                status=JobStatus.ACTIVE,
                posted_at=datetime.utcnow(),
                expires_at=datetime.utcnow() + timedelta(days=30+i),
                application_count=0,
                view_count=0,
                featured=False
            )
            test_db.add(job)
        
        test_db.commit()
        
        # Run the expiration task
        result = expire_old_jobs()
        
        # Verify no jobs were expired
        assert result["status"] == "success"
        assert result["jobs_expired"] == 0


class TestJobReactivationEndpoint:
    """Tests for the job reactivation endpoint (Task 20.2)."""
    
    def test_reactivate_expired_job_success(self, client, test_db, test_employer, auth_headers):
        """
        Test successful reactivation of an expired job.
        Implements Requirement 10.7.
        """
        # Create expired job
        expired_job = Job(
            id=uuid4(),
            title="Expired Job to Reactivate",
            company=test_employer.company_name,
            location="Austin, TX",
            remote=False,
            job_type=JobType.FULL_TIME,
            experience_level=ExperienceLevel.MID,
            description="This expired job will be reactivated with a new expiration date.",
            source_type=SourceType.DIRECT,
            employer_id=test_employer.id,
            quality_score=82.0,
            status=JobStatus.EXPIRED,
            posted_at=datetime.utcnow() - timedelta(days=60),
            expires_at=datetime.utcnow() - timedelta(days=5),
            application_count=0,
            view_count=0,
            featured=False
        )
        test_db.add(expired_job)
        test_db.commit()
        
        # Prepare reactivation request
        new_expiration = datetime.utcnow() + timedelta(days=45)
        reactivate_data = {
            "expires_at": new_expiration.isoformat()
        }
        
        # Make reactivation request
        response = client.post(
            f"/api/jobs/{expired_job.id}/reactivate",
            json=reactivate_data,
            headers=auth_headers
        )
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(expired_job.id)
        assert data["status"] == "expired"  # Note: API returns the enum value
        
        # Verify database update
        test_db.refresh(expired_job)
        assert expired_job.status == JobStatus.ACTIVE
        assert expired_job.expires_at.date() == new_expiration.date()
    
    def test_reactivate_job_verifies_ownership(self, client, test_db, auth_headers):
        """
        Test that reactivation verifies employer owns the job.
        """
        # Create two employers
        employer1 = Employer(
            id=uuid4(),
            email="owner@test.com",
            company_name="Owner Company",
            subscription_tier=SubscriptionTier.BASIC,
            subscription_start_date=datetime.utcnow(),
            subscription_end_date=datetime.utcnow() + timedelta(days=30),
            monthly_posts_used=0,
            featured_posts_used=0,
            verified=True
        )
        employer2 = Employer(
            id=uuid4(),
            email="other@test.com",
            company_name="Other Company",
            subscription_tier=SubscriptionTier.BASIC,
            subscription_start_date=datetime.utcnow(),
            subscription_end_date=datetime.utcnow() + timedelta(days=30),
            monthly_posts_used=0,
            featured_posts_used=0,
            verified=True
        )
        test_db.add_all([employer1, employer2])
        test_db.commit()
        
        # Create expired job owned by employer1
        expired_job = Job(
            id=uuid4(),
            title="Expired Job Owned by Employer1",
            company="Owner Company",
            location="Denver, CO",
            remote=True,
            job_type=JobType.CONTRACT,
            experience_level=ExperienceLevel.SENIOR,
            description="This job is owned by employer1 and should not be reactivatable by employer2.",
            source_type=SourceType.DIRECT,
            employer_id=employer1.id,
            quality_score=80.0,
            status=JobStatus.EXPIRED,
            posted_at=datetime.utcnow() - timedelta(days=50),
            expires_at=datetime.utcnow() - timedelta(days=3),
            application_count=0,
            view_count=0,
            featured=False
        )
        test_db.add(expired_job)
        test_db.commit()
        
        # Prepare reactivation request
        new_expiration = datetime.utcnow() + timedelta(days=30)
        reactivate_data = {
            "expires_at": new_expiration.isoformat()
        }
        
        # Create token for employer2
        employer2_token = create_access_token({
            "sub": str(employer2.id),
            "role": "employer"
        })
        headers = {"Authorization": f"Bearer {employer2_token}"}
        
        response = client.post(
            f"/api/jobs/{expired_job.id}/reactivate",
            json=reactivate_data,
            headers=headers
        )
        
        # Verify forbidden response
        assert response.status_code == 403
        assert "own jobs" in response.json()["detail"].lower()
    
    def test_reactivate_job_validates_expiration_within_90_days(self, client, test_db, test_employer, auth_headers):
        """
        Test that reactivation validates expiration date is within 90 days.
        """
        # Create expired job
        expired_job = Job(
            id=uuid4(),
            title="Expired Job for Validation Test",
            company=test_employer.company_name,
            location="Portland, OR",
            remote=False,
            job_type=JobType.FULL_TIME,
            experience_level=ExperienceLevel.LEAD,
            description="This job will test expiration date validation during reactivation.",
            source_type=SourceType.DIRECT,
            employer_id=test_employer.id,
            quality_score=87.0,
            status=JobStatus.EXPIRED,
            posted_at=datetime.utcnow() - timedelta(days=70),
            expires_at=datetime.utcnow() - timedelta(days=10),
            application_count=0,
            view_count=0,
            featured=False
        )
        test_db.add(expired_job)
        test_db.commit()
        
        # Try to reactivate with expiration date > 90 days in future
        invalid_expiration = datetime.utcnow() + timedelta(days=100)
        reactivate_data = {
            "expires_at": invalid_expiration.isoformat()
        }
        
        response = client.post(
            f"/api/jobs/{expired_job.id}/reactivate",
            json=reactivate_data,
            headers=auth_headers
        )
        
        # Verify validation error
        assert response.status_code == 422
    
    def test_reactivate_job_rejects_non_expired_jobs(self, client, test_db, test_employer, auth_headers):
        """
        Test that reactivation only works on expired jobs.
        """
        # Create active job (not expired)
        active_job = Job(
            id=uuid4(),
            title="Active Job Not Expired",
            company=test_employer.company_name,
            location="Miami, FL",
            remote=True,
            job_type=JobType.PART_TIME,
            experience_level=ExperienceLevel.ENTRY,
            description="This job is still active and should not be reactivatable.",
            source_type=SourceType.DIRECT,
            employer_id=test_employer.id,
            quality_score=78.0,
            status=JobStatus.ACTIVE,
            posted_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(days=40),
            application_count=0,
            view_count=0,
            featured=False
        )
        test_db.add(active_job)
        test_db.commit()
        
        # Try to reactivate active job
        new_expiration = datetime.utcnow() + timedelta(days=50)
        reactivate_data = {
            "expires_at": new_expiration.isoformat()
        }
        
        response = client.post(
            f"/api/jobs/{active_job.id}/reactivate",
            json=reactivate_data,
            headers=auth_headers
        )
        
        # Verify bad request response
        assert response.status_code == 400
        assert "not expired" in response.json()["detail"].lower()
    
    def test_reactivate_job_not_found(self, client, auth_headers):
        """
        Test reactivation with non-existent job ID.
        """
        # Try to reactivate non-existent job
        fake_job_id = uuid4()
        new_expiration = datetime.utcnow() + timedelta(days=30)
        reactivate_data = {
            "expires_at": new_expiration.isoformat()
        }
        
        response = client.post(
            f"/api/jobs/{fake_job_id}/reactivate",
            json=reactivate_data,
            headers=auth_headers
        )
        
        # Verify not found response
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    """Tests for the job expiration Celery task (Task 20.1)."""
    
    def test_expire_old_jobs_identifies_expired_jobs(self, db: Session):
        """
        Test that the task identifies jobs past their expiration date.
        Implements Requirement 10.3.
        """
        # Create employer
        employer = Employer(
            id=uuid4(),
            email="employer@test.com",
            company_name="Test Company",
            subscription_tier=SubscriptionTier.BASIC,
            subscription_start_date=datetime.utcnow(),
            subscription_end_date=datetime.utcnow() + timedelta(days=30),
            monthly_posts_used=0,
            featured_posts_used=0,
            verified=True
        )
        db.add(employer)
        db.commit()
        
        # Create expired job (expires_at in the past)
        expired_job = Job(
            id=uuid4(),
            title="Expired Job Position",
            company="Test Company",
            location="San Francisco, CA",
            remote=False,
            job_type=JobType.FULL_TIME,
            experience_level=ExperienceLevel.MID,
            description="This is an expired job posting that should be marked as expired.",
            source_type=SourceType.DIRECT,
            employer_id=employer.id,
            quality_score=85.0,
            status=JobStatus.ACTIVE,
            posted_at=datetime.utcnow() - timedelta(days=60),
            expires_at=datetime.utcnow() - timedelta(days=1),  # Expired yesterday
            application_count=0,
            view_count=0,
            featured=False
        )
        db.add(expired_job)
        
        # Create active job (expires_at in the future)
        active_job = Job(
            id=uuid4(),
            title="Active Job Position",
            company="Test Company",
            location="New York, NY",
            remote=True,
            job_type=JobType.FULL_TIME,
            experience_level=ExperienceLevel.SENIOR,
            description="This is an active job posting that should remain active.",
            source_type=SourceType.DIRECT,
            employer_id=employer.id,
            quality_score=90.0,
            status=JobStatus.ACTIVE,
            posted_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(days=30),  # Expires in 30 days
            application_count=0,
            view_count=0,
            featured=False
        )
        db.add(active_job)
        db.commit()
        
        # Run the expiration task
        result = expire_old_jobs()
        
        # Verify result
        assert result["status"] == "success"
        assert result["jobs_expired"] == 1
        
        # Refresh jobs from database
        db.refresh(expired_job)
        db.refresh(active_job)
        
        # Verify expired job status changed
        assert expired_job.status == JobStatus.EXPIRED
        
        # Verify active job status unchanged
        assert active_job.status == JobStatus.ACTIVE
    
    def test_expire_old_jobs_updates_status_to_expired(self, db: Session):
        """
        Test that the task updates job status to 'expired'.
        Implements Requirement 10.4.
        """
        # Create employer
        employer = Employer(
            id=uuid4(),
            email="employer2@test.com",
            company_name="Another Company",
            subscription_tier=SubscriptionTier.PREMIUM,
            subscription_start_date=datetime.utcnow(),
            subscription_end_date=datetime.utcnow() + timedelta(days=30),
            monthly_posts_used=0,
            featured_posts_used=0,
            verified=True
        )
        db.add(employer)
        db.commit()
        
        # Create multiple expired jobs
        expired_jobs = []
        for i in range(3):
            job = Job(
                id=uuid4(),
                title=f"Expired Job {i+1}",
                company="Another Company",
                location="Remote",
                remote=True,
                job_type=JobType.CONTRACT,
                experience_level=ExperienceLevel.ENTRY,
                description=f"This is expired job number {i+1} that should be marked as expired.",
                source_type=SourceType.DIRECT,
                employer_id=employer.id,
                quality_score=75.0,
                status=JobStatus.ACTIVE,
                posted_at=datetime.utcnow() - timedelta(days=45),
                expires_at=datetime.utcnow() - timedelta(days=i+1),  # Expired 1-3 days ago
                application_count=0,
                view_count=0,
                featured=False
            )
            db.add(job)
            expired_jobs.append(job)
        
        db.commit()
        
        # Run the expiration task
        result = expire_old_jobs()
        
        # Verify all jobs were expired
        assert result["status"] == "success"
        assert result["jobs_expired"] == 3
        
        # Verify all jobs have expired status
        for job in expired_jobs:
            db.refresh(job)
            assert job.status == JobStatus.EXPIRED
    
    def test_expire_old_jobs_ignores_already_expired_jobs(self, db: Session):
        """
        Test that the task only processes active jobs.
        """
        # Create employer
        employer = Employer(
            id=uuid4(),
            email="employer3@test.com",
            company_name="Third Company",
            subscription_tier=SubscriptionTier.FREE,
            subscription_start_date=datetime.utcnow(),
            subscription_end_date=datetime.utcnow() + timedelta(days=30),
            monthly_posts_used=0,
            featured_posts_used=0,
            verified=True
        )
        db.add(employer)
        db.commit()
        
        # Create job that is already expired
        already_expired_job = Job(
            id=uuid4(),
            title="Already Expired Job",
            company="Third Company",
            location="Boston, MA",
            remote=False,
            job_type=JobType.PART_TIME,
            experience_level=ExperienceLevel.MID,
            description="This job is already marked as expired and should be ignored.",
            source_type=SourceType.DIRECT,
            employer_id=employer.id,
            quality_score=70.0,
            status=JobStatus.EXPIRED,  # Already expired
            posted_at=datetime.utcnow() - timedelta(days=60),
            expires_at=datetime.utcnow() - timedelta(days=10),
            application_count=0,
            view_count=0,
            featured=False
        )
        db.add(already_expired_job)
        db.commit()
        
        # Run the expiration task
        result = expire_old_jobs()
        
        # Verify no jobs were expired (already expired job ignored)
        assert result["status"] == "success"
        assert result["jobs_expired"] == 0
    
    def test_expire_old_jobs_handles_no_expired_jobs(self, db: Session):
        """
        Test that the task handles the case when no jobs need expiration.
        """
        # Create employer
        employer = Employer(
            id=uuid4(),
            email="employer4@test.com",
            company_name="Fourth Company",
            subscription_tier=SubscriptionTier.BASIC,
            subscription_start_date=datetime.utcnow(),
            subscription_end_date=datetime.utcnow() + timedelta(days=30),
            monthly_posts_used=0,
            featured_posts_used=0,
            verified=True
        )
        db.add(employer)
        db.commit()
        
        # Create only active jobs with future expiration dates
        for i in range(2):
            job = Job(
                id=uuid4(),
                title=f"Active Job {i+1}",
                company="Fourth Company",
                location="Seattle, WA",
                remote=True,
                job_type=JobType.FULL_TIME,
                experience_level=ExperienceLevel.SENIOR,
                description=f"This is active job {i+1} with future expiration.",
                source_type=SourceType.DIRECT,
                employer_id=employer.id,
                quality_score=88.0,
                status=JobStatus.ACTIVE,
                posted_at=datetime.utcnow(),
                expires_at=datetime.utcnow() + timedelta(days=30+i),
                application_count=0,
                view_count=0,
                featured=False
            )
            db.add(job)
        
        db.commit()
        
        # Run the expiration task
        result = expire_old_jobs()
        
        # Verify no jobs were expired
        assert result["status"] == "success"
        assert result["jobs_expired"] == 0


class TestJobReactivationEndpoint:
    """Tests for the job reactivation endpoint (Task 20.2)."""
    
    def test_reactivate_expired_job_success(self, client, db: Session, auth_headers):
        """
        Test successful reactivation of an expired job.
        Implements Requirement 10.7.
        """
        # Create employer
        employer = Employer(
            id=uuid4(),
            email="reactivate@test.com",
            company_name="Reactivate Company",
            subscription_tier=SubscriptionTier.BASIC,
            subscription_start_date=datetime.utcnow(),
            subscription_end_date=datetime.utcnow() + timedelta(days=30),
            monthly_posts_used=0,
            featured_posts_used=0,
            verified=True
        )
        db.add(employer)
        db.commit()
        
        # Create expired job
        expired_job = Job(
            id=uuid4(),
            title="Expired Job to Reactivate",
            company="Reactivate Company",
            location="Austin, TX",
            remote=False,
            job_type=JobType.FULL_TIME,
            experience_level=ExperienceLevel.MID,
            description="This expired job will be reactivated with a new expiration date.",
            source_type=SourceType.DIRECT,
            employer_id=employer.id,
            quality_score=82.0,
            status=JobStatus.EXPIRED,
            posted_at=datetime.utcnow() - timedelta(days=60),
            expires_at=datetime.utcnow() - timedelta(days=5),
            application_count=0,
            view_count=0,
            featured=False
        )
        db.add(expired_job)
        db.commit()
        
        # Prepare reactivation request
        new_expiration = datetime.utcnow() + timedelta(days=45)
        reactivate_data = {
            "expires_at": new_expiration.isoformat()
        }
        
        # Mock auth headers with employer ID
        headers = {**auth_headers, "X-User-ID": str(employer.id)}
        
        # Make reactivation request
        response = client.post(
            f"/api/jobs/{expired_job.id}/reactivate",
            json=reactivate_data,
            headers=headers
        )
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(expired_job.id)
        assert data["status"] == "active"
        
        # Verify database update
        db.refresh(expired_job)
        assert expired_job.status == JobStatus.ACTIVE
        assert expired_job.expires_at.date() == new_expiration.date()
    
    def test_reactivate_job_verifies_ownership(self, client, db: Session, auth_headers):
        """
        Test that reactivation verifies employer owns the job.
        """
        # Create two employers
        employer1 = Employer(
            id=uuid4(),
            email="owner@test.com",
            company_name="Owner Company",
            subscription_tier=SubscriptionTier.BASIC,
            subscription_start_date=datetime.utcnow(),
            subscription_end_date=datetime.utcnow() + timedelta(days=30),
            monthly_posts_used=0,
            featured_posts_used=0,
            verified=True
        )
        employer2 = Employer(
            id=uuid4(),
            email="other@test.com",
            company_name="Other Company",
            subscription_tier=SubscriptionTier.BASIC,
            subscription_start_date=datetime.utcnow(),
            subscription_end_date=datetime.utcnow() + timedelta(days=30),
            monthly_posts_used=0,
            featured_posts_used=0,
            verified=True
        )
        db.add_all([employer1, employer2])
        db.commit()
        
        # Create expired job owned by employer1
        expired_job = Job(
            id=uuid4(),
            title="Expired Job Owned by Employer1",
            company="Owner Company",
            location="Denver, CO",
            remote=True,
            job_type=JobType.CONTRACT,
            experience_level=ExperienceLevel.SENIOR,
            description="This job is owned by employer1 and should not be reactivatable by employer2.",
            source_type=SourceType.DIRECT,
            employer_id=employer1.id,
            quality_score=80.0,
            status=JobStatus.EXPIRED,
            posted_at=datetime.utcnow() - timedelta(days=50),
            expires_at=datetime.utcnow() - timedelta(days=3),
            application_count=0,
            view_count=0,
            featured=False
        )
        db.add(expired_job)
        db.commit()
        
        # Prepare reactivation request
        new_expiration = datetime.utcnow() + timedelta(days=30)
        reactivate_data = {
            "expires_at": new_expiration.isoformat()
        }
        
        # Try to reactivate with employer2's credentials
        headers = {**auth_headers, "X-User-ID": str(employer2.id)}
        
        response = client.post(
            f"/api/jobs/{expired_job.id}/reactivate",
            json=reactivate_data,
            headers=headers
        )
        
        # Verify forbidden response
        assert response.status_code == 403
        assert "own jobs" in response.json()["detail"].lower()
    
    def test_reactivate_job_validates_expiration_within_90_days(self, client, db: Session, auth_headers):
        """
        Test that reactivation validates expiration date is within 90 days.
        """
        # Create employer
        employer = Employer(
            id=uuid4(),
            email="validate@test.com",
            company_name="Validate Company",
            subscription_tier=SubscriptionTier.PREMIUM,
            subscription_start_date=datetime.utcnow(),
            subscription_end_date=datetime.utcnow() + timedelta(days=30),
            monthly_posts_used=0,
            featured_posts_used=0,
            verified=True
        )
        db.add(employer)
        db.commit()
        
        # Create expired job
        expired_job = Job(
            id=uuid4(),
            title="Expired Job for Validation Test",
            company="Validate Company",
            location="Portland, OR",
            remote=False,
            job_type=JobType.FULL_TIME,
            experience_level=ExperienceLevel.LEAD,
            description="This job will test expiration date validation during reactivation.",
            source_type=SourceType.DIRECT,
            employer_id=employer.id,
            quality_score=87.0,
            status=JobStatus.EXPIRED,
            posted_at=datetime.utcnow() - timedelta(days=70),
            expires_at=datetime.utcnow() - timedelta(days=10),
            application_count=0,
            view_count=0,
            featured=False
        )
        db.add(expired_job)
        db.commit()
        
        # Try to reactivate with expiration date > 90 days in future
        invalid_expiration = datetime.utcnow() + timedelta(days=100)
        reactivate_data = {
            "expires_at": invalid_expiration.isoformat()
        }
        
        headers = {**auth_headers, "X-User-ID": str(employer.id)}
        
        response = client.post(
            f"/api/jobs/{expired_job.id}/reactivate",
            json=reactivate_data,
            headers=headers
        )
        
        # Verify validation error
        assert response.status_code == 422
    
    def test_reactivate_job_rejects_non_expired_jobs(self, client, db: Session, auth_headers):
        """
        Test that reactivation only works on expired jobs.
        """
        # Create employer
        employer = Employer(
            id=uuid4(),
            email="active@test.com",
            company_name="Active Company",
            subscription_tier=SubscriptionTier.BASIC,
            subscription_start_date=datetime.utcnow(),
            subscription_end_date=datetime.utcnow() + timedelta(days=30),
            monthly_posts_used=0,
            featured_posts_used=0,
            verified=True
        )
        db.add(employer)
        db.commit()
        
        # Create active job (not expired)
        active_job = Job(
            id=uuid4(),
            title="Active Job Not Expired",
            company="Active Company",
            location="Miami, FL",
            remote=True,
            job_type=JobType.PART_TIME,
            experience_level=ExperienceLevel.ENTRY,
            description="This job is still active and should not be reactivatable.",
            source_type=SourceType.DIRECT,
            employer_id=employer.id,
            quality_score=78.0,
            status=JobStatus.ACTIVE,
            posted_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(days=40),
            application_count=0,
            view_count=0,
            featured=False
        )
        db.add(active_job)
        db.commit()
        
        # Try to reactivate active job
        new_expiration = datetime.utcnow() + timedelta(days=50)
        reactivate_data = {
            "expires_at": new_expiration.isoformat()
        }
        
        headers = {**auth_headers, "X-User-ID": str(employer.id)}
        
        response = client.post(
            f"/api/jobs/{active_job.id}/reactivate",
            json=reactivate_data,
            headers=headers
        )
        
        # Verify bad request response
        assert response.status_code == 400
        assert "not expired" in response.json()["detail"].lower()
    
    def test_reactivate_job_not_found(self, client, auth_headers):
        """
        Test reactivation with non-existent job ID.
        """
        # Try to reactivate non-existent job
        fake_job_id = uuid4()
        new_expiration = datetime.utcnow() + timedelta(days=30)
        reactivate_data = {
            "expires_at": new_expiration.isoformat()
        }
        
        response = client.post(
            f"/api/jobs/{fake_job_id}/reactivate",
            json=reactivate_data,
            headers=auth_headers
        )
        
        # Verify not found response
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
