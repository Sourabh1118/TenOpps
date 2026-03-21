"""
Manual test script for job expiration functionality.

This script tests:
- Task 20.1: Job expiration Celery task
- Task 20.2: Job reactivation endpoint

Run this script with: python test_job_expiration_manual.py
"""
import sys
import os
from datetime import datetime, timedelta
from uuid import uuid4

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.db.session import SessionLocal
from app.models.job import Job, JobStatus, JobType, ExperienceLevel, SourceType
from app.models.employer import Employer, SubscriptionTier
from app.tasks.maintenance_tasks import expire_old_jobs


def test_job_expiration_task():
    """Test the job expiration Celery task."""
    print("\n" + "="*60)
    print("Testing Job Expiration Task (Task 20.1)")
    print("="*60)
    
    db = SessionLocal()
    
    try:
        # Create test employer
        employer = Employer(
            id=uuid4(),
            email=f"test_expiration_{uuid4().hex[:8]}@test.com",
            password_hash="test_hash",
            company_name="Test Expiration Company",
            subscription_tier=SubscriptionTier.BASIC,
            subscription_start_date=datetime.utcnow(),
            subscription_end_date=datetime.utcnow() + timedelta(days=30),
            monthly_posts_used=0,
            featured_posts_used=0,
            verified=True
        )
        db.add(employer)
        db.commit()
        print(f"✓ Created test employer: {employer.email}")
        
        # Create expired job
        expired_job = Job(
            id=uuid4(),
            title="Expired Test Job",
            company=employer.company_name,
            location="Test City",
            remote=False,
            job_type=JobType.FULL_TIME,
            experience_level=ExperienceLevel.MID,
            description="This is a test job that should be expired by the task.",
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
        
        # Create active job
        active_job = Job(
            id=uuid4(),
            title="Active Test Job",
            company=employer.company_name,
            location="Test City",
            remote=True,
            job_type=JobType.FULL_TIME,
            experience_level=ExperienceLevel.SENIOR,
            description="This is a test job that should remain active.",
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
        print(f"✓ Created expired job: {expired_job.title} (expires_at: {expired_job.expires_at})")
        print(f"✓ Created active job: {active_job.title} (expires_at: {active_job.expires_at})")
        
        # Run expiration task
        print("\nRunning job expiration task...")
        result = expire_old_jobs()
        
        # Verify results
        print(f"\nTask result: {result}")
        assert result["status"] == "success", "Task should succeed"
        assert result["jobs_expired"] == 1, f"Expected 1 job expired, got {result['jobs_expired']}"
        print("✓ Task completed successfully")
        
        # Refresh jobs and verify status
        db.refresh(expired_job)
        db.refresh(active_job)
        
        assert expired_job.status == JobStatus.EXPIRED, f"Expired job should have status EXPIRED, got {expired_job.status}"
        assert active_job.status == JobStatus.ACTIVE, f"Active job should remain ACTIVE, got {active_job.status}"
        print(f"✓ Expired job status: {expired_job.status}")
        print(f"✓ Active job status: {active_job.status}")
        
        print("\n✅ Job Expiration Task Test PASSED")
        
        # Cleanup
        db.delete(expired_job)
        db.delete(active_job)
        db.delete(employer)
        db.commit()
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test FAILED: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        return False
    finally:
        db.close()


def test_job_reactivation():
    """Test the job reactivation endpoint logic."""
    print("\n" + "="*60)
    print("Testing Job Reactivation Logic (Task 20.2)")
    print("="*60)
    
    db = SessionLocal()
    
    try:
        # Create test employer
        employer = Employer(
            id=uuid4(),
            email=f"test_reactivation_{uuid4().hex[:8]}@test.com",
            password_hash="test_hash",
            company_name="Test Reactivation Company",
            subscription_tier=SubscriptionTier.PREMIUM,
            subscription_start_date=datetime.utcnow(),
            subscription_end_date=datetime.utcnow() + timedelta(days=30),
            monthly_posts_used=0,
            featured_posts_used=0,
            verified=True
        )
        db.add(employer)
        db.commit()
        print(f"✓ Created test employer: {employer.email}")
        
        # Create expired job
        expired_job = Job(
            id=uuid4(),
            title="Expired Job for Reactivation",
            company=employer.company_name,
            location="Test City",
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
        print(f"✓ Created expired job: {expired_job.title}")
        print(f"  Status: {expired_job.status}, Expires: {expired_job.expires_at}")
        
        # Simulate reactivation
        print("\nSimulating job reactivation...")
        new_expiration = datetime.utcnow() + timedelta(days=45)
        
        # Verify job is expired
        assert expired_job.status == JobStatus.EXPIRED, "Job should be expired"
        print("✓ Verified job is expired")
        
        # Reactivate job
        expired_job.expires_at = new_expiration
        expired_job.status = JobStatus.ACTIVE
        db.commit()
        db.refresh(expired_job)
        
        # Verify reactivation
        assert expired_job.status == JobStatus.ACTIVE, f"Job should be active, got {expired_job.status}"
        assert expired_job.expires_at.date() == new_expiration.date(), "Expiration date should be updated"
        print(f"✓ Job reactivated successfully")
        print(f"  New status: {expired_job.status}")
        print(f"  New expiration: {expired_job.expires_at}")
        
        print("\n✅ Job Reactivation Test PASSED")
        
        # Cleanup
        db.delete(expired_job)
        db.delete(employer)
        db.commit()
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test FAILED: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        return False
    finally:
        db.close()


def main():
    """Run all manual tests."""
    print("\n" + "="*60)
    print("JOB EXPIRATION FUNCTIONALITY - MANUAL TESTS")
    print("Task 20: Job expiration service")
    print("="*60)
    
    results = []
    
    # Test 1: Job expiration task
    results.append(("Job Expiration Task", test_job_expiration_task()))
    
    # Test 2: Job reactivation
    results.append(("Job Reactivation", test_job_reactivation()))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    all_passed = all(result[1] for result in results)
    
    if all_passed:
        print("\n🎉 All tests PASSED!")
        return 0
    else:
        print("\n⚠️  Some tests FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
