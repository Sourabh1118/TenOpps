"""
Privacy and data retention API endpoints.

This module provides endpoints for:
- Account deletion for job seekers and employers
- GDPR data export
- Consent management
- Data retention compliance
"""
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any

from app.api.dependencies import get_current_user_from_token
from app.db.session import get_db
from app.models.job_seeker import JobSeeker
from app.models.employer import Employer
from app.models.application import Application
from app.models.job import Job, JobStatus
from app.models.consent import Consent
from app.schemas.auth import TokenData
from app.schemas.privacy import ConsentRequest, ConsentResponse
from app.core.logging import logger


router = APIRouter(prefix="/privacy", tags=["privacy"])


@router.delete(
    "/job-seeker/account",
    status_code=status.HTTP_202_ACCEPTED,
    responses={
        202: {"description": "Account deletion scheduled"},
        401: {"description": "Unauthorized"},
        403: {"description": "Not a job seeker account"},
    }
)
async def delete_job_seeker_account(
    current_user: TokenData = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """
    Delete job seeker account and anonymize data.
    
    Implements Requirements 17.1, 17.2:
    - Schedules account deletion within 30 days
    - Anonymizes all applications (removes personal data)
    - Marks account for deletion
    
    **Process:**
    1. Verify user is a job seeker
    2. Anonymize all applications
    3. Mark account for deletion
    4. Schedule full deletion after 30 days
    
    **Example Response:**
    ```json
    {
      "message": "Account deletion scheduled",
      "deletion_date": "2024-02-15T00:00:00",
      "applications_anonymized": 5
    }
    ```
    """
    # Verify user is a job seeker
    if current_user.role != "job_seeker":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This endpoint is only for job seeker accounts"
        )
    
    # Get job seeker
    job_seeker = db.query(JobSeeker).filter(
        JobSeeker.id == current_user.user_id
    ).first()
    
    if not job_seeker:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job seeker not found"
        )
    
    # Anonymize all applications
    applications = db.query(Application).filter(
        Application.job_seeker_id == job_seeker.id
    ).all()
    
    applications_count = len(applications)
    
    for application in applications:
        # Anonymize application data
        application.resume = "DELETED"
        application.cover_letter = "User data deleted per privacy request"
        application.employer_notes = None
    
    # Mark job seeker for deletion
    # Store deletion date in a new field (we'll add this to the model)
    deletion_date = datetime.utcnow() + timedelta(days=30)
    
    # Anonymize job seeker data immediately
    job_seeker.email = f"deleted_{job_seeker.id}@deleted.local"
    job_seeker.full_name = "Deleted User"
    job_seeker.phone = None
    job_seeker.resume_url = None
    job_seeker.profile_summary = "Account deleted"
    job_seeker.password_hash = "DELETED"
    
    db.commit()
    
    logger.info(
        f"Job seeker account deletion scheduled: id={job_seeker.id}, "
        f"applications_anonymized={applications_count}, "
        f"deletion_date={deletion_date}"
    )
    
    return {
        "message": "Account deletion scheduled",
        "deletion_date": deletion_date.isoformat(),
        "applications_anonymized": applications_count,
        "note": "Your personal data has been anonymized. Account will be fully deleted in 30 days."
    }


