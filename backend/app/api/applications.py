"""
Application API endpoints.

This module provides endpoints for job application management including:
- Application submission by job seekers
- Application retrieval for employers and job seekers
- Application status updates by employers
"""
from uuid import UUID
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_employer, get_current_job_seeker
from app.db.session import get_db
from app.models.application import ApplicationStatus
from app.schemas.auth import TokenData
from app.schemas.application import (
    ApplicationSubmitRequest,
    ApplicationSubmitResponse,
    ApplicationStatusUpdateRequest,
    ApplicationResponse,
    ApplicationWithJobSeekerInfo,
    ApplicationWithJobInfo,
    ApplicationListResponse,
    MyApplicationsListResponse,
    ErrorResponse,
)
from app.services.application import (
    create_application,
    get_applications_for_job,
    get_applications_for_job_seeker,
    update_application_status,
    check_existing_application,
)
from app.services.subscription import check_quota, get_tier_limits
from app.models.employer import Employer


router = APIRouter(prefix="/applications", tags=["applications"])


@router.post(
    "",
    response_model=ApplicationSubmitResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid input or job not eligible"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        409: {"model": ErrorResponse, "description": "Already applied to this job"},
    }
)
async def submit_application(
    application_data: ApplicationSubmitRequest,
    job_seeker: TokenData = Depends(get_current_job_seeker),
    db: Session = Depends(get_db)
):
    """
    Submit a job application.
    
    This endpoint implements Requirements 7.1, 7.2, and 7.3:
    - Validates job seeker authentication
    - Validates that job is a direct post (not aggregated)
    - Requires resume file upload
    - Accepts optional cover letter
    
    **Process:**
    1. Validate job seeker authentication
    2. Check if job seeker has already applied
    3. Validate job is a direct post
    4. Create application record
    5. Increment job's application count
    6. Return application ID
    
    **Example Request:**
    ```json
    {
      "job_id": "123e4567-e89b-12d3-a456-426614174000",
      "resume": "https://storage.example.com/resumes/john-doe-resume.pdf",
      "cover_letter": "I am excited to apply for this position..."
    }
    ```
    
    **Example Response:**
    ```json
    {
      "application_id": "223e4567-e89b-12d3-a456-426614174000",
      "message": "Application submitted successfully"
    }
    ```
    """
    job_seeker_id = UUID(job_seeker.user_id)
    
    # Check if already applied
    if check_existing_application(db, application_data.job_id, job_seeker_id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You have already applied to this job"
        )
    
    # Create application
    try:
        application = create_application(
            db=db,
            job_id=application_data.job_id,
            job_seeker_id=job_seeker_id,
            resume=application_data.resume,
            cover_letter=application_data.cover_letter
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit application: {str(e)}"
        )
    
    return ApplicationSubmitResponse(
        application_id=application.id,
        message="Application submitted successfully"
    )


@router.get(
    "/job/{job_id}",
    response_model=ApplicationListResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden - requires basic or premium tier"},
        404: {"model": ErrorResponse, "description": "Job not found"},
    }
)
async def get_job_applications(
    job_id: UUID,
    employer: TokenData = Depends(get_current_employer),
    db: Session = Depends(get_db)
):
    """
    Get all applications for a specific job.
    
    This endpoint implements Requirements 7.10, 9.4, 9.5, and 9.9:
    - Verifies employer owns the job
    - Returns all applications for the job
    - Includes applicant name, resume URL, status, applied date
    - Verifies employer has basic or premium tier for access
    
    **Query Parameters:**
    - job_id: UUID of the job
    
    **Example Response:**
    ```json
    {
      "applications": [
        {
          "id": "123e4567-e89b-12d3-a456-426614174000",
          "job_id": "223e4567-e89b-12d3-a456-426614174000",
          "job_seeker_id": "323e4567-e89b-12d3-a456-426614174000",
          "applicant_name": "John Doe",
          "resume": "https://storage.example.com/resumes/john-doe-resume.pdf",
          "cover_letter": "I am excited to apply...",
          "status": "submitted",
          "employer_notes": null,
          "applied_at": "2024-01-15T10:30:00Z",
          "updated_at": "2024-01-15T10:30:00Z"
        }
      ],
      "total": 1
    }
    ```
    """
    employer_id = UUID(employer.user_id)
    
    # Verify employer has application tracking access (basic or premium tier)
    employer_record = db.query(Employer).filter(Employer.id == employer_id).first()
    
    if not employer_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employer not found"
        )
    
    tier_limits = get_tier_limits(employer_record.subscription_tier)
    if not tier_limits.get("has_application_tracking", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Application tracking requires basic or premium subscription tier"
        )
    
    # Get applications
    try:
        applications = get_applications_for_job(db, job_id, employer_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve applications: {str(e)}"
        )
    
    # Convert to response models
    application_responses = [
        ApplicationWithJobSeekerInfo(**app) for app in applications
    ]
    
    return ApplicationListResponse(
        applications=application_responses,
        total=len(application_responses)
    )


