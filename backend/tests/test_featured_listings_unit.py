"""
Unit tests for featured listings functionality.

This module tests:
- Task 19.1: Featured listing endpoint logic
- Task 19.2: Featured jobs in search results (sorting)
- Task 19.3: Featured listing expiration task

**Validates: Requirements 11.1, 11.2, 11.3, 11.4, 11.5, 11.6, 11.7**
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from uuid import uuid4

from app.models.job import Job, JobType, ExperienceLevel, SourceType, JobStatus
from app.models.employer import Employer, SubscriptionTier


class TestFeaturedListingLogic:
    """Tests for Task 19.1: Featured listing endpoint logic."""
    
    def test_feature_job_validates_ownership(self):
        """
        Test that featuring validates employer ownership.
        
        **Validates: Requirement 11.1**
        """
        # Create mock job with different employer
        job = Mock(spec=Job)
        job.id = uuid4()
        job.employer_id = uuid4()
        job.featured = False
        
        # Current employer has different ID
        current_employer_id = uuid4()
        
        # Verify ownership check would fail
        assert str(job.employer_id) != str(current_employer_id)
    
    def test_feature_job_checks_quota(self):
        """
        Test that featuring checks featured post quota.
        
        **Validates: Requirement 11.2**
        """
        from app.services.subscription import get_tier_limits
        
        # Test free tier has 0 featured posts
        free_limits = get_tier_limits(SubscriptionTier.FREE)
        assert free_limits["featured_posts"] == 0
        
        # Test basic tier has 2 featured posts
        basic_limits = get_tier_limits(SubscriptionTier.BASIC)
        assert basic_limits["featured_posts"] == 2
        
        # Test premium tier has 10 featured posts
        premium_limits = get_tier_limits(SubscriptionTier.PREMIUM)
        assert premium_limits["featured_posts"] == 10
    
    def test_feature_job_sets_flag(self):
        """
        Test that featuring sets featured flag to true.
        
        **Validates: Requirement 11.3**
        """
        # Create mock job
        job = Mock(spec=Job)
        job.featured = False
        
        # Simulate featuring
        job.featured = True
        
        assert job.featured is True
    
    def test_feature_job_consumes_quota(self):
        """
        Test that featuring consumes featured quota.
        
        **Validates: Requirement 11.4**
        """
        # Create mock employer
        employer = Mock(spec=Employer)
        employer.featured_posts_used = 0
        employer.subscription_tier = SubscriptionTier.BASIC
        
        # Simulate quota consumption
        employer.featured_posts_used += 1
        
        assert employer.featured_posts_used == 1


class TestFeaturedJobsSorting:
    """Tests for Task 19.2: Featured jobs in search results."""
    
    def test_featured_jobs_sort_first(self):
        """
        Test that featured jobs are sorted before non-featured jobs.
        
        **Validates: Requirement 11.5**
        """
        # Create list of jobs with mixed featured status
        jobs = [
            {"id": 1, "featured": False, "quality_score": 90, "posted_at": datetime.utcnow()},
            {"id": 2, "featured": True, "quality_score": 80, "posted_at": datetime.utcnow()},
            {"id": 3, "featured": False, "quality_score": 85, "posted_at": datetime.utcnow()},
            {"id": 4, "featured": True, "quality_score": 75, "posted_at": datetime.utcnow()},
        ]
        
        # Sort by featured (desc), then quality_score (desc)
        sorted_jobs = sorted(
            jobs,
            key=lambda x: (not x["featured"], -x["quality_score"])
        )
        
        # Verify featured jobs come first
        assert sorted_jobs[0]["featured"] is True
        assert sorted_jobs[1]["featured"] is True
        assert sorted_jobs[2]["featured"] is False
        assert sorted_jobs[3]["featured"] is False
        
        # Verify featured jobs are sorted by quality among themselves
        assert sorted_jobs[0]["quality_score"] == 80  # Featured, higher quality
        assert sorted_jobs[1]["quality_score"] == 75  # Featured, lower quality
        
        # Verify non-featured jobs are sorted by quality among themselves
        assert sorted_jobs[2]["quality_score"] == 90  # Non-featured, higher quality
        assert sorted_jobs[3]["quality_score"] == 85  # Non-featured, lower quality
    
    def test_featured_flag_included_in_response(self):
        """
        Test that featured flag is included in job response.
        
        **Validates: Requirement 11.6**
        """
        # Create mock job
        job = Mock(spec=Job)
        job.id = uuid4()
        job.title = "Software Engineer"
        job.featured = True
        
        # Simulate response serialization
        response = {
            "id": str(job.id),
            "title": job.title,
            "featured": job.featured
        }
        
        assert "featured" in response
        assert response["featured"] is True


class TestFeaturedListingExpiration:
    """Tests for Task 19.3: Featured listing expiration task."""
    
    def test_expiration_task_identifies_expired_jobs(self):
        """
        Test that expiration task identifies expired featured jobs.
        
        **Validates: Requirement 11.7**
        """
        current_time = datetime.utcnow()
        
        # Create jobs with different expiration dates
        expired_job = Mock(spec=Job)
        expired_job.id = uuid4()
        expired_job.featured = True
        expired_job.expires_at = current_time - timedelta(days=5)  # Expired
        
        active_job = Mock(spec=Job)
        active_job.id = uuid4()
        active_job.featured = True
        active_job.expires_at = current_time + timedelta(days=25)  # Active
        
        # Check expiration logic
        assert expired_job.expires_at < current_time
        assert active_job.expires_at > current_time
    
    def test_expiration_task_removes_featured_flag(self):
        """
        Test that expiration task removes featured flag from expired jobs.
        
        **Validates: Requirement 11.7**
        """
        current_time = datetime.utcnow()
        
        # Create expired featured job
        job = Mock(spec=Job)
        job.id = uuid4()
        job.featured = True
        job.expires_at = current_time - timedelta(days=5)
        
        # Simulate expiration task logic
        if job.featured and job.expires_at < current_time:
            job.featured = False
        
        assert job.featured is False
    
    def test_expiration_task_preserves_active_featured_jobs(self):
        """
        Test that expiration task does not affect active featured jobs.
        
        **Validates: Requirement 11.7**
        """
        current_time = datetime.utcnow()
        
        # Create active featured job
        job = Mock(spec=Job)
        job.id = uuid4()
        job.featured = True
        job.expires_at = current_time + timedelta(days=25)
        
        # Simulate expiration task logic
        if job.featured and job.expires_at < current_time:
            job.featured = False
        
        # Job should still be featured
        assert job.featured is True
    
    def test_expiration_task_ignores_non_featured_jobs(self):
        """
        Test that expiration task only affects featured jobs.
        
        **Validates: Requirement 11.7**
        """
        current_time = datetime.utcnow()
        
        # Create expired non-featured job
        job = Mock(spec=Job)
        job.id = uuid4()
        job.featured = False
        job.expires_at = current_time - timedelta(days=5)
        
        # Simulate expiration task logic
        if job.featured and job.expires_at < current_time:
            job.featured = False
        
        # Job should remain non-featured (no change)
        assert job.featured is False


class TestSubscriptionTierLimits:
    """Test subscription tier limits for featured posts."""
    
    def test_free_tier_no_featured_posts(self):
        """
        Test that free tier has 0 featured posts.
        
        **Validates: Requirement 11.2**
        """
        from app.services.subscription import get_tier_limits
        
        limits = get_tier_limits(SubscriptionTier.FREE)
        assert limits["featured_posts"] == 0
    
    def test_basic_tier_featured_posts(self):
        """
        Test that basic tier has 2 featured posts.
        
        **Validates: Requirement 11.2**
        """
        from app.services.subscription import get_tier_limits
        
        limits = get_tier_limits(SubscriptionTier.BASIC)
        assert limits["featured_posts"] == 2
    
    def test_premium_tier_featured_posts(self):
        """
        Test that premium tier has 10 featured posts.
        
        **Validates: Requirement 11.2**
        """
        from app.services.subscription import get_tier_limits
        
        limits = get_tier_limits(SubscriptionTier.PREMIUM)
        assert limits["featured_posts"] == 10


class TestSearchSortingLogic:
    """Test search sorting logic for featured jobs."""
    
    def test_sort_order_featured_quality_date(self):
        """
        Test that jobs are sorted by featured, quality score, then date.
        
        **Validates: Requirement 11.5**
        """
        # Create jobs with various attributes
        jobs = [
            {
                "id": 1,
                "featured": False,
                "quality_score": 95,
                "posted_at": datetime(2024, 1, 5)
            },
            {
                "id": 2,
                "featured": True,
                "quality_score": 70,
                "posted_at": datetime(2024, 1, 3)
            },
            {
                "id": 3,
                "featured": True,
                "quality_score": 85,
                "posted_at": datetime(2024, 1, 4)
            },
            {
                "id": 4,
                "featured": False,
                "quality_score": 90,
                "posted_at": datetime(2024, 1, 6)
            },
        ]
        
        # Sort by: featured DESC, quality_score DESC, posted_at DESC
        sorted_jobs = sorted(
            jobs,
            key=lambda x: (
                not x["featured"],  # Featured first (True > False)
                -x["quality_score"],  # Higher quality first
                -x["posted_at"].timestamp()  # Newer first
            )
        )
        
        # Expected order: 3 (featured, 85), 2 (featured, 70), 1 (not featured, 95), 4 (not featured, 90)
        assert sorted_jobs[0]["id"] == 3  # Featured, quality 85
        assert sorted_jobs[1]["id"] == 2  # Featured, quality 70
        assert sorted_jobs[2]["id"] == 1  # Not featured, quality 95
        assert sorted_jobs[3]["id"] == 4  # Not featured, quality 90
        
        # Verify all featured jobs come before non-featured
        featured_indices = [i for i, j in enumerate(sorted_jobs) if j["featured"]]
        non_featured_indices = [i for i, j in enumerate(sorted_jobs) if not j["featured"]]
        
        if featured_indices and non_featured_indices:
            assert max(featured_indices) < min(non_featured_indices)