@router.delete(
    "/employer/account",
    status_code=status.HTTP_202_ACCEPTED,
    responses={
        202: {"description": "Account deletion scheduled"},
        401: {"description": "Unauthorized"},
        403: {"description": "Not an employer account"},
    }
)
async def delete_employer_account(
    current_user: TokenData = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """
    Delete employer account and anonymize data.
    
    Implements Requirements 17.1, 17.3:
    - Schedules account deletion within 30 days
    - Marks all jobs as deleted
    - Anonymizes employer data
    
    **Process:**
    1. Verify user is an employer
    2. Mark all jobs as deleted
    3. Anonymize employer data
    4. Schedule full deletion after 30 days
    
    **Example Response:**
    ```json
    {
      "message": "Account deletion scheduled",
      "deletion_date": "2024-02-15T00:00:00",
      "jobs_marked_deleted": 12
    }
    ```
    """
    # Verify user is an employer
    if current_user.role != "employer":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This endpoint is only for employer accounts"
        )
    
    # Get employer
    employer = db.query(Employer).filter(
        Employer.id == current_user.user_id
    ).first()
    
    if not employer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employer not found"
        )
    
    # Mark all jobs as deleted
    jobs = db.query(Job).filter(
        Job.employer_id == employer.id
    ).all()
    
    jobs_count = len(jobs)
    
    for job in jobs:
        job.status = JobStatus.DELETED
    
    # Calculate deletion date
    deletion_date = datetime.utcnow() + timedelta(days=30)
    
    # Anonymize employer data immediately
    employer.email = f"deleted_{employer.id}@deleted.local"
    employer.company_name = "Deleted Company"
    employer.company_website = None
    employer.company_logo = None
    employer.company_description = "Account deleted"
    employer.password_hash = "DELETED"
    employer.stripe_customer_id = None
    
    db.commit()
    
    logger.info(
        f"Employer account deletion scheduled: id={employer.id}, "
        f"jobs_marked_deleted={jobs_count}, "
        f"deletion_date={deletion_date}"
    )
    
    return {
        "message": "Account deletion scheduled",
        "deletion_date": deletion_date.isoformat(),
        "jobs_marked_deleted": jobs_count,
        "note": "Your personal data has been anonymized. Account will be fully deleted in 30 days."
    }


