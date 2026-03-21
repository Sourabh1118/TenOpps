"""
Application service for the job aggregation platform.

This module provides functions for managing job applications including:
- Application submission
- Application retrieval for employers and job seekers
- Application status updates
"""
from typing import List, Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.application import Application, ApplicationStatus
from app.models.job import Job, SourceType
from app.models.job_seeker import JobSeeker
from app.core.logging import logger
from app.services.analytics import AnalyticsService


def create_application(
    db: Session,
    job_id: UUID,
    job_seeker_id: UUID,
    resume: str,
    cover_letter: Optional[str] = None
) -> Application:
    """
    Create a new job application.
    
    This function implements Requirements 7.4, 7.5, 7.6, 7.7, 7.8, and 7.9:
    - Creates application record with status='submitted'
    - Associates with job and job seeker
    - Stores resume file URL
    - Stores cover letter if provided
    - Increments job's application count
    
    Args:
        db: Database session
        job_id: Job UUID
        job_seeker_id: Job seeker UUID
        resume: Resume file URL
        cover_letter: Optional cover letter text
        
    Returns:
        Created Application instance
        
    Raises:
        ValueError: If job is not a direct post or doesn't exist
        
    Example:
        >>> application = create_application(
        ...     db, job_id, job_seeker_id,
        ...     "https://storage.example.com/resume.pdf",
        ...     "I am excited to apply..."
        ... )
    """
    # Verify job exists and is a direct post
    job = db.query(Job).filter(Job.id == job_id).first()
    
    if not job:
        raise ValueError("Job not found")
    
    if job.source_type != SourceType.DIRECT:
        raise ValueError("Applications can only be submitted to direct posts")
    
    # Create application record
    application = Application(
        job_id=job_id,
        job_seeker_id=job_seeker_id,
        resume=resume,
        cover_letter=cover_letter,
        status=ApplicationStatus.SUBMITTED,
        applied_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    db.add(application)
    
    # Increment job's application count
    job.application_count += 1
    
    try:
        db.commit()
        db.refresh(application)
        logger.info(f"Application created: {application.id} for job {job_id} by job seeker {job_seeker_id}")
        
        # Track application analytics (Requirement 19.6)
        if job.employer_id:
            try:
                analytics = AnalyticsService(db)
                analytics.track_job_event(
                    job_id=job.id,
                    employer_id=job.employer_id,
                    event_type="application",
                    user_id=job_seeker_id,
                )
            except Exception as e:
                # Don't fail the application if analytics tracking fails
                logger.error(f"Error tracking application analytics: {e}")
        
        return application
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating application: {e}")
        raise


def get_applications_for_job(
    db: Session,
    job_id: UUID,
    employer_id: UUID
) -> List[dict]:
    """
    Get all applications for a specific job.
    
    This function implements Requirements 7.10 and 9.4:
    - Fetches all applications for the job
    - Verifies employer owns the job
    - Includes applicant name, resume URL, status, applied date
    
    Args:
        db: Database session
        job_id: Job UUID
        employer_id: Employer UUID
        
    Returns:
        List of application dictionaries with job seeker info
        
    Raises:
        ValueError: If job not found or employer doesn't own the job
        
    Example:
        >>> applications = get_applications_for_job(db, job_id, employer_id)
    """
    # Verify job exists and employer owns it
    job = db.query(Job).filter(Job.id == job_id).first()
    
    if not job:
        raise ValueError("Job not found")
    
    if job.employer_id != employer_id:
        raise ValueError("You can only view applications for your own jobs")
    
    # Fetch applications with job seeker info
    applications = (
        db.query(Application, JobSeeker)
        .join(JobSeeker, Application.job_seeker_id == JobSeeker.id)
        .filter(Application.job_id == job_id)
        .order_by(Application.applied_at.desc())
        .all()
    )
    
    # Format results
    results = []
    for application, job_seeker in applications:
        results.append({
            "id": application.id,
            "job_id": application.job_id,
            "job_seeker_id": application.job_seeker_id,
            "applicant_name": job_seeker.full_name,
            "resume": application.resume,
            "cover_letter": application.cover_letter,
            "status": application.status,
            "employer_notes": application.employer_notes,
            "applied_at": application.applied_at,
            "updated_at": application.updated_at
        })
    
    logger.info(f"Retrieved {len(results)} applications for job {job_id}")
    return results


def get_applications_for_job_seeker(
    db: Session,
    job_seeker_id: UUID
) -> List[dict]:
    """
    Get all applications for a specific job seeker.
    
    This function implements Requirement 7.10:
    - Fetches all applications for the job seeker
    - Includes job details and current status
    
    Args:
        db: Database session
        job_seeker_id: Job seeker UUID
        
    Returns:
        List of application dictionaries with job info
        
    Example:
        >>> applications = get_applications_for_job_seeker(db, job_seeker_id)
    """
    # Fetch applications with job info
    applications = (
        db.query(Application, Job)
        .join(Job, Application.job_id == Job.id)
        .filter(Application.job_seeker_id == job_seeker_id)
        .order_by(Application.applied_at.desc())
        .all()
    )
    
    # Format results
    results = []
    for application, job in applications:
        results.append({
            "id": application.id,
            "job_id": application.job_id,
            "job_title": job.title,
            "company": job.company,
            "location": job.location,
            "resume": application.resume,
            "cover_letter": application.cover_letter,
            "status": application.status,
            "applied_at": application.applied_at,
            "updated_at": application.updated_at
        })
    
    logger.info(f"Retrieved {len(results)} applications for job seeker {job_seeker_id}")
    return results


def update_application_status(
    db: Session,
    application_id: UUID,
    employer_id: UUID,
    new_status: ApplicationStatus,
    employer_notes: Optional[str] = None
) -> Application:
    """
    Update application status.
    
    This function implements Requirements 7.11 and 7.12:
    - Verifies employer owns the job
    - Validates new status
    - Updates application status and timestamp
    - Allows employer to add notes
    
    Args:
        db: Database session
        application_id: Application UUID
        employer_id: Employer UUID
        new_status: New application status
        employer_notes: Optional employer notes
        
    Returns:
        Updated Application instance
        
    Raises:
        ValueError: If application not found or employer doesn't own the job
        
    Example:
        >>> application = update_application_status(
        ...     db, application_id, employer_id,
        ...     ApplicationStatus.SHORTLISTED,
        ...     "Strong candidate"
        ... )
    """
    # Fetch application with job
    application = (
        db.query(Application)
        .filter(Application.id == application_id)
        .first()
    )
    
    if not application:
        raise ValueError("Application not found")
    
    # Verify employer owns the job
    job = db.query(Job).filter(Job.id == application.job_id).first()
    
    if not job or job.employer_id != employer_id:
        raise ValueError("You can only update applications for your own jobs")
    
    # Update status and notes
    application.status = new_status
    application.updated_at = datetime.utcnow()
    
    if employer_notes is not None:
        application.employer_notes = employer_notes
    
    try:
        db.commit()
        db.refresh(application)
        logger.info(f"Application {application_id} status updated to {new_status}")
        return application
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating application status: {e}")
        raise


def check_existing_application(
    db: Session,
    job_id: UUID,
    job_seeker_id: UUID
) -> bool:
    """
    Check if job seeker has already applied to this job.
    
    Args:
        db: Database session
        job_id: Job UUID
        job_seeker_id: Job seeker UUID
        
    Returns:
        True if application exists, False otherwise
        
    Example:
        >>> has_applied = check_existing_application(db, job_id, job_seeker_id)
    """
    existing = (
        db.query(Application)
        .filter(
            and_(
                Application.job_id == job_id,
                Application.job_seeker_id == job_seeker_id
            )
        )
        .first()
    )
    
    return existing is not None
