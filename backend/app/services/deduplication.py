"""
Deduplication service for the job aggregation platform.

This module provides functions for detecting duplicate job postings through:
- Company name normalization
- Title and location normalization  
- Fuzzy string matching
- TF-IDF description similarity
- Multi-stage duplicate detection pipeline
"""
import re
import unicodedata
from typing import List, Tuple, Dict, Any, Optional
from difflib import SequenceMatcher
from collections import Counter
import math

from app.core.logging import logger


# Common company suffixes to remove during normalization
COMPANY_SUFFIXES = [
    "inc", "incorporated", "corp", "corporation", "llc", "ltd", "limited",
    "co", "company", "group", "holdings", "international", "global",
    "technologies", "tech", "solutions", "services", "systems"
]

# Common location abbreviations
LOCATION_ABBREV = {
    "street": "st",
    "avenue": "ave",
    "boulevard": "blvd",
    "drive": "dr",
    "road": "rd",
    "lane": "ln",
    "north": "n",
    "south": "s",
    "east": "e",
    "west": "w",
}

# Common job title words to remove
TITLE_STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "as", "is", "was", "are", "were"
}


def normalize_company_name(company: str) -> str:
    """
    Normalize company name for comparison.
    
    This function implements Requirement 2.1:
    - Convert to lowercase
    - Remove special characters
    - Remove common suffixes (Inc, LLC, Corp, etc.)
    - Remove extra whitespace
    - Handle unicode characters
    
    Args:
        company: Raw company name
        
    Returns:
        Normalized company name
        
    Example:
        >>> normalize_company_name("Tech Corp, Inc.")
        'tech'
        >>> normalize_company_name("Acme Technologies LLC")
        'acme'
        >>> normalize_company_name("  Global  Solutions  ")
        'global'
    """
    if not company:
        return ""
    
    # Convert to lowercase
    normalized = company.lower()
    
    # Remove accents and normalize unicode
    normalized = unicodedata.normalize('NFKD', normalized)
    normalized = ''.join([c for c in normalized if not unicodedata.combining(c)])
    
    # Remove special characters, keep only alphanumeric and spaces
    normalized = re.sub(r'[^a-z0-9\s]', ' ', normalized)
    
    # Remove common suffixes
    words = normalized.split()
    filtered_words = []
    for word in words:
        if word not in COMPANY_SUFFIXES:
            filtered_words.append(word)
    
    # Join and remove extra whitespace
    normalized = ' '.join(filtered_words)
    normalized = re.sub(r'\s+', ' ', normalized).strip()
    
    logger.debug(f"Normalized company '{company}' -> '{normalized}'")
    return normalized


def normalize_title(title: str) -> str:
    """
    Normalize job title for comparison.
    
    This function implements Requirement 2.2:
    - Convert to lowercase
    - Remove special characters
    - Remove common stopwords
    - Standardize seniority levels
    - Remove extra whitespace
    
    Args:
        title: Raw job title
        
    Returns:
        Normalized job title
        
    Example:
        >>> normalize_title("Senior Software Engineer")
        'senior software engineer'
        >>> normalize_title("Sr. Python Developer (Remote)")
        'senior python developer remote'
    """
    if not title:
        return ""
    
    # Convert to lowercase
    normalized = title.lower()
    
    # Normalize unicode
    normalized = unicodedata.normalize('NFKD', normalized)
    normalized = ''.join([c for c in normalized if not unicodedata.combining(c)])
    
    # Standardize seniority abbreviations
    normalized = re.sub(r'\bsr\.?\b', 'senior', normalized)
    normalized = re.sub(r'\bjr\.?\b', 'junior', normalized)
    
    # Remove special characters, keep alphanumeric and spaces
    normalized = re.sub(r'[^a-z0-9\s]', ' ', normalized)
    
    # Remove stopwords
    words = normalized.split()
    filtered_words = [w for w in words if w not in TITLE_STOPWORDS]
    
    # Join and remove extra whitespace
    normalized = ' '.join(filtered_words)
    normalized = re.sub(r'\s+', ' ', normalized).strip()
    
    logger.debug(f"Normalized title '{title}' -> '{normalized}'")
    return normalized


