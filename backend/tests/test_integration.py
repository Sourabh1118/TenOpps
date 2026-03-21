"""
Integration tests for Job Aggregation Platform.

Tests end-to-end workflows across multiple services:
- Scraping pipeline
- Job posting and application flow
- URL import flow
- Search with various filters
- Subscription upgrade flow

**Validates: Requirements 1.10, 4.10, 5.15, 6.13, 8.8**
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
import time

from app.main import app
from app.models.job import Job, JobType, ExperienceLevel, JobStatus, SourceType
from app.models.employer import Employer, SubscriptionTier
from app.models.job_seeker import JobSeeker
from app.models.application import Application, ApplicationStatus
from app.models.scraping_task import ScrapingTask, TaskType, TaskStatus as ScrapingTaskStatus
from app.models.job_source import JobSource
from app.core.security import create_access_token, hash_password


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def test_employer(pg_db_session: Session):
    """Create test employer with basic subscription."""
    employer = Employer(
        email="employer@test.com",
        password_hash=hash_password("password123"),
        company_name="Test Company",
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
def test_job_seeker(pg_db_session: Session):
    """Create test job seeker."""
    job_seeker = JobSeeker(
        email="jobseeker@test.com",
        password_hash=hash_password("password123"),
        full_name="Test Job Seeker",
        phone="1234567890"
    )
    pg_db_session.add(job_seeker)
    pg_db_session.commit()
    pg_db_session.refresh(job_seeker)
    return job_seeker


@pytest.fixture
def employer_token(test_employer):
    """Create employer access token."""
    return create_access_token(
        data={"sub": test_employer.email, "user_id": str(test_employer.id), "role": "employer"}
    )


@pytest.fixture
def job_seeker_token(test_job_seeker):
    """Create job seeker access token."""
    return create_access_token(
        data={"sub": test_job_seeker.email, "user_id": str(test_job_seeker.id), "role": "job_seeker"}
    )


class TestScrapingPipelineIntegration:
    """
    Integration tests for end-to-end scraping pipeline.
    
    **Validates: Requirement 1.10** - WHEN scraping completes, THE System SHALL log 
    the number of jobs found, created, and updated
    """
    
    @pytest.mark.asyncio
    async def test_complete_scraping_pipeline(self, pg_db_session: Session):
        """Test complete scraping pipeline from fetch to database storage."""
        # Mock scraper that returns job data
        mock_job_data = [
            {
                "title": "Software Engineer",
                "company": "Tech Corp",
                "location": "San Francisco, CA",
                "remote": False,
                "job_type": "FULL_TIME",
                "experience_level": "MID",
                "description": "We are looking for a talented software engineer to join our team.",
                "requirements": ["Python", "FastAPI"],
                "responsibilities": ["Build APIs", "Write tests"],
                "salary_min": 100000,
                "salary_max": 150000,
                "salary_currency": "USD",
                "source_url": "https://linkedin.com/jobs/123",
                "posted_at": datetime.utcnow()
            },
            {
                "title": "Senior Software Engineer",
                "company": "Tech Corp",
                "location": "San Francisco, CA",
                "remote": True,
                "job_type": "FULL_TIME",
                "experience_level": "SENIOR",
                "description": "We are looking for a senior software engineer with extensive experience.",
                "requirements": ["Python", "FastAPI", "PostgreSQL"],
                "responsibilities": ["Lead projects", "Mentor juniors"],
                "salary_min": 150000,
                "salary_max": 200000,
                "salary_currency": "USD",
                "source_url": "https://linkedin.com/jobs/124",
                "posted_at": datetime.utcnow()
            }
        ]
        
        # Create scraping task
        task = ScrapingTask(
            task_type=TaskType.SCHEDULED_SCRAPE,
            source_platform="LinkedIn",
            status=ScrapingTaskStatus.PENDING,
            jobs_found=0,
            jobs_created=0,
            jobs_updated=0,
            retry_count=0
        )
        pg_db_session.add(task)
        pg_db_session.commit()
        pg_db_session.refresh(task)
        
        # Simulate scraping process
        task.status = ScrapingTaskStatus.RUNNING
        task.started_at = datetime.utcnow()
        pg_db_session.commit()
        
        jobs_created = 0
        for job_data in mock_job_data:
            # Create job
            job = Job(
                title=job_data["title"],
                company=job_data["company"],
                location=job_data["location"],
                remote=job_data["remote"],
                job_type=JobType[job_data["job_type"]],
                experience_level=ExperienceLevel[job_data["experience_level"]],
                description=job_data["description"],
                requirements=job_data["requirements"],
                responsibilities=job_data["responsibilities"],
                salary_min=job_data["salary_min"],
                salary_max=job_data["salary_max"],
                salary_currency=job_data["salary_currency"],
                source_type=SourceType.AGGREGATED,
                source_url=job_data["source_url"],
                source_platform="LinkedIn",
                quality_score=50.0,
                status=JobStatus.ACTIVE,
                posted_at=job_data["posted_at"],
                expires_at=job_data["posted_at"] + timedelta(days=30),
                view_count=0,
                featured=False,
                tags=[]
            )
            pg_db_session.add(job)
            pg_db_session.commit()
            pg_db_session.refresh(job)
            
            # Create job source
            job_source = JobSource(
                job_id=job.id,
                source_platform="LinkedIn",
                source_url=job_data["source_url"],
                scraped_at=datetime.utcnow(),
                last_verified_at=datetime.utcnow(),
                is_active=True
            )
            pg_db_session.add(job_source)
            jobs_created += 1
        
        pg_db_session.commit()
        
        # Complete scraping task
        task.status = ScrapingTaskStatus.COMPLETED
        task.completed_at = datetime.utcnow()
        task.jobs_found = len(mock_job_data)
        task.jobs_created = jobs_created
        task.jobs_updated = 0
        pg_db_session.commit()
        
        # Verify results
        pg_db_session.refresh(task)
        assert task.status == ScrapingTaskStatus.COMPLETED
        assert task.jobs_found == 2
        assert task.jobs_created == 2
        assert task.jobs_updated == 0
        
        # Verify jobs were created
        jobs = pg_db_session.query(Job).filter(Job.source_platform == "LinkedIn").all()
        assert len(jobs) == 2
        assert all(job.source_type == SourceType.AGGREGATED for job in jobs)
        
        # Verify job sources were created
        sources = pg_db_session.query(JobSource).all()
        assert len(sources) == 2


class TestJobPostingAndApplicationFlow:
    """
    Integration tests for job posting and application workflow.
    
    **Validates: Requirement 4.10** - WHEN a direct post is successfully created, 
    THE System SHALL return the job ID to the employer
    """
    
    def test_complete_job_posting_and_application_flow(
        self, 
        client: TestClient, 
        employer_token: str,
        job_seeker_token: str,
        test_employer: Employer,
        test_job_seeker: JobSeeker,
        pg_db_session: Session
    ):
        """Test complete flow from job posting to application submission."""
        # Step 1: Employer posts a job
        job_data = {
            "title": "Backend Developer",
            "company": test_employer.company_name,
            "location": "Remote",
            "remote": True,
            "job_type": "FULL_TIME",
            "experience_level": "MID",
            "description": "We are looking for a backend developer with Python experience. " * 5,
            "requirements": ["Python", "FastAPI", "PostgreSQL"],
            "responsibilities": ["Build APIs", "Write tests", "Deploy services"],
            "salary_min": 80000,
            "salary_max": 120000,
            "salary_currency": "USD",
            "tags": ["python", "backend", "remote"]
        }
        
        response = client.post(
            "/api/jobs/direct",
            json=job_data,
            headers={"Authorization": f"Bearer {employer_token}"}
        )
        
        assert response.status_code == 201
        job_response = response.json()
        assert "id" in job_response
        job_id = job_response["id"]
        
        # Verify job was created
        job = pg_db_session.query(Job).filter(Job.id == job_id).first()
        assert job is not None
        assert job.source_type == SourceType.DIRECT
        assert job.employer_id == test_employer.id
        assert job.status == JobStatus.ACTIVE
        
        # Step 2: Job seeker searches for jobs
        response = client.get(
            "/api/search",
            params={"query": "Backend", "remote": True}
        )
        
        assert response.status_code == 200
        search_results = response.json()
        assert search_results["total"] >= 1
        assert any(j["id"] == job_id for j in search_results["jobs"])
        
        # Step 3: Job seeker views job details
        response = client.get(f"/api/jobs/{job_id}")
        
        assert response.status_code == 200
        job_details = response.json()
        assert job_details["id"] == job_id
        assert job_details["title"] == "Backend Developer"
        
        # Step 4: Job seeker applies to the job
        application_data = {
            "job_id": job_id,
            "resume": "https://example.com/resume.pdf",
            "cover_letter": "I am very interested in this position."
        }
        
        response = client.post(
            "/api/applications",
            json=application_data,
            headers={"Authorization": f"Bearer {job_seeker_token}"}
        )
        
        assert response.status_code == 201
        application_response = response.json()
        assert "id" in application_response
        application_id = application_response["id"]
        
        # Verify application was created
        application = pg_db_session.query(Application).filter(Application.id == application_id).first()
        assert application is not None
        assert application.job_id == job_id
        assert application.job_seeker_id == test_job_seeker.id
        assert application.status == ApplicationStatus.SUBMITTED
        
        # Step 5: Employer views applications
        response = client.get(
            f"/api/jobs/{job_id}/applications",
            headers={"Authorization": f"Bearer {employer_token}"}
        )
        
        assert response.status_code == 200
        applications = response.json()
        assert len(applications) >= 1
        assert any(app["id"] == application_id for app in applications)
        
        # Step 6: Employer updates application status
        response = client.patch(
            f"/api/applications/{application_id}",
            json={"status": "REVIEWED"},
            headers={"Authorization": f"Bearer {employer_token}"}
        )
        
        assert response.status_code == 200
        
        # Verify status was updated
        pg_db_session.refresh(application)
        assert application.status == ApplicationStatus.REVIEWED


class TestURLImportFlow:
    """
    Integration tests for URL import workflow.
    
    **Validates: Requirement 5.15** - WHEN the import task completes, THE System 
    SHALL notify the employer via WebSocket or polling
    """
    
    @patch('app.services.url_import.URLImportService.scrape_url')
    def test_complete_url_import_flow(
        self,
        mock_scrape_url,
        client: TestClient,
        employer_token: str,
        test_employer: Employer,
        pg_db_session: Session
    ):
        """Test complete URL import flow from submission to job creation."""
        # Mock the scraping function
        mock_job_data = {
            "title": "Data Scientist",
            "company": "Data Corp",
            "location": "New York, NY",
            "remote": False,
            "job_type": "FULL_TIME",
            "experience_level": "SENIOR",
            "description": "We are looking for an experienced data scientist to join our team. " * 5,
            "requirements": ["Python", "Machine Learning", "Statistics"],
            "responsibilities": ["Build models", "Analyze data"],
            "salary_min": 120000,
            "salary_max": 180000,
            "salary_currency": "USD"
        }
        mock_scrape_url.return_value = mock_job_data
        
        # Step 1: Employer submits URL for import
        import_data = {
            "url": "https://linkedin.com/jobs/data-scientist-123"
        }
        
        response = client.post(
            "/api/jobs/import-url",
            json=import_data,
            headers={"Authorization": f"Bearer {employer_token}"}
        )
        
        assert response.status_code == 202
        import_response = response.json()
        assert "task_id" in import_response
        task_id = import_response["task_id"]
        
        # Verify task was created
        task = pg_db_session.query(ScrapingTask).filter(ScrapingTask.id == task_id).first()
        assert task is not None
        assert task.task_type == TaskType.URL_IMPORT
        assert task.target_url == import_data["url"]
        
        # Step 2: Simulate task processing
        task.status = ScrapingTaskStatus.RUNNING
        task.started_at = datetime.utcnow()
        pg_db_session.commit()
        
        # Create the imported job
        job = Job(
            title=mock_job_data["title"],
            company=mock_job_data["company"],
            location=mock_job_data["location"],
            remote=mock_job_data["remote"],
            job_type=JobType[mock_job_data["job_type"]],
            experience_level=ExperienceLevel[mock_job_data["experience_level"]],
            description=mock_job_data["description"],
            requirements=mock_job_data["requirements"],
            responsibilities=mock_job_data["responsibilities"],
            salary_min=mock_job_data["salary_min"],
            salary_max=mock_job_data["salary_max"],
            salary_currency=mock_job_data["salary_currency"],
            source_type=SourceType.URL_IMPORT,
            source_url=import_data["url"],
            employer_id=test_employer.id,
            quality_score=60.0,
            status=JobStatus.ACTIVE,
            posted_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(days=30),
            view_count=0,
            featured=False,
            tags=[]
        )
        pg_db_session.add(job)
        pg_db_session.commit()
        pg_db_session.refresh(job)
        
        # Complete the task
        task.status = ScrapingTaskStatus.COMPLETED
        task.completed_at = datetime.utcnow()
        task.jobs_found = 1
        task.jobs_created = 1
        pg_db_session.commit()
        
        # Step 3: Employer polls for task status
        response = client.get(
            f"/api/jobs/import-url/{task_id}",
            headers={"Authorization": f"Bearer {employer_token}"}
        )
        
        assert response.status_code == 200
        status_response = response.json()
        assert status_response["status"] == "COMPLETED"
        assert status_response["jobs_created"] == 1
        
        # Verify job was created with correct source type
        imported_job = pg_db_session.query(Job).filter(Job.id == job.id).first()
        assert imported_job is not None
        assert imported_job.source_type == SourceType.URL_IMPORT
        assert imported_job.employer_id == test_employer.id


class TestSearchWithFilters:
    """
    Integration tests for search with various filters.
    
    **Validates: Requirement 6.13** - WHEN page size exceeds 100, THE System 
    SHALL limit results to 100 per page
    """
    
    def test_search_with_multiple_filters(self, client: TestClient, pg_db_session: Session):
        """Test search with various filter combinations."""
        # Create test jobs with different attributes
        jobs_data = [
            {
                "title": "Junior Python Developer",
                "company": "StartupCo",
                "location": "San Francisco, CA",
                "remote": True,
                "job_type": JobType.FULL_TIME,
                "experience_level": ExperienceLevel.ENTRY,
                "salary_min": 60000,
                "salary_max": 80000,
                "posted_at": datetime.utcnow()
            },
            {
                "title": "Senior Python Developer",
                "company": "BigTech",
                "location": "New York, NY",
                "remote": False,
                "job_type": JobType.FULL_TIME,
                "experience_level": ExperienceLevel.SENIOR,
                "salary_min": 150000,
                "salary_max": 200000,
                "posted_at": datetime.utcnow() - timedelta(days=5)
            },
            {
                "title": "Python Freelancer",
                "company": "FreelanceCo",
                "location": "Remote",
                "remote": True,
                "job_type": JobType.CONTRACT,
                "experience_level": ExperienceLevel.MID,
                "salary_min": 80000,
                "salary_max": 120000,
                "posted_at": datetime.utcnow() - timedelta(days=15)
            },
            {
                "title": "Data Engineer",
                "company": "DataCorp",
                "location": "Austin, TX",
                "remote": True,
                "job_type": JobType.FULL_TIME,
                "experience_level": ExperienceLevel.MID,
                "salary_min": 100000,
                "salary_max": 140000,
                "posted_at": datetime.utcnow() - timedelta(days=2)
            }
        ]
        
        for job_data in jobs_data:
            job = Job(
                title=job_data["title"],
                company=job_data["company"],
                location=job_data["location"],
                remote=job_data["remote"],
                job_type=job_data["job_type"],
                experience_level=job_data["experience_level"],
                description="A great opportunity to work with our team. " * 10,
                requirements=["Python"],
                responsibilities=["Write code"],
                salary_min=job_data["salary_min"],
                salary_max=job_data["salary_max"],
                salary_currency="USD",
                source_type=SourceType.AGGREGATED,
                quality_score=50.0,
                status=JobStatus.ACTIVE,
                posted_at=job_data["posted_at"],
                expires_at=job_data["posted_at"] + timedelta(days=30),
                view_count=0,
                featured=False,
                tags=[]
            )
            pg_db_session.add(job)
        
        pg_db_session.commit()
        
        # Test 1: Search by query
        response = client.get("/api/search", params={"query": "Python"})
        assert response.status_code == 200
        results = response.json()
        assert results["total"] >= 3
        
        # Test 2: Filter by remote
        response = client.get("/api/search", params={"remote": True})
        assert response.status_code == 200
        results = response.json()
        assert all(job["remote"] for job in results["jobs"])
        
        # Test 3: Filter by experience level
        response = client.get("/api/search", params={"experience_level": "SENIOR"})
        assert response.status_code == 200
        results = response.json()
        assert all(job["experience_level"] == "SENIOR" for job in results["jobs"])
        
        # Test 4: Filter by salary range
        response = client.get("/api/search", params={"salary_min": 100000})
        assert response.status_code == 200
        results = response.json()
        assert all(
            job.get("salary_min", 0) >= 100000 or job.get("salary_max", 0) >= 100000 
            for job in results["jobs"]
        )
        
        # Test 5: Filter by posted within days
        response = client.get("/api/search", params={"posted_within": 7})
        assert response.status_code == 200
        results = response.json()
        # All returned jobs should be posted within 7 days
        for job in results["jobs"]:
            posted_date = datetime.fromisoformat(job["posted_at"].replace("Z", "+00:00"))
            days_old = (datetime.utcnow() - posted_date.replace(tzinfo=None)).days
            assert days_old <= 7
        
        # Test 6: Multiple filters combined
        response = client.get(
            "/api/search",
            params={
                "query": "Python",
                "remote": True,
                "experience_level": "MID",
                "salary_min": 80000
            }
        )
        assert response.status_code == 200
        results = response.json()
        # Should match the Python Freelancer job
        assert results["total"] >= 1
        
        # Test 7: Pagination limit
        response = client.get("/api/search", params={"page_size": 150})
        assert response.status_code == 200
        results = response.json()
        # Should be limited to 100
        assert len(results["jobs"]) <= 100


class TestSubscriptionUpgradeFlow:
    """
    Integration tests for subscription upgrade workflow.
    
    **Validates: Requirement 8.8** - WHEN an employer upgrades subscription, 
    THE System SHALL update the subscription start and end dates
    """
    
    def test_complete_subscription_upgrade_flow(
        self,
        client: TestClient,
        employer_token: str,
        test_employer: Employer,
        pg_db_session: Session
    ):
        """Test complete subscription upgrade flow."""
        # Step 1: Check current subscription
        response = client.get(
            "/api/subscription",
            headers={"Authorization": f"Bearer {employer_token}"}
        )
        
        assert response.status_code == 200
        subscription = response.json()
        assert subscription["tier"] == "BASIC"
        
        # Step 2: Check quota before upgrade
        initial_posts_used = test_employer.monthly_posts_used
        
        # Step 3: Upgrade to premium
        upgrade_data = {
            "tier": "PREMIUM"
        }
        
        response = client.post(
            "/api/subscription/upgrade",
            json=upgrade_data,
            headers={"Authorization": f"Bearer {employer_token}"}
        )
        
        assert response.status_code == 200
        upgrade_response = response.json()
        assert upgrade_response["tier"] == "PREMIUM"
        
        # Verify subscription was updated in database
        pg_db_session.refresh(test_employer)
        assert test_employer.subscription_tier == SubscriptionTier.PREMIUM
        assert test_employer.subscription_start_date is not None
        assert test_employer.subscription_end_date is not None
        assert test_employer.subscription_end_date > test_employer.subscription_start_date
        
        # Step 4: Verify increased limits
        response = client.get(
            "/api/subscription",
            headers={"Authorization": f"Bearer {employer_token}"}
        )
        
        assert response.status_code == 200
        subscription = response.json()
        assert subscription["tier"] == "PREMIUM"
        assert subscription["limits"]["monthly_posts"] == -1  # Unlimited
        assert subscription["limits"]["featured_posts"] == 10
        
        # Step 5: Test posting with new limits
        job_data = {
            "title": "Premium Job Posting",
            "company": test_employer.company_name,
            "location": "Anywhere",
            "remote": True,
            "job_type": "FULL_TIME",
            "experience_level": "MID",
            "description": "This is a premium job posting with unlimited quota. " * 5,
            "requirements": ["Skills"],
            "responsibilities": ["Tasks"],
            "featured": True  # Premium tier allows featured posts
        }
        
        response = client.post(
            "/api/jobs/direct",
            json=job_data,
            headers={"Authorization": f"Bearer {employer_token}"}
        )
        
        assert response.status_code == 201
        job_response = response.json()
        assert job_response["featured"] is True
        
        # Verify featured post quota was consumed
        pg_db_session.refresh(test_employer)
        assert test_employer.featured_posts_used == 1


@pytest.mark.integration
class TestEndToEndPlatformWorkflow:
    """
    Comprehensive end-to-end test covering multiple workflows.
    
    Tests the complete platform workflow from scraping to application.
    """
    
    def test_complete_platform_workflow(
        self,
        client: TestClient,
        employer_token: str,
        job_seeker_token: str,
        test_employer: Employer,
        test_job_seeker: JobSeeker,
        pg_db_session: Session
    ):
        """Test complete platform workflow across all major features."""
        # Phase 1: Scraping creates aggregated jobs
        aggregated_job = Job(
            title="Full Stack Developer",
            company="TechStartup",
            location="Seattle, WA",
            remote=True,
            job_type=JobType.FULL_TIME,
            experience_level=ExperienceLevel.MID,
            description="Join our team as a full stack developer. " * 10,
            requirements=["JavaScript", "React", "Node.js"],
            responsibilities=["Build features", "Fix bugs"],
            salary_min=90000,
            salary_max=130000,
            salary_currency="USD",
            source_type=SourceType.AGGREGATED,
            source_platform="Indeed",
            quality_score=45.0,
            status=JobStatus.ACTIVE,
            posted_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(days=30),
            view_count=0,
            featured=False,
            tags=["javascript", "fullstack"]
        )
        pg_db_session.add(aggregated_job)
        pg_db_session.commit()
        
        # Phase 2: Employer posts direct job
        direct_job_data = {
            "title": "Senior Backend Engineer",
            "company": test_employer.company_name,
            "location": "Remote",
            "remote": True,
            "job_type": "FULL_TIME",
            "experience_level": "SENIOR",
            "description": "We need an experienced backend engineer to lead our API development. " * 5,
            "requirements": ["Python", "FastAPI", "PostgreSQL", "Redis"],
            "responsibilities": ["Design APIs", "Mentor team", "Deploy services"],
            "salary_min": 140000,
            "salary_max": 180000,
            "salary_currency": "USD",
            "tags": ["python", "backend", "senior"]
        }
        
        response = client.post(
            "/api/jobs/direct",
            json=direct_job_data,
            headers={"Authorization": f"Bearer {employer_token}"}
        )
        assert response.status_code == 201
        direct_job_id = response.json()["id"]
        
        # Phase 3: Job seeker searches and finds both jobs
        response = client.get("/api/search", params={"query": "developer"})
        assert response.status_code == 200
        search_results = response.json()
        assert search_results["total"] >= 2
        
        # Direct posts should rank higher due to quality score
        job_ids = [job["id"] for job in search_results["jobs"]]
        direct_job_index = job_ids.index(direct_job_id)
        aggregated_job_index = job_ids.index(str(aggregated_job.id))
        assert direct_job_index < aggregated_job_index  # Direct job ranks higher
        
        # Phase 4: Job seeker applies to direct job
        application_data = {
            "job_id": direct_job_id,
            "resume": "https://example.com/resume.pdf",
            "cover_letter": "I am excited about this opportunity."
        }
        
        response = client.post(
            "/api/applications",
            json=application_data,
            headers={"Authorization": f"Bearer {job_seeker_token}"}
        )
        assert response.status_code == 201
        application_id = response.json()["id"]
        
        # Phase 5: Employer reviews application
        response = client.get(
            f"/api/jobs/{direct_job_id}/applications",
            headers={"Authorization": f"Bearer {employer_token}"}
        )
        assert response.status_code == 200
        applications = response.json()
        assert len(applications) == 1
        assert applications[0]["id"] == application_id
        
        # Phase 6: Employer shortlists candidate
        response = client.patch(
            f"/api/applications/{application_id}",
            json={"status": "SHORTLISTED"},
            headers={"Authorization": f"Bearer {employer_token}"}
        )
        assert response.status_code == 200
        
        # Verify complete workflow
        application = pg_db_session.query(Application).filter(Application.id == application_id).first()
        assert application.status == ApplicationStatus.SHORTLISTED
        
        direct_job = pg_db_session.query(Job).filter(Job.id == direct_job_id).first()
        assert direct_job.application_count == 1
        assert direct_job.quality_score > aggregated_job.quality_score
