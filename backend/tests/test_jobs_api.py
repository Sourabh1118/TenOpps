"""
Tests for job API endpoints.

This module tests all job-related API endpoints including:
- Direct job posting
- Job retrieval
- Job updates
- Job deletion and status management
- View counter increment
"""
import pytest
from datetime import datetime, timedelta
from uuid import uuid4
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import Mock, patch

from app.main import app
from app.db.base import Base
from app.db.session import get_db
from app.models.employer import Employer, SubscriptionTier
from app.models.job import Job, JobType, ExperienceLevel, JobStatus, SourceType
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
def test_job(test_db, test_employer):
    """Create a test job."""
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
        quality_score=95.0,
        status=JobStatus.ACTIVE,
        posted_at=datetime.utcnow(),
        expires_at=datetime.utcnow() + timedelta(days=30),
        featured=False,
        tags=["python", "backend"],
        application_count=0,
        view_count=0,
    )
    test_db.add(job)
    test_db.commit()
    test_db.refresh(job)
    return job


class TestDirectJobPosting:
    """Tests for direct job posting endpoint."""
    
    @patch('app.api.jobs.check_quota')
    @patch('app.api.jobs.consume_quota')
    def test_create_direct_job_success(self, mock_consume, mock_check, client, employer_token):
        """Test successful direct job creation."""
        mock_check.return_value = True
        
        job_data = {
            "title": "Senior Python Developer",
            "company": "Test Company",
            "location": "San Francisco, CA",
            "remote": True,
            "job_type": "full_time",
            "experience_level": "senior",
            "description": "We are looking for an experienced Python developer to join our team and build amazing products.",
            "requirements": ["5+ years Python", "Django/FastAPI experience"],
            "responsibilities": ["Build APIs", "Mentor junior developers"],
            "salary_min": 120000,
            "salary_max": 180000,
            "salary_currency": "USD",
            "expires_at": (datetime.utcnow() + timedelta(days=30)).isoformat(),
            "featured": False,
            "tags": ["python", "backend"]
        }
        
        response = client.post(
            "/api/jobs/direct",
            json=job_data,
            headers={"Authorization": f"Bearer {employer_token}"}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert "job_id" in data
        assert data["message"] == "Job posted successfully"
    
    @patch('app.api.jobs.check_quota')
    def test_create_job_quota_exceeded(self, mock_check, client, employer_token):
        """Test job creation when quota is exceeded."""
        mock_check.return_value = False
        
        job_data = {
            "title": "Senior Python Developer",
            "company": "Test Company",
            "location": "San Francisco, CA",
            "remote": True,
            "job_type": "full_time",
            "experience_level": "senior",
            "description": "We are looking for an experienced Python developer to join our team and build amazing products.",
            "expires_at": (datetime.utcnow() + timedelta(days=30)).isoformat(),
        }
        
        response = client.post(
            "/api/jobs/direct",
            json=job_data,
            headers={"Authorization": f"Bearer {employer_token}"}
        )
        
        assert response.status_code == 403
        assert "quota exceeded" in response.json()["detail"].lower()
    
    def test_create_job_invalid_title_length(self, client, employer_token):
        """Test job creation with invalid title length."""
        job_data = {
            "title": "Short",  # Too short (< 10 chars)
            "company": "Test Company",
            "location": "San Francisco, CA",
            "remote": True,
            "job_type": "full_time",
            "experience_level": "senior",
            "description": "We are looking for an experienced Python developer to join our team and build amazing products.",
            "expires_at": (datetime.utcnow() + timedelta(days=30)).isoformat(),
        }
        
        response = client.post(
            "/api/jobs/direct",
            json=job_data,
            headers={"Authorization": f"Bearer {employer_token}"}
        )
        
        assert response.status_code == 422
    
    def test_create_job_invalid_salary_range(self, client, employer_token):
        """Test job creation with invalid salary range."""
        job_data = {
            "title": "Senior Python Developer",
            "company": "Test Company",
            "location": "San Francisco, CA",
            "remote": True,
            "job_type": "full_time",
            "experience_level": "senior",
            "description": "We are looking for an experienced Python developer to join our team and build amazing products.",
            "salary_min": 180000,
            "salary_max": 120000,  # Max < Min (invalid)
            "expires_at": (datetime.utcnow() + timedelta(days=30)).isoformat(),
        }
        
        response = client.post(
            "/api/jobs/direct",
            json=job_data,
            headers={"Authorization": f"Bearer {employer_token}"}
        )
        
        assert response.status_code == 422
    
    def test_create_job_expiration_too_far(self, client, employer_token):
        """Test job creation with expiration date beyond 90 days."""
        job_data = {
            "title": "Senior Python Developer",
            "company": "Test Company",
            "location": "San Francisco, CA",
            "remote": True,
            "job_type": "full_time",
            "experience_level": "senior",
            "description": "We are looking for an experienced Python developer to join our team and build amazing products.",
            "expires_at": (datetime.utcnow() + timedelta(days=100)).isoformat(),  # > 90 days
        }
        
        response = client.post(
            "/api/jobs/direct",
            json=job_data,
            headers={"Authorization": f"Bearer {employer_token}"}
        )
        
        assert response.status_code == 422


class TestJobRetrieval:
    """Tests for job retrieval endpoints."""
    
    def test_get_job_by_id_success(self, client, test_job):
        """Test successful job retrieval by ID."""
        response = client.get(f"/api/jobs/{test_job.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_job.id)
        assert data["title"] == test_job.title
        assert data["company"] == test_job.company
        assert "application_count" in data
        assert "view_count" in data
    
    def test_get_job_not_found(self, client):
        """Test job retrieval with non-existent ID."""
        fake_id = uuid4()
        response = client.get(f"/api/jobs/{fake_id}")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_get_employer_jobs_success(self, client, test_employer, test_job, employer_token):
        """Test successful retrieval of employer's jobs."""
        response = client.get(
            f"/api/jobs/employer/{test_employer.id}",
            headers={"Authorization": f"Bearer {employer_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "jobs" in data
        assert "total" in data
        assert len(data["jobs"]) == 1
        assert data["jobs"][0]["id"] == str(test_job.id)
    
    def test_get_employer_jobs_with_status_filter(self, client, test_employer, test_job, employer_token):
        """Test employer jobs retrieval with status filter."""
        response = client.get(
            f"/api/jobs/employer/{test_employer.id}?status_filter=active",
            headers={"Authorization": f"Bearer {employer_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["jobs"]) == 1
    
    def test_get_employer_jobs_unauthorized(self, client, test_employer):
        """Test employer jobs retrieval without authentication."""
        response = client.get(f"/api/jobs/employer/{test_employer.id}")
        
        assert response.status_code == 403


class TestJobUpdate:
    """Tests for job update endpoint."""
    
    def test_update_job_success(self, client, test_job, employer_token):
        """Test successful job update."""
        update_data = {
            "description": "Updated job description with more details about the role and responsibilities.",
            "salary_min": 130000,
            "salary_max": 190000
        }
        
        response = client.patch(
            f"/api/jobs/{test_job.id}",
            json=update_data,
            headers={"Authorization": f"Bearer {employer_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["description"] == update_data["description"]
        assert data["salary_min"] == update_data["salary_min"]
        assert data["salary_max"] == update_data["salary_max"]
    
    def test_update_job_not_found(self, client, employer_token):
        """Test job update with non-existent ID."""
        fake_id = uuid4()
        update_data = {"description": "Updated description"}
        
        response = client.patch(
            f"/api/jobs/{fake_id}",
            json=update_data,
            headers={"Authorization": f"Bearer {employer_token}"}
        )
        
        assert response.status_code == 404
    
    def test_update_job_wrong_employer(self, client, test_job):
        """Test job update by wrong employer."""
        # Create token for different employer
        wrong_token = create_access_token({
            "sub": str(uuid4()),
            "role": "employer"
        })
        
        update_data = {"description": "Updated description"}
        
        response = client.patch(
            f"/api/jobs/{test_job.id}",
            json=update_data,
            headers={"Authorization": f"Bearer {wrong_token}"}
        )
        
        assert response.status_code == 403


class TestJobDeletion:
    """Tests for job deletion and status management."""
    
    def test_delete_job_success(self, client, test_job, employer_token):
        """Test successful job deletion."""
        response = client.delete(
            f"/api/jobs/{test_job.id}",
            headers={"Authorization": f"Bearer {employer_token}"}
        )
        
        assert response.status_code == 200
        assert "deleted successfully" in response.json()["message"].lower()
    
    def test_delete_job_not_found(self, client, employer_token):
        """Test job deletion with non-existent ID."""
        fake_id = uuid4()
        
        response = client.delete(
            f"/api/jobs/{fake_id}",
            headers={"Authorization": f"Bearer {employer_token}"}
        )
        
        assert response.status_code == 404
    
    def test_mark_job_filled_success(self, client, test_job, employer_token):
        """Test successfully marking job as filled."""
        response = client.post(
            f"/api/jobs/{test_job.id}/mark-filled",
            headers={"Authorization": f"Bearer {employer_token}"}
        )
        
        assert response.status_code == 200
        assert "filled" in response.json()["message"].lower()
    
    def test_mark_job_filled_wrong_employer(self, client, test_job):
        """Test marking job as filled by wrong employer."""
        wrong_token = create_access_token({
            "sub": str(uuid4()),
            "role": "employer"
        })
        
        response = client.post(
            f"/api/jobs/{test_job.id}/mark-filled",
            headers={"Authorization": f"Bearer {wrong_token}"}
        )
        
        assert response.status_code == 403


class TestViewCounter:
    """Tests for view counter increment."""
    
    @patch('app.api.jobs.redis_client')
    def test_increment_view_count_success(self, mock_redis_client, client, test_job):
        """Test successful view count increment."""
        mock_redis = Mock()
        mock_redis.incr.return_value = 5
        mock_redis_client.get_cache_client.return_value = mock_redis
        
        response = client.post(f"/api/jobs/{test_job.id}/increment-view")
        
        assert response.status_code == 200
        assert "incremented" in response.json()["message"].lower()
        mock_redis.incr.assert_called_once()
    
    @patch('app.api.jobs.redis_client')
    def test_increment_view_count_batch_update(self, mock_redis_client, client, test_job, test_db):
        """Test view count batch update to database."""
        mock_redis = Mock()
        mock_redis.incr.return_value = 10  # Trigger batch update
        mock_redis_client.get_cache_client.return_value = mock_redis
        
        response = client.post(f"/api/jobs/{test_job.id}/increment-view")
        
        assert response.status_code == 200
        mock_redis.delete.assert_called_once()
    
    def test_increment_view_count_job_not_found(self, client):
        """Test view count increment for non-existent job."""
        fake_id = uuid4()
        
        response = client.post(f"/api/jobs/{fake_id}/increment-view")
        
        assert response.status_code == 404