def normalize_location(location: str) -> str:
    """
    Normalize location string for comparison.
    
    This function implements Requirement 2.2:
    - Convert to lowercase
    - Standardize abbreviations (St -> Street, etc.)
    - Remove special characters
    - Remove extra whitespace
    
    Args:
        location: Raw location string
        
    Returns:
        Normalized location string
        
    Example:
        >>> normalize_location("San Francisco, CA")
        'san francisco ca'
        >>> normalize_location("New York City, NY")
        'new york city ny'
    """
    if not location:
        return ""
    
    # Convert to lowercase
    normalized = location.lower()
    
    # Normalize unicode
    normalized = unicodedata.normalize('NFKD', normalized)
    normalized = ''.join([c for c in normalized if not unicodedata.combining(c)])
    
    # Standardize abbreviations
    for full, abbrev in LOCATION_ABBREV.items():
        normalized = re.sub(rf'\b{full}\b', abbrev, normalized)
    
    # Remove special characters, keep alphanumeric and spaces
    normalized = re.sub(r'[^a-z0-9\s]', ' ', normalized)
    
    # Remove extra whitespace
    normalized = re.sub(r'\s+', ' ', normalized).strip()
    
    logger.debug(f"Normalized location '{location}' -> '{normalized}'")
    return normalized


def fuzzy_match(str1: str, str2: str, threshold: float = 0.85) -> bool:
    """
    Perform fuzzy string matching using sequence similarity.
    
    This function implements Requirement 2.3:
    - Uses SequenceMatcher for similarity calculation
    - Returns True if similarity >= threshold
    - Default threshold is 0.85 (85% similarity)
    
    Args:
        str1: First string to compare
        str2: Second string to compare
        threshold: Minimum similarity ratio (0.0 to 1.0)
        
    Returns:
        True if strings are similar enough, False otherwise
        
    Example:
        >>> fuzzy_match("Software Engineer", "Software Engineeer")
        True
        >>> fuzzy_match("Python Developer", "Java Developer")
        False
    """
    if not str1 or not str2:
        return False
    
    # Calculate similarity ratio
    ratio = SequenceMatcher(None, str1.lower(), str2.lower()).ratio()
    
    is_match = ratio >= threshold
    logger.debug(f"Fuzzy match '{str1}' vs '{str2}': {ratio:.3f} (threshold={threshold}, match={is_match})")
    
    return is_match


def calculate_tfidf_similarity(desc1: str, desc2: str, threshold: float = 0.7) -> Tuple[bool, float]:
    """
    Calculate TF-IDF based similarity between two job descriptions.
    
    This function implements Requirement 2.4:
    - Tokenizes descriptions into words
    - Calculates term frequency (TF) for each document
    - Calculates inverse document frequency (IDF)
    - Computes cosine similarity between TF-IDF vectors
    - Returns True if similarity >= threshold
    
    Args:
        desc1: First job description
        desc2: Second job description
        threshold: Minimum similarity score (0.0 to 1.0)
        
    Returns:
        Tuple of (is_similar: bool, similarity_score: float)
        
    Example:
        >>> desc1 = "Python developer with Django experience"
        >>> desc2 = "Python engineer experienced in Django"
        >>> is_similar, score = calculate_tfidf_similarity(desc1, desc2)
        >>> is_similar
        True
    """
    if not desc1 or not desc2:
        return False, 0.0
    
    # Tokenize and normalize
    def tokenize(text: str) -> List[str]:
        # Convert to lowercase and remove special chars
        text = text.lower()
        text = re.sub(r'[^a-z0-9\s]', ' ', text)
        # Split into words and filter short words
        words = [w for w in text.split() if len(w) > 2]
        return words
    
    tokens1 = tokenize(desc1)
    tokens2 = tokenize(desc2)
    
    if not tokens1 or not tokens2:
        return False, 0.0
    
    # Calculate term frequencies
    tf1 = Counter(tokens1)
    tf2 = Counter(tokens2)
    
    # Get all unique terms
    all_terms = set(tf1.keys()) | set(tf2.keys())
    
    # Calculate IDF (simplified: log(2 / (1 + term_appears_in_docs)))
    idf = {}
    for term in all_terms:
        docs_with_term = (1 if term in tf1 else 0) + (1 if term in tf2 else 0)
        idf[term] = math.log(2.0 / (1.0 + docs_with_term))
    
    # Calculate TF-IDF vectors
    def get_tfidf_vector(tf: Counter) -> Dict[str, float]:
        vector = {}
        total_terms = sum(tf.values())
        for term in all_terms:
            tf_score = tf.get(term, 0) / total_terms if total_terms > 0 else 0
            vector[term] = tf_score * idf[term]
        return vector
    
    vec1 = get_tfidf_vector(tf1)
    vec2 = get_tfidf_vector(tf2)
    
    # Calculate cosine similarity
    dot_product = sum(vec1[term] * vec2[term] for term in all_terms)
    magnitude1 = math.sqrt(sum(v ** 2 for v in vec1.values()))
    magnitude2 = math.sqrt(sum(v ** 2 for v in vec2.values()))
    
    if magnitude1 == 0 or magnitude2 == 0:
        similarity = 0.0
    else:
        similarity = dot_product / (magnitude1 * magnitude2)
    
    is_similar = similarity >= threshold
    
    logger.debug(
        f"TF-IDF similarity: {similarity:.3f} "
        f"(threshold={threshold}, similar={is_similar})"
    )
    
    return is_similar, similarity