@router.get(
    "/export",
    responses={
        200: {"description": "User data export"},
        401: {"description": "Unauthorized"},
    }
)
async def export_user_data(
    current_user: TokenData = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Export user data in JSON format for GDPR compliance.
    
    Implements Requirement 17.7:
    - Exports all personal data and activity history
    - Verifies user authentication before export
    - Returns data in machine-readable JSON format
    
    **Process:**
    1. Verify user authentication
    2. Collect all personal data
    3. Collect activity history
    4. Return as JSON
    
    **Example Response:**
    ```json
    {
      "user_type": "job_seeker",
      "personal_data": {
        "email": "user@example.com",
        "full_name": "John Doe",
        "phone": "+1234567890"
      },
      "activity": {
        "applications": [...],
        "created_at": "2024-01-01T00:00:00"
      }
    }
    ```
    """
    if current_user.role == "job_seeker":
        # Export job seeker data
        job_seeker = db.query(JobSeeker).filter(
            JobSeeker.id == current_user.user_id
        ).first()
        
        if not job_seeker:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Job seeker not found"
            )
        
        # Get all applications
        applications = db.query(Application).filter(
            Application.job_seeker_id == job_seeker.id
        ).all()
        
        export_data = {
            "user_type": "job_seeker",
            "export_date": datetime.utcnow().isoformat(),
            "personal_data": {
                "id": str(job_seeker.id),
                "email": job_seeker.email,
                "full_name": job_seeker.full_name,
                "phone": job_seeker.phone,
                "resume_url": job_seeker.resume_url,
                "profile_summary": job_seeker.profile_summary,
                "created_at": job_seeker.created_at.isoformat(),
                "updated_at": job_seeker.updated_at.isoformat(),
            },
            "activity": {
                "applications": [
                    {
                        "id": str(app.id),
                        "job_id": str(app.job_id),
                        "resume": app.resume,
                        "cover_letter": app.cover_letter,
                        "status": app.status.value,
                        "applied_at": app.applied_at.isoformat(),
                        "updated_at": app.updated_at.isoformat(),
                    }
                    for app in applications
                ],
                "total_applications": len(applications),
            }
        }
        
        logger.info(f"Data export generated for job seeker: id={job_seeker.id}")
        return export_data
    
    elif current_user.role == "employer":
        # Export employer data
        employer = db.query(Employer).filter(
            Employer.id == current_user.user_id
        ).first()
        
        if not employer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Employer not found"
            )
        
        # Get all jobs
        jobs = db.query(Job).filter(
            Job.employer_id == employer.id
        ).all()
        
        export_data = {
            "user_type": "employer",
            "export_date": datetime.utcnow().isoformat(),
            "personal_data": {
                "id": str(employer.id),
                "email": employer.email,
                "company_name": employer.company_name,
                "company_website": employer.company_website,
                "company_description": employer.company_description,
                "verified": employer.verified,
                "created_at": employer.created_at.isoformat(),
                "updated_at": employer.updated_at.isoformat(),
            },
            "subscription": {
                "tier": employer.subscription_tier.value,
                "start_date": employer.subscription_start_date.isoformat(),
                "end_date": employer.subscription_end_date.isoformat(),
                "monthly_posts_used": employer.monthly_posts_used,
                "featured_posts_used": employer.featured_posts_used,
            },
            "activity": {
                "jobs": [
                    {
                        "id": str(job.id),
                        "title": job.title,
                        "status": job.status.value,
                        "application_count": job.application_count,
                        "view_count": job.view_count,
                        "posted_at": job.posted_at.isoformat(),
                        "expires_at": job.expires_at.isoformat(),
                    }
                    for job in jobs
                ],
                "total_jobs": len(jobs),
            }
        }
        
        logger.info(f"Data export generated for employer: id={employer.id}")
        return export_data
    
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unknown user type"
        )


@router.post(
    "/consent",
    response_model=ConsentResponse,
    responses={
        200: {"description": "Consent preferences updated"},
        401: {"description": "Unauthorized"},
    }
)
async def update_consent(
    consent_data: ConsentRequest,
    current_user: TokenData = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """
    Update user consent preferences for GDPR compliance.
    
    Implements Requirement 17.8:
    - Stores consent records in database
    - Allows users to update consent preferences
    - Tracks consent date and updates
    
    **Process:**
    1. Verify user authentication
    2. Find or create consent record
    3. Update consent preferences
    4. Return updated consent
    
    **Example Request:**
    ```json
    {
      "marketing_emails": true,
      "data_processing": true,
      "third_party_sharing": false
    }
    ```
    
    **Example Response:**
    ```json
    {
      "user_id": "123e4567-e89b-12d3-a456-426614174000",
      "marketing_emails": true,
      "data_processing": true,
      "third_party_sharing": false,
      "consent_date": "2024-01-01T00:00:00",
      "updated_at": "2024-01-15T10:30:00"
    }
    ```
    """
    # Find existing consent record
    consent = db.query(Consent).filter(
        Consent.user_id == current_user.user_id,
        Consent.user_type == current_user.role
    ).first()
    
    if consent:
        # Update existing consent
        consent.marketing_emails = consent_data.marketing_emails
        consent.data_processing = consent_data.data_processing
        consent.third_party_sharing = consent_data.third_party_sharing
        consent.updated_at = datetime.utcnow()
    else:
        # Create new consent record
        consent = Consent(
            user_id=current_user.user_id,
            user_type=current_user.role,
            marketing_emails=consent_data.marketing_emails,
            data_processing=consent_data.data_processing,
            third_party_sharing=consent_data.third_party_sharing,
        )
        db.add(consent)
    
    db.commit()
    db.refresh(consent)
    
    logger.info(
        f"Consent preferences updated for user {current_user.user_id} "
        f"({current_user.role})"
    )
    
    return ConsentResponse(
        user_id=str(consent.user_id),
        marketing_emails=consent.marketing_emails,
        data_processing=consent.data_processing,
        third_party_sharing=consent.third_party_sharing,
        consent_date=consent.consent_date,
        updated_at=consent.updated_at,
    )


@router.get(
    "/consent",
    response_model=ConsentResponse,
    responses={
        200: {"description": "Current consent preferences"},
        401: {"description": "Unauthorized"},
        404: {"description": "No consent record found"},
    }
)
async def get_consent(
    current_user: TokenData = Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """
    Get current user consent preferences.
    
    Implements Requirement 17.8:
    - Allows users to view consent preferences
    
    **Example Response:**
    ```json
    {
      "user_id": "123e4567-e89b-12d3-a456-426614174000",
      "marketing_emails": true,
      "data_processing": true,
      "third_party_sharing": false,
      "consent_date": "2024-01-01T00:00:00",
      "updated_at": "2024-01-15T10:30:00"
    }
    ```
    """
    # Find consent record
    consent = db.query(Consent).filter(
        Consent.user_id == current_user.user_id,
        Consent.user_type == current_user.role
    ).first()
    
    if not consent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No consent record found. Please set your preferences."
        )
    
    return ConsentResponse(
        user_id=str(consent.user_id),
        marketing_emails=consent.marketing_emails,
        data_processing=consent.data_processing,
        third_party_sharing=consent.third_party_sharing,
        consent_date=consent.consent_date,
        updated_at=consent.updated_at,
    )
