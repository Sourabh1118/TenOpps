"""
Unit tests for quality scoring service.

Tests cover:
- Base score calculation for each source type
- Completeness scoring with various field combinations
- Freshness scoring for different time periods
- Combined quality score calculation
- Score clamping
- Edge cases and error handling
"""
import pytest
from datetime import datetime, timedelta

from app.models.job import SourceType
from app.services.quality_scoring import (
    clamp_score,
    calculate_base_score,
    calculate_completeness_score,
    calculate_freshness_score,
    calculate_quality_score,
)


class TestClampScore:
    """Test score clamping utility function."""
    
    def test_clamp_score_within_bounds(self):
        """Test that scores within bounds are unchanged."""
        assert clamp_score(50.0) == 50.0
        assert clamp_score(0.0) == 0.0
        assert clamp_score(100.0) == 100.0
        assert clamp_score(75.5) == 75.5
    
    def test_clamp_score_above_max(self):
        """Test that scores above max are clamped to max."""
        assert clamp_score(150.0) == 100.0
        assert clamp_score(101.0) == 100.0
        assert clamp_score(999.9) == 100.0
    
    def test_clamp_score_below_min(self):
        """Test that scores below min are clamped to min."""
        assert clamp_score(-10.0) == 0.0
        assert clamp_score(-0.1) == 0.0
        assert clamp_score(-999.9) == 0.0
    
    def test_clamp_score_custom_bounds(self):
        """Test clamping with custom min/max values."""
        assert clamp_score(50.0, min_val=10.0, max_val=90.0) == 50.0
        assert clamp_score(5.0, min_val=10.0, max_val=90.0) == 10.0
        assert clamp_score(95.0, min_val=10.0, max_val=90.0) == 90.0


class TestCalculateBaseScore:
    """Test base score calculation for different source types."""
    
    def test_direct_post_base_score(self):
        """Test that direct posts get base score of 70."""
        score = calculate_base_score(SourceType.DIRECT)
        assert score == 70.0
    
    def test_url_import_base_score(self):
        """Test that URL imports get base score of 50."""
        score = calculate_base_score(SourceType.URL_IMPORT)
        assert score == 50.0
    
    def test_aggregated_base_score(self):
        """Test that aggregated jobs get base score of 30."""
        score = calculate_base_score(SourceType.AGGREGATED)
        assert score == 30.0
    
    def test_base_score_ordering(self):
        """Test that direct > url_import > aggregated."""
        direct = calculate_base_score(SourceType.DIRECT)
        url_import = calculate_base_score(SourceType.URL_IMPORT)
        aggregated = calculate_base_score(SourceType.AGGREGATED)
        
        assert direct > url_import
        assert url_import > aggregated
        assert direct >= 70.0
        assert aggregated <= 30.0


class TestCalculateCompletenessScore:
    """Test completeness scoring based on field presence."""
    
    def test_completeness_all_fields_present(self):
        """Test maximum completeness score with all fields."""
        job_data = {
            "requirements": ["Python", "Django"],
            "responsibilities": ["Build APIs", "Write tests"],
            "salary_min": 100000,
            "salary_max": 150000,
            "tags": ["python", "backend"],
        }
        score = calculate_completeness_score(job_data)
        assert score == 20.0
    
    def test_completeness_no_fields_present(self):
        """Test zero completeness score with no optional fields."""
        job_data = {}
        score = calculate_completeness_score(job_data)
        assert score == 0.0
    
    def test_completeness_only_requirements(self):
        """Test completeness with only requirements field."""
        job_data = {"requirements": ["Python"]}
        score = calculate_completeness_score(job_data)
        assert score == 4.0
    
    def test_completeness_only_responsibilities(self):
        """Test completeness with only responsibilities field."""
        job_data = {"responsibilities": ["Build APIs"]}
        score = calculate_completeness_score(job_data)
        assert score == 4.0
    
    def test_completeness_only_salary_min(self):
        """Test completeness with only salary_min field."""
        job_data = {"salary_min": 100000}
        score = calculate_completeness_score(job_data)
        assert score == 4.0
    
    def test_completeness_only_salary_max(self):
        """Test completeness with only salary_max field."""
        job_data = {"salary_max": 150000}
        score = calculate_completeness_score(job_data)
        assert score == 4.0
    
    def test_completeness_only_tags(self):
        """Test completeness with only tags field."""
        job_data = {"tags": ["python"]}
        score = calculate_completeness_score(job_data)
        assert score == 4.0
    
    def test_completeness_partial_fields(self):
        """Test completeness with some fields present."""
        job_data = {
            "requirements": ["Python"],
            "salary_min": 100000,
            "tags": ["python"],
        }
        score = calculate_completeness_score(job_data)
        assert score == 12.0  # 3 fields × 4 points
    
    def test_completeness_empty_lists_ignored(self):
        """Test that empty lists don't count toward completeness."""
        job_data = {
            "requirements": [],
            "responsibilities": [],
            "tags": [],
        }
        score = calculate_completeness_score(job_data)
        assert score == 0.0
    
    def test_completeness_zero_salary_ignored(self):
        """Test that zero salary values don't count."""
        job_data = {
            "salary_min": 0,
            "salary_max": 0,
        }
        score = calculate_completeness_score(job_data)
        assert score == 0.0
    
    def test_completeness_negative_salary_ignored(self):
        """Test that negative salary values don't count."""
        job_data = {
            "salary_min": -1000,
            "salary_max": -5000,
        }
        score = calculate_completeness_score(job_data)
        assert score == 0.0


