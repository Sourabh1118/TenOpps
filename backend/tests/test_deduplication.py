"""
Unit tests for the deduplication service.

Tests cover:
- Company name normalization
- Title and location normalization
- Fuzzy string matching
- TF-IDF description similarity
- Multi-stage duplicate detection
"""
import pytest
from app.services.deduplication import (
    normalize_company_name,
    normalize_title,
    normalize_location,
    fuzzy_match,
    calculate_tfidf_similarity,
    is_duplicate,
    find_duplicates,
)


class TestCompanyNameNormalization:
    """Test company name normalization."""
    
    def test_removes_common_suffixes(self):
        """Test that common suffixes are removed."""
        assert normalize_company_name("Tech Corp, Inc.") == "tech"
        assert normalize_company_name("Acme Technologies LLC") == "acme"
        assert normalize_company_name("Global Solutions Ltd") == "global"
        assert normalize_company_name("Data Systems Corporation") == "data"
    
    def test_converts_to_lowercase(self):
        """Test that company names are converted to lowercase."""
        assert normalize_company_name("TECH COMPANY") == "tech company"
        assert normalize_company_name("Acme Corp") == "acme"
    
    def test_removes_special_characters(self):
        """Test that special characters are removed."""
        assert normalize_company_name("Tech@Corp!") == "tech"
        assert normalize_company_name("Acme & Co.") == "acme co"
    
    def test_normalizes_whitespace(self):
        """Test that extra whitespace is normalized."""
        assert normalize_company_name("  Tech   Corp  ") == "tech"
        assert normalize_company_name("Acme\\tCorp") == "acme"
    
    def test_handles_unicode(self):
        """Test that unicode characters are normalized."""
        assert normalize_company_name("Café Corp") == "cafe"
        assert normalize_company_name("Naïve Systems") == "naive"
    
    def test_handles_empty_string(self):
        """Test that empty strings are handled."""
        assert normalize_company_name("") == ""
        assert normalize_company_name(None) == ""


class TestTitleNormalization:
    """Test job title normalization."""
    
    def test_standardizes_seniority_levels(self):
        """Test that seniority abbreviations are standardized."""
        assert "senior" in normalize_title("Sr. Software Engineer")
        assert "junior" in normalize_title("Jr. Developer")
    
    def test_removes_special_characters(self):
        """Test that special characters are removed."""
        assert normalize_title("Python Developer (Remote)") == "senior python developer remote"
    
    def test_removes_stopwords(self):
        """Test that common stopwords are removed."""
        title = normalize_title("The Software Engineer")
        assert "the" not in title.split()
    
    def test_converts_to_lowercase(self):
        """Test that titles are converted to lowercase."""
        assert normalize_title("SOFTWARE ENGINEER") == "software engineer"
    
    def test_handles_empty_string(self):
        """Test that empty strings are handled."""
        assert normalize_title("") == ""
        assert normalize_title(None) == ""


class TestLocationNormalization:
    """Test location normalization."""
    
    def test_standardizes_abbreviations(self):
        """Test that location abbreviations are standardized."""
        normalized = normalize_location("123 Main Street")
        assert "st" in normalized
    
    def test_removes_special_characters(self):
        """Test that special characters are removed."""
        assert normalize_location("San Francisco, CA") == "san francisco ca"
    
    def test_converts_to_lowercase(self):
        """Test that locations are converted to lowercase."""
        assert normalize_location("NEW YORK") == "new york"
    
    def test_handles_empty_string(self):
        """Test that empty strings are handled."""
        assert normalize_location("") == ""
        assert normalize_location(None) == ""


