"""
Unit tests for SearchFilters Pydantic model.

Tests validation rules, enum handling, and range constraints.
"""
import pytest
from pydantic import ValidationError
from app.schemas.search import SearchFilters
from app.models.job import JobType, ExperienceLevel, SourceType


class TestSearchFiltersValidation:
    """Test SearchFilters validation rules."""

    def test_all_filters_optional(self):
        """Test that all filters are optional and model can be created empty."""
        filters = SearchFilters()
        assert filters.query is None
        assert filters.location is None
        assert filters.jobType is None
        assert filters.experienceLevel is None
        assert filters.salaryMin is None
        assert filters.salaryMax is None
        assert filters.remote is None
        assert filters.postedWithin is None
        assert filters.sourceType is None

    def test_query_filter_valid(self):
        """Test query filter accepts valid strings."""
        filters = SearchFilters(query="software engineer")
        assert filters.query == "software engineer"

    def test_query_filter_max_length(self):
        """Test query filter enforces max length of 200 characters."""
        long_query = "a" * 201
        with pytest.raises(ValidationError) as exc_info:
            SearchFilters(query=long_query)
        assert "String should have at most 200 characters" in str(exc_info.value)

    def test_location_filter_valid(self):
        """Test location filter accepts valid strings."""
        filters = SearchFilters(location="San Francisco")
        assert filters.location == "San Francisco"

    def test_location_filter_max_length(self):
        """Test location filter enforces max length of 200 characters."""
        long_location = "a" * 201
        with pytest.raises(ValidationError) as exc_info:
            SearchFilters(location=long_location)
        assert "String should have at most 200 characters" in str(exc_info.value)

    def test_job_type_filter_valid_single(self):
        """Test jobType filter accepts single valid enum value."""
        filters = SearchFilters(jobType=[JobType.FULL_TIME])
        assert filters.jobType == [JobType.FULL_TIME]

    def test_job_type_filter_valid_multiple(self):
        """Test jobType filter accepts multiple valid enum values."""
        filters = SearchFilters(jobType=[JobType.FULL_TIME, JobType.CONTRACT])
        assert filters.jobType == [JobType.FULL_TIME, JobType.CONTRACT]

    def test_job_type_filter_invalid_enum(self):
        """Test jobType filter rejects invalid enum values."""
        with pytest.raises(ValidationError) as exc_info:
            SearchFilters(jobType=["INVALID_TYPE"])
        assert "Input should be" in str(exc_info.value)

    def test_job_type_filter_empty_list(self):
        """Test jobType filter rejects empty lists."""
        with pytest.raises(ValidationError) as exc_info:
            SearchFilters(jobType=[])
        assert "Filter list cannot be empty" in str(exc_info.value)

    def test_experience_level_filter_valid(self):
        """Test experienceLevel filter accepts valid enum values."""
        filters = SearchFilters(experienceLevel=[ExperienceLevel.MID, ExperienceLevel.SENIOR])
        assert filters.experienceLevel == [ExperienceLevel.MID, ExperienceLevel.SENIOR]

    def test_experience_level_filter_invalid_enum(self):
        """Test experienceLevel filter rejects invalid enum values."""
        with pytest.raises(ValidationError) as exc_info:
            SearchFilters(experienceLevel=["INVALID_LEVEL"])
        assert "Input should be" in str(exc_info.value)

    def test_experience_level_filter_empty_list(self):
        """Test experienceLevel filter rejects empty lists."""
        with pytest.raises(ValidationError) as exc_info:
            SearchFilters(experienceLevel=[])
        assert "Filter list cannot be empty" in str(exc_info.value)

    def test_salary_min_valid(self):
        """Test salaryMin accepts valid positive integers."""
        filters = SearchFilters(salaryMin=50000)
        assert filters.salaryMin == 50000

    def test_salary_min_zero(self):
        """Test salaryMin accepts zero."""
        filters = SearchFilters(salaryMin=0)
        assert filters.salaryMin == 0

    def test_salary_min_negative(self):
        """Test salaryMin rejects negative values."""
        with pytest.raises(ValidationError) as exc_info:
            SearchFilters(salaryMin=-1000)
        assert "Input should be greater than or equal to 0" in str(exc_info.value)

    def test_salary_max_valid(self):
        """Test salaryMax accepts valid positive integers."""
        filters = SearchFilters(salaryMax=150000)
        assert filters.salaryMax == 150000

    def test_salary_max_zero(self):
        """Test salaryMax accepts zero."""
        filters = SearchFilters(salaryMax=0)
        assert filters.salaryMax == 0

    def test_salary_max_negative(self):
        """Test salaryMax rejects negative values."""
        with pytest.raises(ValidationError) as exc_info:
            SearchFilters(salaryMax=-1000)
        assert "Input should be greater than or equal to 0" in str(exc_info.value)

    def test_salary_range_valid(self):
        """Test valid salary range where max >= min."""
        filters = SearchFilters(salaryMin=50000, salaryMax=150000)
        assert filters.salaryMin == 50000
        assert filters.salaryMax == 150000

    def test_salary_range_equal(self):
        """Test salary range where max equals min."""
        filters = SearchFilters(salaryMin=100000, salaryMax=100000)
        assert filters.salaryMin == 100000
        assert filters.salaryMax == 100000

    def test_salary_range_invalid(self):
        """Test salary range rejects max < min."""
        with pytest.raises(ValidationError) as exc_info:
            SearchFilters(salaryMin=150000, salaryMax=50000)
        assert "salaryMax must be greater than or equal to salaryMin" in str(exc_info.value)

    def test_remote_filter_true(self):
        """Test remote filter accepts true."""
        filters = SearchFilters(remote=True)
        assert filters.remote is True

    def test_remote_filter_false(self):
        """Test remote filter accepts false."""
        filters = SearchFilters(remote=False)
        assert filters.remote is False

    def test_posted_within_valid(self):
        """Test postedWithin accepts valid day counts."""
        filters = SearchFilters(postedWithin=7)
        assert filters.postedWithin == 7

    def test_posted_within_min_boundary(self):
        """Test postedWithin accepts minimum value of 1."""
        filters = SearchFilters(postedWithin=1)
        assert filters.postedWithin == 1

    def test_posted_within_max_boundary(self):
        """Test postedWithin accepts maximum value of 365."""
        filters = SearchFilters(postedWithin=365)
        assert filters.postedWithin == 365

    def test_posted_within_below_min(self):
        """Test postedWithin rejects values below 1."""
        with pytest.raises(ValidationError) as exc_info:
            SearchFilters(postedWithin=0)
        assert "Input should be greater than or equal to 1" in str(exc_info.value)

    def test_posted_within_above_max(self):
        """Test postedWithin rejects values above 365."""
        with pytest.raises(ValidationError) as exc_info:
            SearchFilters(postedWithin=366)
        assert "Input should be less than or equal to 365" in str(exc_info.value)

    def test_source_type_filter_valid(self):
        """Test sourceType filter accepts valid enum values."""
        filters = SearchFilters(sourceType=[SourceType.DIRECT, SourceType.AGGREGATED])
        assert filters.sourceType == [SourceType.DIRECT, SourceType.AGGREGATED]

    def test_source_type_filter_invalid_enum(self):
        """Test sourceType filter rejects invalid enum values."""
        with pytest.raises(ValidationError) as exc_info:
            SearchFilters(sourceType=["INVALID_SOURCE"])
        assert "Input should be" in str(exc_info.value)

    def test_source_type_filter_empty_list(self):
        """Test sourceType filter rejects empty lists."""
        with pytest.raises(ValidationError) as exc_info:
            SearchFilters(sourceType=[])
        assert "Filter list cannot be empty" in str(exc_info.value)

    def test_multiple_filters_combined(self):
        """Test multiple filters can be combined."""
        filters = SearchFilters(
            query="python developer",
            location="New York",
            jobType=[JobType.FULL_TIME, JobType.CONTRACT],
            experienceLevel=[ExperienceLevel.MID],
            salaryMin=80000,
            salaryMax=120000,
            remote=True,
            postedWithin=30,
            sourceType=[SourceType.DIRECT]
        )
        assert filters.query == "python developer"
        assert filters.location == "New York"
        assert filters.jobType == [JobType.FULL_TIME, JobType.CONTRACT]
        assert filters.experienceLevel == [ExperienceLevel.MID]
        assert filters.salaryMin == 80000
        assert filters.salaryMax == 120000
        assert filters.remote is True
        assert filters.postedWithin == 30
        assert filters.sourceType == [SourceType.DIRECT]


class TestSearchFiltersEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_whitespace_query(self):
        """Test query with only whitespace."""
        filters = SearchFilters(query="   ")
        assert filters.query == "   "

    def test_special_characters_query(self):
        """Test query with special characters."""
        filters = SearchFilters(query="C++ developer @company #remote")
        assert filters.query == "C++ developer @company #remote"

    def test_unicode_query(self):
        """Test query with unicode characters."""
        filters = SearchFilters(query="développeur Python 日本語")
        assert filters.query == "développeur Python 日本語"

    def test_all_job_types(self):
        """Test filter with all job types."""
        all_types = [
            JobType.FULL_TIME,
            JobType.PART_TIME,
            JobType.CONTRACT,
            JobType.FREELANCE,
            JobType.INTERNSHIP,
            JobType.FELLOWSHIP,
            JobType.ACADEMIC
        ]
        filters = SearchFilters(jobType=all_types)
        assert filters.jobType == all_types

    def test_all_experience_levels(self):
        """Test filter with all experience levels."""
        all_levels = [
            ExperienceLevel.ENTRY,
            ExperienceLevel.MID,
            ExperienceLevel.SENIOR,
            ExperienceLevel.LEAD,
            ExperienceLevel.EXECUTIVE
        ]
        filters = SearchFilters(experienceLevel=all_levels)
        assert filters.experienceLevel == all_levels

    def test_all_source_types(self):
        """Test filter with all source types."""
        all_sources = [
            SourceType.DIRECT,
            SourceType.URL_IMPORT,
            SourceType.AGGREGATED
        ]
        filters = SearchFilters(sourceType=all_sources)
        assert filters.sourceType == all_sources

    def test_large_salary_values(self):
        """Test filter with large salary values."""
        filters = SearchFilters(salaryMin=1000000, salaryMax=5000000)
        assert filters.salaryMin == 1000000
        assert filters.salaryMax == 5000000