class TestCalculateFreshnessScore:
    """Test freshness scoring based on job age."""
    
    def test_freshness_less_than_1_day(self):
        """Test freshness score for jobs less than 1 day old."""
        now = datetime.utcnow()
        posted_at = now - timedelta(hours=12)
        score = calculate_freshness_score(posted_at)
        assert score == 10.0
    
    def test_freshness_just_posted(self):
        """Test freshness score for jobs just posted."""
        posted_at = datetime.utcnow()
        score = calculate_freshness_score(posted_at)
        assert score == 10.0
    
    def test_freshness_1_to_7_days(self):
        """Test freshness score for jobs 1-7 days old."""
        now = datetime.utcnow()
        
        # Test 1 day old
        posted_at = now - timedelta(days=1)
        assert calculate_freshness_score(posted_at) == 8.0
        
        # Test 5 days old
        posted_at = now - timedelta(days=5)
        assert calculate_freshness_score(posted_at) == 8.0
        
        # Test 7 days old
        posted_at = now - timedelta(days=7)
        assert calculate_freshness_score(posted_at) == 8.0
    
    def test_freshness_8_to_14_days(self):
        """Test freshness score for jobs 8-14 days old."""
        now = datetime.utcnow()
        
        # Test 8 days old
        posted_at = now - timedelta(days=8)
        assert calculate_freshness_score(posted_at) == 6.0
        
        # Test 10 days old
        posted_at = now - timedelta(days=10)
        assert calculate_freshness_score(posted_at) == 6.0
        
        # Test 14 days old
        posted_at = now - timedelta(days=14)
        assert calculate_freshness_score(posted_at) == 6.0
    
    def test_freshness_15_to_30_days(self):
        """Test freshness score for jobs 15-30 days old."""
        now = datetime.utcnow()
        
        # Test 15 days old
        posted_at = now - timedelta(days=15)
        assert calculate_freshness_score(posted_at) == 4.0
        
        # Test 20 days old
        posted_at = now - timedelta(days=20)
        assert calculate_freshness_score(posted_at) == 4.0
        
        # Test 30 days old
        posted_at = now - timedelta(days=30)
        assert calculate_freshness_score(posted_at) == 4.0
    
    def test_freshness_more_than_30_days(self):
        """Test freshness score for jobs more than 30 days old."""
        now = datetime.utcnow()
        
        # Test 31 days old
        posted_at = now - timedelta(days=31)
        assert calculate_freshness_score(posted_at) == 2.0
        
        # Test 60 days old
        posted_at = now - timedelta(days=60)
        assert calculate_freshness_score(posted_at) == 2.0
        
        # Test 90 days old
        posted_at = now - timedelta(days=90)
        assert calculate_freshness_score(posted_at) == 2.0
    
    def test_freshness_score_ordering(self):
        """Test that newer jobs have higher freshness scores."""
        now = datetime.utcnow()
        
        score_new = calculate_freshness_score(now)
        score_week = calculate_freshness_score(now - timedelta(days=7))
        score_month = calculate_freshness_score(now - timedelta(days=30))
        score_old = calculate_freshness_score(now - timedelta(days=60))
        
        assert score_new > score_week
        assert score_week > score_month
        assert score_month > score_old


