"""
Tests for application API endpoints and service.

This module tests all application-related functionality including:
- Application submission by job seekers
- Application retrieval for employers
- Application status updates
- Application retrieval for job seekers
"""
import pytest
from datetime import datetime, timedelta
from uuid import uuid4
from fastapi.testclient import TestClient

from app.main import app
from app.db.session import get_db
from app.models.employer import Employer, SubscriptionTier
from app.models.job_seeker import JobSeeker
from app.models.job import Job, JobType, ExperienceLevel, JobStatus, SourceType
from app.models.application import Application, ApplicationStatus
from app.core.security import create_access_token


# Use conftest fixtures for database
@pytest.fixture(scope="function")
def client(db_session):
    """Create test client with database override."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def test_employer(db_session):
    """Create a test employer with basic tier."""
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
        url_imports_used=0,
        verified=True,
    )
    db_session.add(employer)
    db_session.commit()
    db_session.refresh(employer)
    return employer


@pytest.fixture
def test_free_employer(db_session):
    """Create a test employer with free tier (no application tracking)."""
    employer = Employer(
        id=uuid4(),
        email="free@employer.com",
        password_hash="hashed_password",
        company_name="Free Company",
        subscription_tier=SubscriptionTier.FREE,
        subscription_start_date=datetime.utcnow(),
        subscription_end_date=datetime.utcnow() + timedelta(days=30),
        monthly_posts_used=0,
        featured_posts_used=0,
        url_imports_used=0,
        verified=True,
    )
    db_session.add(employer)
    db_session.commit()
    db_session.refresh(employer)
    return employer


@pytest.fixture
def test_job_seeker(db_session):
    """Create a test job seeker."""
    job_seeker = JobSeeker(
        id=uuid4(),
        email="jobseeker@example.com",
        password_hash="hashed_password",
        full_name="John Doe",
        phone="+1234567890",
        resume_url="https://storage.example.com/resumes/john-doe.pdf",
    )
    db_session.add(job_seeker)
    db_session.commit()
    db_session.refresh(job_seeker)
    return job_seeker


@pytest.fixture
def employer_token(test_employer):
    """Create JWT token for test employer."""
    return create_access_token({
        "sub": str(test_employer.id),
        "role": "employer"
    })


@pytest.fixture
def free_employer_token(test_free_employer):
    """Create JWT token for free tier employer."""
    return create_access_token({
        "sub": str(test_free_employer.id),
        "role": "employer"
    })


@pytest.fixture
def job_seeker_token(test_job_seeker):
    """Create JWT token for test job seeker."""
    return create_access_token({
        "sub": str(test_job_seeker.id),
        "role": "job_seeker"
    })


@pytest.fixture
def test_direct_job(db_session, test_employer):
    """Create a test direct job."""
    job = Job(
        id=uuid4(),
        title="Senior Python Developer",
        company=test_employer.company_name,
        location="San Francisco, CA",
        remote=True,
        job_type=JobType.FULL_TIME,
        experience_level=ExperienceLevel.SENIOR,
        description="We are looking for an experienced Python developer to join our team.",
        requirements=["5+ years Python", "Django/FastAPI experience"],
        responsibilities=["Build APIs", "Mentor junior developers"],
        salary_min=120000,
        salary_max=180000,
        salary_currency="USD",
        source_type=SourceType.DIRECT,
        employer_id=test_employer.id,
        quality_score=85.0,
        status=JobStatus.ACTIVE,
        posted_at=datetime.utcnow(),
        expires_at=datetime.utcnow() + timedelta(days=30),
        application_count=0,
        view_count=0,
        featured=False,
        tags=["python", "backend", "api"],
    )
    db_session.add(job)
    db_session.commit()
    db_session.refresh(job)
    return job


@pytest.fixture
def test_aggregated_job(db_session):
    """Create a test aggregated job (not eligible for applications)."""
    job = Job(
        id=uuid4(),
        title="Software Engineer",
        company="External Company",
        location="New York, NY",
        remote=False,
        job_type=JobType.FULL_TIME,
        experience_level=ExperienceLevel.MID,
        description="Software engineering position at external company.",
        source_type=SourceType.AGGREGATED,
        source_url="https://linkedin.com/jobs/12345",
        source_platform="LinkedIn",
        quality_score=60.0,
        status=JobStatus.ACTIVE,
        posted_at=datetime.utcnow(),
        expires_at=datetime.utcnow() + timedelta(days=30),
        application_count=0,
        view_count=0,
        featured=False,
    )
    db_session.add(job)
    db_session.commit()
    db_session.refresh(job)
    return job


# Test Application Submission (Task 18.1)
class TestApplicationSubmission:
    """Tests for application submission endpoint."""
    
    def test_submit_application_success(self, client, job_seeker_token, test_direct_job, db_session):
        """Test successful application submission."""
        response = client.post(
            "/api/applications",
            json={
                "job_id": str(test_direct_job.id),
                "resume": "https://storage.example.com/resumes/john-doe.pdf",
                "cover_letter": "I am excited to apply for this position."
            },
            headers={"Authorization": f"Bearer {job_seeker_token}"}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert "application_id" in data
        assert data["message"] == "Application submitted successfully"
        
        # Verify application was created in database
        application = db_session.query(Application).filter(
            Application.id == data["application_id"]
        ).first()
        assert application is not None
        assert application.status == ApplicationStatus.SUBMITTED
        
        # Verify job application count was incremented
        db_session.refresh(test_direct_job)
        assert test_direct_job.application_count == 1
    
    def test_submit_application_without_cover_letter(self, client, job_seeker_token, test_direct_job):
        """Test application submission without cover letter."""
        response = client.post(
            "/api/applications",
            json={
                "job_id": str(test_direct_job.id),
                "resume": "https://storage.example.com/resumes/john-doe.pdf"
            },
            headers={"Authorization": f"Bearer {job_seeker_token}"}
        )
        
        assert response.status_code == 201
    
    def test_submit_application_to_aggregated_job(self, client, job_seeker_token, test_aggregated_job):
        """Test that applications cannot be submitted to aggregated jobs."""
        response = client.post(
            "/api/applications",
            json={
                "job_id": str(test_aggregated_job.id),
                "resume": "https://storage.example.com/resumes/john-doe.pdf"
            },
            headers={"Authorization": f"Bearer {job_seeker_token}"}
        )
        
        assert response.status_code == 400
        assert "direct posts" in response.json()["detail"].lower()
    
    def test_submit_duplicate_application(self, client, job_seeker_token, test_direct_job, test_job_seeker, db_session):
        """Test that duplicate applications are rejected."""
        # Create first application
        application = Application(
            id=uuid4(),
            job_id=test_direct_job.id,
            job_seeker_id=test_job_seeker.id,
            resume="https://storage.example.com/resumes/john-doe.pdf",
            status=ApplicationStatus.SUBMITTED,
        )
        db_session.add(application)
        db_session.commit()
        
        # Try to submit duplicate
        response = client.post(
            "/api/applications",
            json={
                "job_id": str(test_direct_job.id),
                "resume": "https://storage.example.com/resumes/john-doe.pdf"
            },
            headers={"Authorization": f"Bearer {job_seeker_token}"}
        )
        
        assert response.status_code == 409
        assert "already applied" in response.json()["detail"].lower()
    
    def test_submit_application_unauthorized(self, client, test_direct_job):
        """Test that unauthorized requests are rejected."""
        response = client.post(
            "/api/applications",
            json={
                "job_id": str(test_direct_job.id),
                "resume": "https://storage.example.com/resumes/john-doe.pdf"
            }
        )
        
        assert response.status_code == 403
    
    def test_submit_application_with_employer_token(self, client, employer_token, test_direct_job):
        """Test that employers cannot submit applications."""
        response = client.post(
            "/api/applications",
            json={
                "job_id": str(test_direct_job.id),
                "resume": "https://storage.example.com/resumes/john-doe.pdf"
            },
            headers={"Authorization": f"Bearer {employer_token}"}
        )
        
        assert response.status_code == 403


# Test Application Retrieval for Employers (Task 18.3)
class TestEmployerApplicationRetrieval:
    """Tests for employer application retrieval endpoint."""
    
    def test_get_job_applications_success(self, client, employer_token, test_direct_job, test_job_seeker, db_session):
        """Test successful retrieval of job applications."""
        # Create test applications
        app1 = Application(
            id=uuid4(),
            job_id=test_direct_job.id,
            job_seeker_id=test_job_seeker.id,
            resume="https://storage.example.com/resumes/john-doe.pdf",
            cover_letter="I am excited to apply.",
            status=ApplicationStatus.SUBMITTED,
        )
        db_session.add(app1)
        db_session.commit()
        
        response = client.get(
            f"/api/applications/job/{test_direct_job.id}",
            headers={"Authorization": f"Bearer {employer_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["applications"]) == 1
        assert data["applications"][0]["applicant_name"] == "John Doe"
        assert data["applications"][0]["status"] == "submitted"
    
    def test_get_job_applications_free_tier(self, client, free_employer_token, test_direct_job, test_free_employer, db_session):
        """Test that free tier employers cannot access application tracking."""
        # Update job to belong to free employer
        test_direct_job.employer_id = test_free_employer.id
        db_session.commit()
        
        response = client.get(
            f"/api/applications/job/{test_direct_job.id}",
            headers={"Authorization": f"Bearer {free_employer_token}"}
        )
        
        assert response.status_code == 403
        assert "basic or premium" in response.json()["detail"].lower()
    
    def test_get_job_applications_wrong_employer(self, client, test_direct_job, db_session):
        """Test that employers can only view applications for their own jobs."""
        # Create another employer
        other_employer = Employer(
            id=uuid4(),
            email="other@employer.com",
            password_hash="hashed_password",
            company_name="Other Company",
            subscription_tier=SubscriptionTier.BASIC,
            subscription_start_date=datetime.utcnow(),
            subscription_end_date=datetime.utcnow() + timedelta(days=30),
            monthly_posts_used=0,
            featured_posts_used=0,
            url_imports_used=0,
            verified=True,
        )
        db_session.add(other_employer)
        db_session.commit()
        
        other_token = create_access_token({
            "sub": str(other_employer.id),
            "role": "employer"
        })
        
        response = client.get(
            f"/api/applications/job/{test_direct_job.id}",
            headers={"Authorization": f"Bearer {other_token}"}
        )
        
        assert response.status_code == 403


# Test Application Status Updates (Task 18.4)
class TestApplicationStatusUpdate:
    """Tests for application status update endpoint."""
    
    def test_update_application_status_success(self, client, employer_token, test_direct_job, test_job_seeker, db_session):
        """Test successful application status update."""
        # Create test application
        application = Application(
            id=uuid4(),
            job_id=test_direct_job.id,
            job_seeker_id=test_job_seeker.id,
            resume="https://storage.example.com/resumes/john-doe.pdf",
            status=ApplicationStatus.SUBMITTED,
        )
        db_session.add(application)
        db_session.commit()
        
        response = client.patch(
            f"/api/applications/{application.id}",
            json={
                "status": "shortlisted",
                "employer_notes": "Strong candidate"
            },
            headers={"Authorization": f"Bearer {employer_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "shortlisted"
        assert data["employer_notes"] == "Strong candidate"
    
    def test_update_application_all_statuses(self, client, employer_token, test_direct_job, test_job_seeker, db_session):
        """Test updating application through all valid statuses."""
        application = Application(
            id=uuid4(),
            job_id=test_direct_job.id,
            job_seeker_id=test_job_seeker.id,
            resume="https://storage.example.com/resumes/john-doe.pdf",
            status=ApplicationStatus.SUBMITTED,
        )
        db_session.add(application)
        db_session.commit()
        
        statuses = ["reviewed", "shortlisted", "accepted"]
        
        for new_status in statuses:
            response = client.patch(
                f"/api/applications/{application.id}",
                json={"status": new_status},
                headers={"Authorization": f"Bearer {employer_token}"}
            )
            assert response.status_code == 200
            assert response.json()["status"] == new_status
    
    def test_update_application_wrong_employer(self, client, test_direct_job, test_job_seeker, db_session):
        """Test that employers can only update applications for their own jobs."""
        # Create application
        application = Application(
            id=uuid4(),
            job_id=test_direct_job.id,
            job_seeker_id=test_job_seeker.id,
            resume="https://storage.example.com/resumes/john-doe.pdf",
            status=ApplicationStatus.SUBMITTED,
        )
        db_session.add(application)
        db_session.commit()
        
        # Create another employer
        other_employer = Employer(
            id=uuid4(),
            email="other@employer.com",
            password_hash="hashed_password",
            company_name="Other Company",
            subscription_tier=SubscriptionTier.BASIC,
            subscription_start_date=datetime.utcnow(),
            subscription_end_date=datetime.utcnow() + timedelta(days=30),
            monthly_posts_used=0,
            featured_posts_used=0,
            url_imports_used=0,
            verified=True,
        )
        db_session.add(other_employer)
        db_session.commit()
        
        other_token = create_access_token({
            "sub": str(other_employer.id),
            "role": "employer"
        })
        
        response = client.patch(
            f"/api/applications/{application.id}",
            json={"status": "reviewed"},
            headers={"Authorization": f"Bearer {other_token}"}
        )
        
        assert response.status_code == 403
    
    def test_update_nonexistent_application(self, client, employer_token):
        """Test updating a nonexistent application."""
        fake_id = uuid4()
        response = client.patch(
            f"/api/applications/{fake_id}",
            json={"status": "reviewed"},
            headers={"Authorization": f"Bearer {employer_token}"}
        )
        
        assert response.status_code == 404


# Test Job Seeker Application Retrieval (Task 18.5)
class TestJobSeekerApplicationRetrieval:
    """Tests for job seeker application retrieval endpoint."""
    
    def test_get_my_applications_success(self, client, job_seeker_token, test_direct_job, test_job_seeker, db_session):
        """Test successful retrieval of job seeker's applications."""
        # Create test applications
        app1 = Application(
            id=uuid4(),
            job_id=test_direct_job.id,
            job_seeker_id=test_job_seeker.id,
            resume="https://storage.example.com/resumes/john-doe.pdf",
            status=ApplicationStatus.SUBMITTED,
        )
        db_session.add(app1)
        db_session.commit()
        
        response = client.get(
            "/api/applications/my-applications",
            headers={"Authorization": f"Bearer {job_seeker_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["applications"]) == 1
        assert data["applications"][0]["job_title"] == "Senior Python Developer"
        assert data["applications"][0]["company"] == "Test Company"
        assert data["applications"][0]["status"] == "submitted"
    
    def test_get_my_applications_empty(self, client, job_seeker_token):
        """Test retrieval when job seeker has no applications."""
        response = client.get(
            "/api/applications/my-applications",
            headers={"Authorization": f"Bearer {job_seeker_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert len(data["applications"]) == 0
    
    def test_get_my_applications_multiple(self, client, job_seeker_token, test_direct_job, test_job_seeker, test_employer, db_session):
        """Test retrieval of multiple applications."""
        # Create another job
        job2 = Job(
            id=uuid4(),
            title="Backend Engineer",
            company=test_employer.company_name,
            location="Remote",
            remote=True,
            job_type=JobType.FULL_TIME,
            experience_level=ExperienceLevel.MID,
            description="Backend engineering position.",
            source_type=SourceType.DIRECT,
            employer_id=test_employer.id,
            quality_score=80.0,
            status=JobStatus.ACTIVE,
            posted_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(days=30),
            application_count=0,
            view_count=0,
            featured=False,
        )
        db_session.add(job2)
        db_session.commit()
        
        # Create applications
        app1 = Application(
            id=uuid4(),
            job_id=test_direct_job.id,
            job_seeker_id=test_job_seeker.id,
            resume="https://storage.example.com/resumes/john-doe.pdf",
            status=ApplicationStatus.SUBMITTED,
        )
        app2 = Application(
            id=uuid4(),
            job_id=job2.id,
            job_seeker_id=test_job_seeker.id,
            resume="https://storage.example.com/resumes/john-doe.pdf",
            status=ApplicationStatus.REVIEWED,
        )
        db_session.add_all([app1, app2])
        db_session.commit()
        
        response = client.get(
            "/api/applications/my-applications",
            headers={"Authorization": f"Bearer {job_seeker_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert len(data["applications"]) == 2
    
    def test_get_my_applications_unauthorized(self, client):
        """Test that unauthorized requests are rejected."""
        response = client.get("/api/applications/my-applications")
        
        assert response.status_code == 403
    
    def test_get_my_applications_with_employer_token(self, client, employer_token):
        """Test that employers cannot access job seeker endpoint."""
        response = client.get(
            "/api/applications/my-applications",
            headers={"Authorization": f"Bearer {employer_token}"}
        )
        
        assert response.status_code == 403


# Integration Tests
class TestApplicationIntegration:
    """Integration tests for complete application workflows."""
    
    def test_complete_application_workflow(self, client, job_seeker_token, employer_token, test_direct_job, test_job_seeker, db_session):
        """Test complete workflow: submit -> view -> update -> view."""
        # 1. Job seeker submits application
        submit_response = client.post(
            "/api/applications",
            json={
                "job_id": str(test_direct_job.id),
                "resume": "https://storage.example.com/resumes/john-doe.pdf",
                "cover_letter": "I am excited to apply."
            },
            headers={"Authorization": f"Bearer {job_seeker_token}"}
        )
        assert submit_response.status_code == 201
        application_id = submit_response.json()["application_id"]
        
        # 2. Job seeker views their applications
        my_apps_response = client.get(
            "/api/applications/my-applications",
            headers={"Authorization": f"Bearer {job_seeker_token}"}
        )
        assert my_apps_response.status_code == 200
        assert my_apps_response.json()["total"] == 1
        
        # 3. Employer views applications for job
        employer_view_response = client.get(
            f"/api/applications/job/{test_direct_job.id}",
            headers={"Authorization": f"Bearer {employer_token}"}
        )
        assert employer_view_response.status_code == 200
        assert employer_view_response.json()["total"] == 1
        
        # 4. Employer updates application status
        update_response = client.patch(
            f"/api/applications/{application_id}",
            json={
                "status": "shortlisted",
                "employer_notes": "Great candidate"
            },
            headers={"Authorization": f"Bearer {employer_token}"}
        )
        assert update_response.status_code == 200
        assert update_response.json()["status"] == "shortlisted"
        
        # 5. Job seeker views updated status
        final_view_response = client.get(
            "/api/applications/my-applications",
            headers={"Authorization": f"Bearer {job_seeker_token}"}
        )
        assert final_view_response.status_code == 200
        assert final_view_response.json()["applications"][0]["status"] == "shortlisted"
