# SearchFilters Model Guide

## Overview

The `SearchFilters` Pydantic model provides comprehensive validation for job search query parameters. It supports multiple optional filters that can be combined to create precise job searches.

## Model Location

```python
from app.schemas.search import SearchFilters
```

## Supported Filters

### 1. Text Search

**query** (Optional[str])
- Full-text search on job title and description
- Max length: 200 characters
- Example: `"software engineer"`

**location** (Optional[str])
- Exact location match
- Max length: 200 characters
- Example: `"San Francisco"`

### 2. Categorical Filters

**jobType** (Optional[List[JobType]])
- Filter by employment types
- Valid values: `FULL_TIME`, `PART_TIME`, `CONTRACT`, `FREELANCE`, `INTERNSHIP`, `FELLOWSHIP`, `ACADEMIC`
- Cannot be empty list
- Example: `[JobType.FULL_TIME, JobType.CONTRACT]`

**experienceLevel** (Optional[List[ExperienceLevel]])
- Filter by required experience
- Valid values: `ENTRY`, `MID`, `SENIOR`, `LEAD`, `EXECUTIVE`
- Cannot be empty list
- Example: `[ExperienceLevel.MID, ExperienceLevel.SENIOR]`

**sourceType** (Optional[List[SourceType]])
- Filter by job source
- Valid values: `DIRECT`, `URL_IMPORT`, `AGGREGATED`
- Cannot be empty list
- Example: `[SourceType.DIRECT]`

### 3. Numeric Filters

**salaryMin** (Optional[int])
- Minimum salary threshold
- Must be >= 0
- Example: `50000`

**salaryMax** (Optional[int])
- Maximum salary threshold
- Must be >= 0
- Must be >= salaryMin if both provided
- Example: `150000`

**postedWithin** (Optional[int])
- Jobs posted within N days
- Range: 1-365 days
- Example: `7` (last 7 days)

### 4. Boolean Filters

**remote** (Optional[bool])
- Filter for remote jobs
- `True`: only remote jobs
- `False` or `None`: all jobs
- Example: `True`

## Validation Rules

### Salary Range Validation
- If both `salaryMin` and `salaryMax` are provided, `salaryMax` must be >= `salaryMin`
- Both values must be non-negative

### List Validation
- Filter lists (`jobType`, `experienceLevel`, `sourceType`) cannot be empty
- If provided, must contain at least one valid enum value

### String Length Validation
- `query`: max 200 characters
- `location`: max 200 characters

### Range Validation
- `postedWithin`: 1-365 days
- `salaryMin`, `salaryMax`: >= 0

## Usage Examples

### Example 1: Simple Text Search
```python
from app.schemas.search import SearchFilters

filters = SearchFilters(query="python developer")
```

### Example 2: Location and Job Type
```python
from app.schemas.search import SearchFilters
from app.models.job import JobType

filters = SearchFilters(
    location="New York",
    jobType=[JobType.FULL_TIME, JobType.CONTRACT]
)
```

### Example 3: Salary Range Filter
```python
from app.schemas.search import SearchFilters

filters = SearchFilters(
    salaryMin=80000,
    salaryMax=120000
)
```

### Example 4: Recent Remote Jobs
```python
from app.schemas.search import SearchFilters

filters = SearchFilters(
    remote=True,
    postedWithin=7  # Last 7 days
)
```

### Example 5: Comprehensive Filter
```python
from app.schemas.search import SearchFilters
from app.models.job import JobType, ExperienceLevel, SourceType

filters = SearchFilters(
    query="software engineer",
    location="San Francisco",
    jobType=[JobType.FULL_TIME],
    experienceLevel=[ExperienceLevel.MID, ExperienceLevel.SENIOR],
    salaryMin=100000,
    salaryMax=200000,
    remote=True,
    postedWithin=30,
    sourceType=[SourceType.DIRECT, SourceType.URL_IMPORT]
)
```

### Example 6: Empty Filters (All Jobs)
```python
from app.schemas.search import SearchFilters

filters = SearchFilters()  # All filters are None
```

## API Integration

### FastAPI Endpoint Example
```python
from fastapi import APIRouter, Query
from typing import Optional, List
from app.schemas.search import SearchFilters
from app.models.job import JobType, ExperienceLevel, SourceType

router = APIRouter()

@router.get("/jobs/search")
async def search_jobs(
    query: Optional[str] = None,
    location: Optional[str] = None,
    jobType: Optional[List[JobType]] = Query(None),
    experienceLevel: Optional[List[ExperienceLevel]] = Query(None),
    salaryMin: Optional[int] = None,
    salaryMax: Optional[int] = None,
    remote: Optional[bool] = None,
    postedWithin: Optional[int] = None,
    sourceType: Optional[List[SourceType]] = Query(None),
):
    # Create filters from query parameters
    filters = SearchFilters(
        query=query,
        location=location,
        jobType=jobType,
        experienceLevel=experienceLevel,
        salaryMin=salaryMin,
        salaryMax=salaryMax,
        remote=remote,
        postedWithin=postedWithin,
        sourceType=sourceType
    )
    
    # Use filters in search service
    results = await search_service.search(filters)
    return results
```

## Error Handling

### Validation Errors
```python
from pydantic import ValidationError
from app.schemas.search import SearchFilters

try:
    filters = SearchFilters(salaryMin=150000, salaryMax=50000)
except ValidationError as e:
    print(e.errors())
    # [{'loc': ('salaryMax',), 'msg': 'salaryMax must be greater than or equal to salaryMin', ...}]
```

### Common Validation Errors

1. **Invalid salary range**
   - Error: `salaryMax must be greater than or equal to salaryMin`
   - Fix: Ensure `salaryMax >= salaryMin`

2. **Empty filter list**
   - Error: `Filter list cannot be empty`
   - Fix: Provide at least one value or set to `None`

3. **Invalid enum value**
   - Error: `Input should be 'full_time', 'part_time', ...`
   - Fix: Use valid enum values from JobType, ExperienceLevel, or SourceType

4. **String too long**
   - Error: `String should have at most 200 characters`
   - Fix: Limit query/location to 200 characters

5. **Invalid range**
   - Error: `Input should be greater than or equal to 1`
   - Fix: Ensure `postedWithin` is between 1-365

## Testing

Run the test suite:
```bash
pytest backend/tests/test_search_filters.py -v
```

Test coverage includes:
- All filter validations
- Enum handling
- Range constraints
- Edge cases (empty strings, unicode, large numbers)
- Combined filters

## Requirements Mapping

This model satisfies the following requirements:
- **6.1**: Full-text search on title and description (query filter)
- **6.2**: Location filtering (location filter)
- **6.3**: Job type filtering (jobType filter)
- **6.4**: Experience level filtering (experienceLevel filter)
- **6.5**: Minimum salary filtering (salaryMin filter)
- **6.6**: Maximum salary filtering (salaryMax filter)
- **6.7**: Remote job filtering (remote filter)
- **6.8**: Posted within filtering (postedWithin filter)
- **6.9**: Source type filtering (sourceType filter)

## Next Steps

After implementing SearchFilters, the next tasks are:
1. **Task 17.2**: Implement full-text search using PostgreSQL tsvector
2. **Task 17.3**: Implement filter application logic in search service
3. **Task 17.4**: Implement search result ranking and sorting
4. **Task 17.5**: Implement pagination
5. **Task 17.6**: Implement search result caching
6. **Task 17.7**: Create search endpoint
