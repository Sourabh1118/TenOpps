"""
Tests for job archival task.

This module tests:
- Archiving jobs older than 180 days
- Preserving recent jobs
- Task execution and logging
"""
import pytest
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.models.job import Job, JobType, ExperienceLevel, SourceType, JobStatus
from app.tasks.maintenance_tasks import archive_old_jobs


def test_archive_old_jobs(db: Session):
    """Test archiving jobs older than 180 days."""
    # Create old job (200 days old)
    old_job = Job(
        title="Old Software Engineer Position",
        company="Old Company",
        location="San Francisco",
        remote=False,
        job_type=JobType.FULL_TIME,
        experience_level=ExperienceLevel.MID,
        description="This is an old job that should be archived for testing",
        source_type=SourceType.AGGREGATED,
        quality_score=50.0,
        status=JobStatus.EXPIRED,
        posted_at=datetime.utcnow() - timedelta(days=200),
        expires_at=datetime.utcnow() - timedelta(days=170),
    )
    db.add(old_job)
    
    # Create recent job (30 days old)
    recent_job = Job(
        title="Recent Software Engineer Position",
        company="Recent Company",
        location="New York",
        remote=True,
        job_type=JobType.FULL_TIME,
        experience_level=ExperienceLevel.SENIOR,
        description="This is a recent job that should not be archived yet",
        source_type=SourceType.DIRECT,
        quality_score=75.0,
        status=JobStatus.ACTIVE,
        posted_at=datetime.utcnow() - timedelta(days=30),
        expires_at=datetime.utcnow() + timedelta(days=30),
    )
    db.add(recent_job)
    
    # Create job at boundary (exactly 180 days old)
    boundary_job = Job(
        title="Boundary Software Engineer Position",
        company="Boundary Company",
        location="Austin",
        remote=False,
        job_type=JobType.CONTRACT,
        experience_level=ExperienceLevel.MID,
        description="This job is exactly at the 180 day boundary for testing",
        source_type=SourceType.URL_IMPORT,
        quality_score=60.0,
        status=JobStatus.FILLED,
        posted_at=datetime.utcnow() - timedelta(days=180),
        expires_at=datetime.utcnow() - timedelta(days=150),
    )
    db.add(boundary_job)
    
    db.commit()
    
    # Run archival task
    result = archive_old_jobs()
    
    # Verify results
    assert result["status"] == "success"
    assert result["jobs_archived"] >= 1  # At least the old job
    
    # Verify old job was archived
    db.refresh(old_job)
    assert old_job.status == JobStatus.DELETED
    
    # Verify recent job was not archived
    db.refresh(recent_job)
    assert recent_job.status == JobStatus.ACTIVE
    
    # Verify boundary job was archived (>= 180 days)
    db.refresh(boundary_job)
    assert boundary_job.status == JobStatus.DELETED


def test_archive_only_active_expired_filled(db: Session):
    """Test that only active, expired, and filled jobs are archived."""
    # Create old job that's already deleted
    deleted_job = Job(
        title="Already Deleted Job",
        company="Test Company",
        location="Boston",
        remote=False,
        job_type=JobType.FULL_TIME,
        experience_level=ExperienceLevel.ENTRY,
        description="This job is already deleted and should not be counted",
        source_type=SourceType.AGGREGATED,
        quality_score=40.0,
        status=JobStatus.DELETED,
        posted_at=datetime.utcnow() - timedelta(days=200),
        expires_at=datetime.utcnow() - timedelta(days=170),
    )
    db.add(deleted_job)
    
    # Create old active job
    active_job = Job(
        title="Old Active Job",
        company="Active Company",
        location="Seattle",
        remote=True,
        job_type=JobType.PART_TIME,
        experience_level=ExperienceLevel.MID,
        description="This is an old active job that should be archived now",
        source_type=SourceType.DIRECT,
        quality_score=70.0,
        status=JobStatus.ACTIVE,
        posted_at=datetime.utcnow() - timedelta(days=190),
        expires_at=datetime.utcnow() - timedelta(days=160),
    )
    db.add(active_job)
    
    db.commit()
    
    # Run archival task
    result = archive_old_jobs()
    
    # Verify only the active job was archived
    db.refresh(deleted_job)
    assert deleted_job.status == JobStatus.DELETED  # Still deleted
    
    db.refresh(active_job)
    assert active_job.status == JobStatus.DELETED  # Now deleted


def test_archive_empty_database(db: Session):
    """Test archival task with no jobs to archive."""
    # Run archival task on empty database
    result = archive_old_jobs()
    
    # Should complete successfully with 0 jobs archived
    assert result["status"] == "success"
    assert result["jobs_archived"] == 0


def test_archive_multiple_old_jobs(db: Session):
    """Test archiving multiple old jobs at once."""
    # Create multiple old jobs
    for i in range(5):
        job = Job(
            title=f"Old Job {i}",
            company=f"Company {i}",
            location="Various",
            remote=i % 2 == 0,
            job_type=JobType.FULL_TIME,
            experience_level=ExperienceLevel.MID,
            description=f"Old job number {i} for bulk archival testing purposes",
            source_type=SourceType.AGGREGATED,
            quality_score=50.0 + i,
            status=JobStatus.EXPIRED,
            posted_at=datetime.utcnow() - timedelta(days=200 + i),
            expires_at=datetime.utcnow() - timedelta(days=170 + i),
        )
        db.add(job)
    
    db.commit()
    
    # Run archival task
    result = archive_old_jobs()
    
    # Verify all 5 jobs were archived
    assert result["status"] == "success"
    assert result["jobs_archived"] == 5