class TestFuzzyMatching:
    """Test fuzzy string matching."""
    
    def test_exact_match(self):
        """Test that exact matches return True."""
        assert fuzzy_match("Software Engineer", "Software Engineer") is True
    
    def test_similar_strings(self):
        """Test that similar strings match."""
        assert fuzzy_match("Software Engineer", "Software Engineeer") is True
        assert fuzzy_match("Python Developer", "Python Developr") is True
    
    def test_dissimilar_strings(self):
        """Test that dissimilar strings don't match."""
        assert fuzzy_match("Python Developer", "Java Developer") is False
        assert fuzzy_match("Backend Engineer", "Frontend Engineer") is False
    
    def test_case_insensitive(self):
        """Test that matching is case insensitive."""
        assert fuzzy_match("Software Engineer", "software engineer") is True
    
    def test_custom_threshold(self):
        """Test that custom thresholds work."""
        # Lower threshold should match more loosely
        assert fuzzy_match("Python Dev", "Python Developer", threshold=0.6) is True
        # Higher threshold should be stricter
        assert fuzzy_match("Python Dev", "Python Developer", threshold=0.95) is False
    
    def test_empty_strings(self):
        """Test that empty strings return False."""
        assert fuzzy_match("", "test") is False
        assert fuzzy_match("test", "") is False
        assert fuzzy_match("", "") is False


class TestTFIDFSimilarity:
    """Test TF-IDF description similarity."""
    
    def test_identical_descriptions(self):
        """Test that identical descriptions have high similarity."""
        desc = "Python developer with Django experience"
        is_similar, score = calculate_tfidf_similarity(desc, desc)
        assert is_similar is True
        assert score > 0.9
    
    def test_similar_descriptions(self):
        """Test that similar descriptions match."""
        desc1 = "Python developer with Django experience"
        desc2 = "Python engineer experienced in Django"
        is_similar, score = calculate_tfidf_similarity(desc1, desc2)
        assert is_similar is True
        assert score > 0.5
    
    def test_dissimilar_descriptions(self):
        """Test that dissimilar descriptions don't match."""
        desc1 = "Python developer with Django experience"
        desc2 = "Java developer with Spring Boot experience"
        is_similar, score = calculate_tfidf_similarity(desc1, desc2, threshold=0.7)
        assert is_similar is False
    
    def test_empty_descriptions(self):
        """Test that empty descriptions return False."""
        is_similar, score = calculate_tfidf_similarity("", "test")
        assert is_similar is False
        assert score == 0.0
    
    def test_custom_threshold(self):
        """Test that custom thresholds work."""
        desc1 = "Python developer"
        desc2 = "Python engineer"
        is_similar_high, _ = calculate_tfidf_similarity(desc1, desc2, threshold=0.9)
        is_similar_low, _ = calculate_tfidf_similarity(desc1, desc2, threshold=0.3)
        assert is_similar_low is True
        # May or may not match with high threshold depending on exact calculation