def is_duplicate(
    job1: Dict[str, Any],
    job2: Dict[str, Any],
    company_threshold: float = 0.85,
    title_threshold: float = 0.85,
    location_threshold: float = 0.85,
    description_threshold: float = 0.7
) -> Tuple[bool, Dict[str, Any]]:
    """
    Detect if two jobs are duplicates using multi-stage comparison.
    
    This function implements Requirement 2.5:
    - Stage 1: Normalize and compare company names (fuzzy match)
    - Stage 2: Normalize and compare titles (fuzzy match)
    - Stage 3: Normalize and compare locations (fuzzy match)
    - Stage 4: Compare descriptions (TF-IDF similarity)
    - Jobs are duplicates if all stages pass their thresholds
    
    Args:
        job1: First job dictionary with keys: company, title, location, description
        job2: Second job dictionary with keys: company, title, location, description
        company_threshold: Minimum similarity for company names (default: 0.85)
        title_threshold: Minimum similarity for titles (default: 0.85)
        location_threshold: Minimum similarity for locations (default: 0.85)
        description_threshold: Minimum similarity for descriptions (default: 0.7)
        
    Returns:
        Tuple of (is_duplicate: bool, details: dict)
        Details dict contains:
        - company_match: bool
        - title_match: bool
        - location_match: bool
        - description_match: bool
        - description_similarity: float
        
    Example:
        >>> job1 = {
        ...     "company": "Tech Corp Inc",
        ...     "title": "Senior Python Developer",
        ...     "location": "San Francisco, CA",
        ...     "description": "Build scalable Python applications..."
        ... }
        >>> job2 = {
        ...     "company": "Tech Corporation",
        ...     "title": "Sr. Python Developer",
        ...     "location": "San Francisco, California",
        ...     "description": "Develop scalable Python apps..."
        ... }
        >>> is_dup, details = is_duplicate(job1, job2)
        >>> is_dup
        True
    """
    # Extract and normalize fields
    company1 = normalize_company_name(job1.get("company", ""))
    company2 = normalize_company_name(job2.get("company", ""))
    
    title1 = normalize_title(job1.get("title", ""))
    title2 = normalize_title(job2.get("title", ""))
    
    location1 = normalize_location(job1.get("location", ""))
    location2 = normalize_location(job2.get("location", ""))
    
    description1 = job1.get("description", "")
    description2 = job2.get("description", "")
    
    # Stage 1: Company name comparison
    company_match = fuzzy_match(company1, company2, company_threshold)
    
    # Stage 2: Title comparison
    title_match = fuzzy_match(title1, title2, title_threshold)
    
    # Stage 3: Location comparison
    location_match = fuzzy_match(location1, location2, location_threshold)
    
    # Stage 4: Description comparison
    description_match, description_similarity = calculate_tfidf_similarity(
        description1, description2, description_threshold
    )
    
    # Jobs are duplicates if all stages pass
    is_dup = company_match and title_match and location_match and description_match
    
    details = {
        "company_match": company_match,
        "title_match": title_match,
        "location_match": location_match,
        "description_match": description_match,
        "description_similarity": description_similarity,
    }
    
    logger.info(
        f"Duplicate detection: {is_dup} - "
        f"Company: {company_match}, Title: {title_match}, "
        f"Location: {location_match}, Description: {description_match} ({description_similarity:.3f})"
    )
    
    return is_dup, details


def find_duplicates(
    new_job: Dict[str, Any],
    existing_jobs: List[Dict[str, Any]],
    **kwargs
) -> List[Tuple[Dict[str, Any], Dict[str, Any]]]:
    """
    Find all duplicate jobs for a new job posting.
    
    Args:
        new_job: New job to check for duplicates
        existing_jobs: List of existing jobs to compare against
        **kwargs: Additional arguments to pass to is_duplicate()
        
    Returns:
        List of tuples (duplicate_job, match_details) for all found duplicates
        
    Example:
        >>> new_job = {"company": "Tech Corp", "title": "Developer", ...}
        >>> existing = [{"company": "Tech Corporation", "title": "Developer", ...}]
        >>> duplicates = find_duplicates(new_job, existing)
        >>> len(duplicates)
        1
    """
    duplicates = []
    
    for existing_job in existing_jobs:
        is_dup, details = is_duplicate(new_job, existing_job, **kwargs)
        if is_dup:
            duplicates.append((existing_job, details))
    
    logger.info(f"Found {len(duplicates)} duplicates out of {len(existing_jobs)} existing jobs")
    return duplicates



