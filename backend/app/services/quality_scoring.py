"""
Quality scoring service for the job aggregation platform.

This module provides functions for calculating quality scores for job postings
based on source type, field completeness, and freshness.
"""
from datetime import datetime
from typing import Dict, Any, Optional
from app.models.job import SourceType
from app.core.logging import logger


def clamp_score(score: float, min_val: float = 0.0, max_val: float = 100.0) -> float:
    """
    Clamp a score value between minimum and maximum bounds.
    
    Args:
        score: Score value to clamp
        min_val: Minimum allowed value (default: 0.0)
        max_val: Maximum allowed value (default: 100.0)
        
    Returns:
        Clamped score value
        
    Example:
        >>> clamp_score(150.0)
        100.0
        >>> clamp_score(-10.0)
        0.0
        >>> clamp_score(75.5)
        75.5
    """
    return max(min_val, min(score, max_val))


def calculate_base_score(source_type: SourceType) -> float:
    """
    Calculate base quality score based on job source type.
    
    This function implements Requirements 3.1, 3.2, and 3.3:
    - Direct posts: 70 points (highest quality, verified employers)
    - URL imports: 50 points (medium quality, employer-curated)
    - Aggregated jobs: 30 points (lower quality, automated scraping)
    
    Args:
        source_type: Type of job source (DIRECT, URL_IMPORT, or AGGREGATED)
        
    Returns:
        Base score as float (30.0, 50.0, or 70.0)
        
    Example:
        >>> calculate_base_score(SourceType.DIRECT)
        70.0
        >>> calculate_base_score(SourceType.URL_IMPORT)
        50.0
        >>> calculate_base_score(SourceType.AGGREGATED)
        30.0
    """
    base_scores = {
        SourceType.DIRECT: 70.0,
        SourceType.URL_IMPORT: 50.0,
        SourceType.AGGREGATED: 30.0,
    }
    
    score = base_scores.get(source_type, 30.0)
    logger.debug(f"Base score for {source_type.value}: {score}")
    return score


def calculate_completeness_score(job_data: Dict[str, Any]) -> float:
    """
    Calculate completeness score based on presence of optional fields.
    
    This function implements Requirement 3.4:
    - Awards up to 20 points for field completeness
    - Each of 5 fields is worth 4 points
    - Fields checked: requirements, responsibilities, salary_min, salary_max, tags
    
    Args:
        job_data: Dictionary containing job fields
        
    Returns:
        Completeness score as float (0.0 to 20.0)
        
    Example:
        >>> job_data = {
        ...     "requirements": ["Python", "Django"],
        ...     "responsibilities": ["Build APIs"],
        ...     "salary_min": 100000,
        ...     "salary_max": 150000,
        ...     "tags": ["python"]
        ... }
        >>> calculate_completeness_score(job_data)
        20.0
    """
    score = 0.0
    points_per_field = 4.0
    
    # Check requirements field (non-empty list)
    if job_data.get("requirements") and len(job_data["requirements"]) > 0:
        score += points_per_field
    
    # Check responsibilities field (non-empty list)
    if job_data.get("responsibilities") and len(job_data["responsibilities"]) > 0:
        score += points_per_field
    
    # Check salary_min field (not None and > 0)
    if job_data.get("salary_min") is not None and job_data["salary_min"] > 0:
        score += points_per_field
    
    # Check salary_max field (not None and > 0)
    if job_data.get("salary_max") is not None and job_data["salary_max"] > 0:
        score += points_per_field
    
    # Check tags field (non-empty list)
    if job_data.get("tags") and len(job_data["tags"]) > 0:
        score += points_per_field
    
    logger.debug(f"Completeness score: {score}/20.0")
    return score


def calculate_freshness_score(posted_at: datetime) -> float:
    """
    Calculate freshness score based on job age.
    
    This function implements Requirements 3.5, 3.6, 3.7, 3.8, 3.9, and 3.10:
    - <1 day old: 10 points
    - 1-7 days old: 8 points
    - 8-14 days old: 6 points
    - 15-30 days old: 4 points
    - >30 days old: 2 points
    
    Args:
        posted_at: Datetime when job was posted
        
    Returns:
        Freshness score as float (2.0 to 10.0)
        
    Example:
        >>> from datetime import datetime, timedelta
        >>> now = datetime.utcnow()
        >>> calculate_freshness_score(now)  # Just posted
        10.0
        >>> calculate_freshness_score(now - timedelta(days=5))  # 5 days old
        8.0
        >>> calculate_freshness_score(now - timedelta(days=10))  # 10 days old
        6.0
    """
    now = datetime.utcnow()
    age = now - posted_at
    days_old = age.days
    
    if days_old < 1:
        score = 10.0
    elif days_old <= 7:
        score = 8.0
    elif days_old <= 14:
        score = 6.0
    elif days_old <= 30:
        score = 4.0
    else:
        score = 2.0
    
    logger.debug(f"Freshness score for {days_old} days old: {score}")
    return score


def calculate_quality_score(
    source_type: SourceType,
    job_data: Dict[str, Any],
    posted_at: Optional[datetime] = None
) -> float:
    """
    Calculate overall quality score for a job posting.
    
    This function implements Requirement 4.6 and combines:
    - Base score (30-70 points based on source type)
    - Completeness score (0-20 points based on field completeness)
    - Freshness score (2-10 points based on job age)
    
    Final score is clamped between 0 and 100.
    
    Args:
        source_type: Type of job source (DIRECT, URL_IMPORT, or AGGREGATED)
        job_data: Dictionary containing job fields
        posted_at: Datetime when job was posted (defaults to now)
        
    Returns:
        Overall quality score as float (0.0 to 100.0)
        
    Example:
        >>> from datetime import datetime
        >>> job_data = {
        ...     "requirements": ["Python"],
        ...     "responsibilities": ["Build APIs"],
        ...     "salary_min": 100000,
        ...     "salary_max": 150000,
        ...     "tags": ["python"]
        ... }
        >>> score = calculate_quality_score(
        ...     SourceType.DIRECT,
        ...     job_data,
        ...     datetime.utcnow()
        ... )
        >>> score
        100.0  # 70 (base) + 20 (completeness) + 10 (freshness)
    """
    if posted_at is None:
        posted_at = datetime.utcnow()
    
    # Calculate component scores
    base = calculate_base_score(source_type)
    completeness = calculate_completeness_score(job_data)
    freshness = calculate_freshness_score(posted_at)
    
    # Combine scores
    total_score = base + completeness + freshness
    
    # Clamp to valid range
    final_score = clamp_score(total_score)
    
    logger.info(
        f"Quality score calculated: {final_score:.1f} "
        f"(base={base}, completeness={completeness}, freshness={freshness})"
    )
    
    return final_score