class TestCalculateQualityScore:
    """Test combined quality score calculation."""
    
    def test_quality_score_direct_complete_fresh(self):
        """Test maximum quality score for direct, complete, fresh job."""
        job_data = {
            "requirements": ["Python"],
            "responsibilities": ["Build APIs"],
            "salary_min": 100000,
            "salary_max": 150000,
            "tags": ["python"],
        }
        posted_at = datetime.utcnow()
        
        score = calculate_quality_score(SourceType.DIRECT, job_data, posted_at)
        
        # 70 (base) + 20 (completeness) + 10 (freshness) = 100
        assert score == 100.0
    
    def test_quality_score_aggregated_minimal_old(self):
        """Test minimum quality score for aggregated, minimal, old job."""
        job_data = {}  # No optional fields
        posted_at = datetime.utcnow() - timedelta(days=60)
        
        score = calculate_quality_score(SourceType.AGGREGATED, job_data, posted_at)
        
        # 30 (base) + 0 (completeness) + 2 (freshness) = 32
        assert score == 32.0
    
    def test_quality_score_url_import_partial(self):
        """Test quality score for URL import with partial completeness."""
        job_data = {
            "requirements": ["Python"],
            "salary_min": 100000,
        }
        posted_at = datetime.utcnow() - timedelta(days=10)
        
        score = calculate_quality_score(SourceType.URL_IMPORT, job_data, posted_at)
        
        # 50 (base) + 8 (completeness: 2 fields) + 6 (freshness: 10 days) = 64
        assert score == 64.0
    
    def test_quality_score_defaults_to_now(self):
        """Test that posted_at defaults to current time."""
        job_data = {
            "requirements": ["Python"],
        }
        
        score = calculate_quality_score(SourceType.DIRECT, job_data)
        
        # Should include maximum freshness score (10) since it defaults to now
        # 70 (base) + 4 (completeness: 1 field) + 10 (freshness) = 84
        assert score == 84.0
    
    def test_quality_score_clamped_to_100(self):
        """Test that quality score is clamped to maximum 100."""
        # This shouldn't happen in practice, but test the clamping
        job_data = {
            "requirements": ["Python"],
            "responsibilities": ["Build APIs"],
            "salary_min": 100000,
            "salary_max": 150000,
            "tags": ["python"],
        }
        posted_at = datetime.utcnow()
        
        score = calculate_quality_score(SourceType.DIRECT, job_data, posted_at)
        
        assert score <= 100.0
        assert score == 100.0
    
    def test_quality_score_clamped_to_0(self):
        """Test that quality score is clamped to minimum 0."""
        # This shouldn't happen in practice, but test the clamping
        job_data = {}
        posted_at = datetime.utcnow() - timedelta(days=90)
        
        score = calculate_quality_score(SourceType.AGGREGATED, job_data, posted_at)
        
        assert score >= 0.0
    
    def test_quality_score_direct_always_above_70(self):
        """Test that direct posts always score at least 70."""
        job_data = {}  # Minimal data
        posted_at = datetime.utcnow() - timedelta(days=90)  # Old
        
        score = calculate_quality_score(SourceType.DIRECT, job_data, posted_at)
        
        # 70 (base) + 0 (completeness) + 2 (freshness) = 72
        assert score >= 70.0
    
    def test_quality_score_aggregated_below_60(self):
        """Test that aggregated posts with no extras score below 60."""
        job_data = {}  # No optional fields
        posted_at = datetime.utcnow()
        
        score = calculate_quality_score(SourceType.AGGREGATED, job_data, posted_at)
        
        # 30 (base) + 0 (completeness) + 10 (freshness) = 40
        assert score <= 60.0
    
    def test_quality_score_components_sum_correctly(self):
        """Test that quality score is sum of components."""
        job_data = {
            "requirements": ["Python"],
            "responsibilities": ["Build APIs"],
        }
        posted_at = datetime.utcnow() - timedelta(days=5)
        
        base = calculate_base_score(SourceType.URL_IMPORT)
        completeness = calculate_completeness_score(job_data)
        freshness = calculate_freshness_score(posted_at)
        
        expected = base + completeness + freshness
        actual = calculate_quality_score(SourceType.URL_IMPORT, job_data, posted_at)
        
        assert actual == expected


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_quality_score_with_none_values(self):
        """Test quality score with None values in job_data."""
        job_data = {
            "requirements": None,
            "responsibilities": None,
            "salary_min": None,
            "salary_max": None,
            "tags": None,
        }
        
        score = calculate_quality_score(SourceType.DIRECT, job_data)
        
        # Should handle None values gracefully
        assert score >= 70.0  # At least base + freshness
    
    def test_quality_score_with_extra_fields(self):
        """Test that extra fields in job_data don't affect score."""
        job_data = {
            "requirements": ["Python"],
            "extra_field": "should be ignored",
            "another_field": 12345,
        }
        
        score = calculate_quality_score(SourceType.DIRECT, job_data)
        
        # Should only count requirements field
        # 70 (base) + 4 (completeness: 1 field) + 10 (freshness) = 84
        assert score == 84.0
    
    def test_freshness_score_with_future_date(self):
        """Test freshness score with future posted_at date."""
        future = datetime.utcnow() + timedelta(days=1)
        
        # Should treat as very fresh (negative age becomes 0 days)
        score = calculate_freshness_score(future)
        
        # Future dates have negative age, which becomes < 1 day
        assert score == 10.0