@router.patch(
    "/{application_id}",
    response_model=ApplicationResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden"},
        404: {"model": ErrorResponse, "description": "Application not found"},
    }
)
async def update_application(
    application_id: UUID,
    update_data: ApplicationStatusUpdateRequest,
    employer: TokenData = Depends(get_current_employer),
    db: Session = Depends(get_db)
):
    """
    Update application status.
    
    This endpoint implements Requirements 7.11 and 7.12:
    - Verifies employer owns the job
    - Validates new status (SUBMITTED, REVIEWED, SHORTLISTED, REJECTED, ACCEPTED)
    - Updates application status and timestamp
    - Allows employer to add notes
    
    **Example Request:**
    ```json
    {
      "status": "shortlisted",
      "employer_notes": "Strong candidate, schedule interview"
    }
    ```
    
    **Example Response:**
    ```json
    {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "job_id": "223e4567-e89b-12d3-a456-426614174000",
      "job_seeker_id": "323e4567-e89b-12d3-a456-426614174000",
      "resume": "https://storage.example.com/resumes/john-doe-resume.pdf",
      "cover_letter": "I am excited to apply...",
      "status": "shortlisted",
      "employer_notes": "Strong candidate, schedule interview",
      "applied_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-01-15T14:30:00Z"
    }
    ```
    """
    employer_id = UUID(employer.user_id)
    
    # Update application
    try:
        application = update_application_status(
            db=db,
            application_id=application_id,
            employer_id=employer_id,
            new_status=update_data.status,
            employer_notes=update_data.employer_notes
        )
    except ValueError as e:
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=str(e)
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update application: {str(e)}"
        )
    
    return ApplicationResponse.model_validate(application)


@router.get(
    "/my-applications",
    response_model=MyApplicationsListResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
    }
)
async def get_my_applications(
    job_seeker: TokenData = Depends(get_current_job_seeker),
    db: Session = Depends(get_db)
):
    """
    Get all applications for the authenticated job seeker.
    
    This endpoint implements Requirement 7.10:
    - Returns all applications for authenticated job seeker
    - Includes job details and current status
    
    **Example Response:**
    ```json
    {
      "applications": [
        {
          "id": "123e4567-e89b-12d3-a456-426614174000",
          "job_id": "223e4567-e89b-12d3-a456-426614174000",
          "job_title": "Senior Python Developer",
          "company": "Tech Corp",
          "location": "San Francisco, CA",
          "resume": "https://storage.example.com/resumes/john-doe-resume.pdf",
          "cover_letter": "I am excited to apply...",
          "status": "submitted",
          "applied_at": "2024-01-15T10:30:00Z",
          "updated_at": "2024-01-15T10:30:00Z"
        }
      ],
      "total": 1
    }
    ```
    """
    job_seeker_id = UUID(job_seeker.user_id)
    
    # Get applications
    try:
        applications = get_applications_for_job_seeker(db, job_seeker_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve applications: {str(e)}"
        )
    
    # Convert to response models
    application_responses = [
        ApplicationWithJobInfo(**app) for app in applications
    ]
    
    return MyApplicationsListResponse(
        applications=application_responses,
        total=len(application_responses)
    )
