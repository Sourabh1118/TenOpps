"""
Tests for privacy and data retention endpoints.

This module tests:
- Account deletion for job seekers and employers
- GDPR data export
- Consent management
"""
import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.models.job_seeker import JobSeeker
from app.models.employer import Employer
from app.models.application import Application, ApplicationStatus
from app.models.job import Job, JobType, ExperienceLevel, SourceType, JobStatus
from app.models.consent import Consent
from app.core.security import hash_password, create_access_token


client = TestClient(app)


@pytest.fixture
def job_seeker_token(db: Session):
    """Create a job seeker and return auth token."""
    job_seeker = JobSeeker(
        email="jobseeker@test.com",
        password_hash=hash_password("TestPass123!"),
        full_name="Test Job Seeker",
        phone="+1234567890",
    )
    db.add(job_seeker)
    db.commit()
    db.refresh(job_seeker)
    
    token = create_access_token({
        "sub": str(job_seeker.id),
        "role": "job_seeker"
    })
    
    return token, job_seeker


@pytest.fixture
def employer_token(db: Session):
    """Create an employer and return auth token."""
    from app.models.employer import SubscriptionTier
    
    employer = Employer(
        email="employer@test.com",
        password_hash=hash_password("TestPass123!"),
        company_name="Test Company",
        subscription_tier=SubscriptionTier.FREE,
        subscription_start_date=datetime.utcnow(),
        subscription_end_date=datetime.utcnow() + timedelta(days=365),
    )
    db.add(employer)
    db.commit()
    db.refresh(employer)
    
    token = create_access_token({
        "sub": str(employer.id),
        "role": "employer"
    })
    
    return token, employer


def test_delete_job_seeker_account(db: Session, job_seeker_token):
    """Test job seeker account deletion."""
    token, job_seeker = job_seeker_token
    
    # Create some applications
    job = Job(
        title="Test Software Engineer",
        company="Test Company",
        location="San Francisco",
        remote=False,
        job_type=JobType.FULL_TIME,
        experience_level=ExperienceLevel.MID,
        description="Test job description for testing purposes only",
        source_type=SourceType.DIRECT,
        quality_score=75.0,
        status=JobStatus.ACTIVE,
        posted_at=datetime.utcnow(),
        expires_at=datetime.utcnow() + timedelta(days=30),
    )
    db.add(job)
    db.commit()
    
    application = Application(
        job_id=job.id,
        job_seeker_id=job_seeker.id,
        resume="https://example.com/resume.pdf",
        cover_letter="Test cover letter",
        status=ApplicationStatus.SUBMITTED,
    )
    db.add(application)
    db.commit()
    
    # Delete account
    response = client.delete(
        "/api/privacy/job-seeker/account",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 202
    data = response.json()
    assert "deletion_date" in data
    assert data["applications_anonymized"] == 1
    
    # Verify data was anonymized
    db.refresh(job_seeker)
    assert job_seeker.email.startswith("deleted_")
    assert job_seeker.full_name == "Deleted User"
    assert job_seeker.password_hash == "DELETED"
    
    db.refresh(application)
    assert application.resume == "DELETED"


def test_delete_employer_account(db: Session, employer_token):
    """Test employer account deletion."""
    token, employer = employer_token
    
    # Create some jobs
    job = Job(
        title="Test Software Engineer",
        company=employer.company_name,
        location="San Francisco",
        remote=False,
        job_type=JobType.FULL_TIME,
        experience_level=ExperienceLevel.MID,
        description="Test job description for testing purposes only",
        source_type=SourceType.DIRECT,
        employer_id=employer.id,
        quality_score=75.0,
        status=JobStatus.ACTIVE,
        posted_at=datetime.utcnow(),
        expires_at=datetime.utcnow() + timedelta(days=30),
    )
    db.add(job)
    db.commit()
    
    # Delete account
    response = client.delete(
        "/api/privacy/employer/account",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 202
    data = response.json()
    assert "deletion_date" in data
    assert data["jobs_marked_deleted"] == 1
    
    # Verify data was anonymized
    db.refresh(employer)
    assert employer.email.startswith("deleted_")
    assert employer.company_name == "Deleted Company"
    assert employer.password_hash == "DELETED"
    
    db.refresh(job)
    assert job.status == JobStatus.DELETED


def test_export_job_seeker_data(db: Session, job_seeker_token):
    """Test GDPR data export for job seeker."""
    token, job_seeker = job_seeker_token
    
    response = client.get(
        "/api/privacy/export",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["user_type"] == "job_seeker"
    assert "personal_data" in data
    assert data["personal_data"]["email"] == job_seeker.email
    assert data["personal_data"]["full_name"] == job_seeker.full_name
    assert "activity" in data
    assert "applications" in data["activity"]


def test_export_employer_data(db: Session, employer_token):
    """Test GDPR data export for employer."""
    token, employer = employer_token
    
    response = client.get(
        "/api/privacy/export",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["user_type"] == "employer"
    assert "personal_data" in data
    assert data["personal_data"]["email"] == employer.email
    assert data["personal_data"]["company_name"] == employer.company_name
    assert "subscription" in data
    assert "activity" in data
    assert "jobs" in data["activity"]


def test_update_consent(db: Session, job_seeker_token):
    """Test updating consent preferences."""
    token, job_seeker = job_seeker_token
    
    consent_data = {
        "marketing_emails": True,
        "data_processing": True,
        "third_party_sharing": False,
    }
    
    response = client.post(
        "/api/privacy/consent",
        json=consent_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["user_id"] == str(job_seeker.id)
    assert data["marketing_emails"] == True
    assert data["data_processing"] == True
    assert data["third_party_sharing"] == False
    assert "consent_date" in data
    assert "updated_at" in data


def test_get_consent(db: Session, job_seeker_token):
    """Test getting consent preferences."""
    token, job_seeker = job_seeker_token
    
    # Create consent record
    consent = Consent(
        user_id=job_seeker.id,
        user_type="job_seeker",
        marketing_emails=True,
        data_processing=True,
        third_party_sharing=False,
    )
    db.add(consent)
    db.commit()
    
    response = client.get(
        "/api/privacy/consent",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["user_id"] == str(job_seeker.id)
    assert data["marketing_emails"] == True
    assert data["data_processing"] == True
    assert data["third_party_sharing"] == False


def test_get_consent_not_found(db: Session, job_seeker_token):
    """Test getting consent when no record exists."""
    token, job_seeker = job_seeker_token
    
    response = client.get(
        "/api/privacy/consent",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 404
    assert "No consent record found" in response.json()["detail"]


def test_delete_account_wrong_role(db: Session, employer_token):
    """Test that employer cannot use job seeker deletion endpoint."""
    token, employer = employer_token
    
    response = client.delete(
        "/api/privacy/job-seeker/account",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 403
    assert "only for job seeker accounts" in response.json()["detail"]


def test_unauthorized_access(db: Session):
    """Test that endpoints require authentication."""
    response = client.delete("/api/privacy/job-seeker/account")
    assert response.status_code == 401
    
    response = client.get("/api/privacy/export")
    assert response.status_code == 401
    
    response = client.get("/api/privacy/consent")
    assert response.status_code == 401