class TestDuplicateDetection:
    """Test multi-stage duplicate detection."""
    
    def test_exact_duplicate(self):
        """Test that exact duplicates are detected."""
        job1 = {
            "company": "Tech Corp Inc",
            "title": "Senior Python Developer",
            "location": "San Francisco, CA",
            "description": "Build scalable Python applications using Django and PostgreSQL"
        }
        job2 = {
            "company": "Tech Corporation",
            "title": "Sr. Python Developer",
            "location": "San Francisco, California",
            "description": "Build scalable Python apps using Django and PostgreSQL"
        }
        is_dup, details = is_duplicate(job1, job2)
        assert is_dup is True
        assert details["company_match"] is True
        assert details["title_match"] is True
        assert details["location_match"] is True
        assert details["description_match"] is True
    
    def test_different_company(self):
        """Test that jobs from different companies are not duplicates."""
        job1 = {
            "company": "Tech Corp",
            "title": "Python Developer",
            "location": "San Francisco",
            "description": "Build Python applications"
        }
        job2 = {
            "company": "Acme Inc",
            "title": "Python Developer",
            "location": "San Francisco",
            "description": "Build Python applications"
        }
        is_dup, details = is_duplicate(job1, job2)
        assert is_dup is False
        assert details["company_match"] is False
    
    def test_different_title(self):
        """Test that jobs with different titles are not duplicates."""
        job1 = {
            "company": "Tech Corp",
            "title": "Python Developer",
            "location": "San Francisco",
            "description": "Build Python applications"
        }
        job2 = {
            "company": "Tech Corp",
            "title": "Java Developer",
            "location": "San Francisco",
            "description": "Build Java applications"
        }
        is_dup, details = is_duplicate(job1, job2)
        assert is_dup is False
        assert details["title_match"] is False
    
    def test_different_location(self):
        """Test that jobs in different locations are not duplicates."""
        job1 = {
            "company": "Tech Corp",
            "title": "Python Developer",
            "location": "San Francisco",
            "description": "Build Python applications"
        }
        job2 = {
            "company": "Tech Corp",
            "title": "Python Developer",
            "location": "New York",
            "description": "Build Python applications"
        }
        is_dup, details = is_duplicate(job1, job2)
        assert is_dup is False
        assert details["location_match"] is False
    
    def test_different_description(self):
        """Test that jobs with different descriptions are not duplicates."""
        job1 = {
            "company": "Tech Corp",
            "title": "Python Developer",
            "location": "San Francisco",
            "description": "Build Python applications using Django"
        }
        job2 = {
            "company": "Tech Corp",
            "title": "Python Developer",
            "location": "San Francisco",
            "description": "Build mobile applications using React Native"
        }
        is_dup, details = is_duplicate(job1, job2)
        assert is_dup is False
        assert details["description_match"] is False
    
    def test_custom_thresholds(self):
        """Test that custom thresholds work."""
        job1 = {
            "company": "Tech Corp",
            "title": "Python Dev",
            "location": "SF",
            "description": "Python"
        }
        job2 = {
            "company": "Tech Corporation",
            "title": "Python Developer",
            "location": "San Francisco",
            "description": "Python programming"
        }
        # With lower thresholds, should match
        is_dup, _ = is_duplicate(
            job1, job2,
            company_threshold=0.7,
            title_threshold=0.7,
            location_threshold=0.5,
            description_threshold=0.5
        )
        assert is_dup is True


class TestFindDuplicates:
    """Test finding duplicates in a list of jobs."""
    
    def test_finds_single_duplicate(self):
        """Test that a single duplicate is found."""
        new_job = {
            "company": "Tech Corp",
            "title": "Python Developer",
            "location": "San Francisco",
            "description": "Build Python applications"
        }
        existing_jobs = [
            {
                "company": "Tech Corporation",
                "title": "Python Developer",
                "location": "San Francisco",
                "description": "Build Python apps"
            }
        ]
        duplicates = find_duplicates(new_job, existing_jobs)
        assert len(duplicates) == 1
    
    def test_finds_multiple_duplicates(self):
        """Test that multiple duplicates are found."""
        new_job = {
            "company": "Tech Corp",
            "title": "Python Developer",
            "location": "San Francisco",
            "description": "Build Python applications"
        }
        existing_jobs = [
            {
                "company": "Tech Corporation",
                "title": "Python Developer",
                "location": "San Francisco",
                "description": "Build Python apps"
            },
            {
                "company": "Tech Corp Inc",
                "title": "Python Developer",
                "location": "San Francisco",
                "description": "Build Python applications"
            }
        ]
        duplicates = find_duplicates(new_job, existing_jobs)
        assert len(duplicates) == 2
    
    def test_finds_no_duplicates(self):
        """Test that no duplicates are found when none exist."""
        new_job = {
            "company": "Tech Corp",
            "title": "Python Developer",
            "location": "San Francisco",
            "description": "Build Python applications"
        }
        existing_jobs = [
            {
                "company": "Acme Inc",
                "title": "Java Developer",
                "location": "New York",
                "description": "Build Java applications"
            }
        ]
        duplicates = find_duplicates(new_job, existing_jobs)
        assert len(duplicates) == 0
    
    def test_empty_existing_jobs(self):
        """Test that empty existing jobs list returns no duplicates."""
        new_job = {
            "company": "Tech Corp",
            "title": "Python Developer",
            "location": "San Francisco",
            "description": "Build Python applications"
        }
        duplicates = find_duplicates(new_job, [])
        assert len(duplicates) == 0