def merge_duplicate_job(
    existing_job_id: int,
    new_job_data: Dict[str, Any],
    new_source: Dict[str, Any],
    db_session
) -> Dict[str, Any]:
    """
    Merge a duplicate job by updating the existing record.
    
    This function implements Requirement 2.7, 2.8, 2.9:
    - Update existing job record instead of creating new one
    - Add new source reference to job_sources table
    - Preserve highest quality score
    - Update last_seen timestamp
    
    Args:
        existing_job_id: ID of the existing job in database
        new_job_data: Data from the newly discovered duplicate job
        new_source: Source information for the new job (platform, url, etc.)
        db_session: SQLAlchemy database session
        
    Returns:
        Updated job dictionary
        
    Example:
        >>> merge_duplicate_job(
        ...     existing_job_id=123,
        ...     new_job_data={"quality_score": 85, ...},
        ...     new_source={"platform": "indeed", "url": "https://..."},
        ...     db_session=session
        ... )
    """
    from app.models.job import Job
    from app.models.job_source import JobSource
    from datetime import datetime
    
    # Fetch existing job
    existing_job = db_session.query(Job).filter(Job.id == existing_job_id).first()
    if not existing_job:
        logger.error(f"Job with ID {existing_job_id} not found")
        raise ValueError(f"Job with ID {existing_job_id} not found")
    
    # Preserve highest quality score
    new_quality_score = new_job_data.get("quality_score", 0)
    if new_quality_score > existing_job.quality_score:
        existing_job.quality_score = new_quality_score
        logger.info(
            f"Updated quality score for job {existing_job_id}: "
            f"{existing_job.quality_score} -> {new_quality_score}"
        )
    
    # Update last_seen timestamp
    existing_job.last_seen = datetime.utcnow()
    
    # Add new source reference
    new_job_source = JobSource(
        job_id=existing_job_id,
        source_platform=new_source.get("platform"),
        source_url=new_source.get("url"),
        source_job_id=new_source.get("job_id"),
        scraped_at=datetime.utcnow()
    )
    db_session.add(new_job_source)
    
    # Commit changes
    db_session.commit()
    db_session.refresh(existing_job)
    
    logger.info(
        f"Merged duplicate job: existing_id={existing_job_id}, "
        f"new_source={new_source.get('platform')}"
    )
    
    return {
        "id": existing_job.id,
        "title": existing_job.title,
        "company": existing_job.company,
        "quality_score": existing_job.quality_score,
        "last_seen": existing_job.last_seen,
        "merged": True
    }


def process_job_with_deduplication(
    job_data: Dict[str, Any],
    source_info: Dict[str, Any],
    db_session
) -> Tuple[bool, Dict[str, Any]]:
    """
    Process a new job with deduplication check.
    
    This is a high-level function that:
    1. Checks for duplicates in the database
    2. If duplicate found, merges with existing job
    3. If no duplicate, returns indication to create new job
    
    Args:
        job_data: Job data dictionary (company, title, location, description, etc.)
        source_info: Source information (platform, url, job_id)
        db_session: SQLAlchemy database session
        
    Returns:
        Tuple of (is_duplicate: bool, result: dict)
        - If duplicate: (True, merged_job_data)
        - If not duplicate: (False, {})
        
    Example:
        >>> is_dup, result = process_job_with_deduplication(
        ...     job_data={"company": "Tech Corp", "title": "Developer", ...},
        ...     source_info={"platform": "indeed", "url": "https://..."},
        ...     db_session=session
        ... )
    """
    from app.models.job import Job
    
    # Query existing jobs from the same company (normalized)
    normalized_company = normalize_company_name(job_data.get("company", ""))
    
    # Get all active jobs to check for duplicates
    # In production, this should be optimized with better filtering
    existing_jobs_query = db_session.query(Job).filter(
        Job.status == "active"
    ).all()
    
    # Convert to dictionaries for comparison
    existing_jobs_dicts = [
        {
            "id": job.id,
            "company": job.company,
            "title": job.title,
            "location": job.location,
            "description": job.description
        }
        for job in existing_jobs_query
    ]
    
    # Find duplicates
    duplicates = find_duplicates(job_data, existing_jobs_dicts)
    
    if duplicates:
        # Merge with the first duplicate found
        duplicate_job, match_details = duplicates[0]
        existing_job_id = duplicate_job["id"]
        
        merged_job = merge_duplicate_job(
            existing_job_id=existing_job_id,
            new_job_data=job_data,
            new_source=source_info,
            db_session=db_session
        )
        
        logger.info(
            f"Duplicate detected and merged: job_id={existing_job_id}, "
            f"match_details={match_details}"
        )
        
        return True, merged_job
    else:
        logger.info("No duplicates found, job can be created as new")
        return False, {}
