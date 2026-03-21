# Task 17.2: Full-Text Search Implementation

**Status:** ✅ COMPLETED

**Validates:** Requirements 6.1

## Overview

Task 17.2 implements PostgreSQL full-text search functionality using tsvector and tsquery for efficient searching on job titles and descriptions. This enables job seekers to perform natural language searches across job postings.

## Implementation Details

### 1. Search Schema (`app/schemas/search.py`)

Added `query` parameter to `SearchFilters`:

```python
query: Optional[str] = Field(
    default=None,
    description="Full-text search query for job title and description",
    max_length=200
)
```

### 2. Search Service (`app/services/search.py`)

Implemented full-text search in `SearchService.search_jobs()`:

```python
if filters.query:
    # Create tsquery from search query
    search_query = func.plainto_tsquery('english', filters.query)
    
    # Search in both title and description using tsvector
    title_match = func.to_tsvector('english', Job.title).op('@@')(search_query)
    description_match = func.to_tsvector('english', Job.description).op('@@')(search_query)
    
    # Match if query appears in either title or description
    query = query.where(or_(title_match, description_match))
```

**Key Features:**
- Uses `plainto_tsquery('english', ...)` for simple query parsing (handles spaces, special characters)
- Searches both title and description fields
- Uses OR logic - matches if query appears in either field
- Leverages GIN indexes for efficient search

### 3. Database Indexes (`app/models/job.py`)

GIN indexes defined in Job model for efficient full-text search:

```python
Index(
    "idx_jobs_title_fts",
    func.to_tsvector("english", "title"),
    postgresql_using="gin"
),
Index(
    "idx_jobs_description_fts",
    func.to_tsvector("english", "description"),
    postgresql_using="gin"
)
```

### 4. Database Migration (`alembic/versions/001_create_jobs_table.py`)

Migration creates GIN indexes:

```python
op.execute(
    """
    CREATE INDEX idx_jobs_title_fts ON jobs 
    USING gin(to_tsvector('english', title))
    """
)
op.execute(
    """
    CREATE INDEX idx_jobs_description_fts ON jobs 
    USING gin(to_tsvector('english', description))
    """
)
```

### 5. Tests (`tests/test_search.py`)

Comprehensive test coverage:

- `test_full_text_search_on_title` - Verifies search matches job titles
- `test_full_text_search_on_description` - Verifies search matches descriptions
- `test_full_text_search_title_or_description` - Verifies OR logic between fields

## Technical Decisions

### Why `plainto_tsquery` instead of `to_tsquery`?

- `plainto_tsquery` is more user-friendly - it automatically handles:
  - Spaces between words
  - Special characters
  - No need for users to understand query syntax
- Suitable for simple search queries from job seekers

### Why search both title and description?

- Requirement 6.1 specifies: "perform full-text search on job titles and descriptions"
- Increases search recall - users can find jobs by keywords in either field
- Uses OR logic to match either field

### Why GIN indexes?

- GIN (Generalized Inverted Index) is optimized for full-text search
- Provides fast lookups for tsvector operations
- Essential for performance with large job datasets

## Search Behavior

### Example Queries

1. **Simple keyword search:**
   - Query: `"python"`
   - Matches: Jobs with "Python" in title or description

2. **Multi-word search:**
   - Query: `"machine learning"`
   - Matches: Jobs containing both "machine" and "learning"

3. **Combined with filters:**
   - Query: `"software engineer"` + location: `"San Francisco"` + remote: `true`
   - Matches: Remote software engineer jobs in San Francisco

### Search Features

- **Case-insensitive:** Searches ignore case
- **Stemming:** English language stemming (e.g., "engineer" matches "engineering")
- **Stop words:** Common words like "the", "a" are ignored
- **Ranking:** Results sorted by quality_score DESC, posted_at DESC

## Integration with Existing System

The full-text search integrates seamlessly with:

1. **Other filters:** Combined with AND logic
2. **Pagination:** Works with page/page_size parameters
3. **Sorting:** Results sorted by quality score and date
4. **Status filtering:** Only searches active jobs

## Performance Considerations

- **GIN indexes:** Enable fast full-text search even with millions of jobs
- **Index size:** GIN indexes are larger than B-tree but essential for FTS
- **Query optimization:** PostgreSQL automatically uses indexes when available

## Testing

Run tests with PostgreSQL database:

```bash
export TEST_DATABASE_URL="postgresql://user:pass@localhost/test_db"
pytest tests/test_search.py -v
```

## Verification

Run verification script:

```bash
python test_fulltext_search_verification.py
```

## Requirements Validation

✅ **Requirement 6.1:** "WHEN a job seeker submits a search query, THE Search_Engine SHALL perform full-text search on job titles and descriptions"

- Search query parameter added to SearchFilters
- Full-text search implemented using tsvector and tsquery
- Searches both title and description fields
- GIN indexes created for efficient search
- Comprehensive tests validate functionality

## Files Modified

1. `app/schemas/search.py` - Added query parameter
2. `app/services/search.py` - Implemented full-text search logic
3. `app/models/job.py` - Added GIN indexes
4. `alembic/versions/001_create_jobs_table.py` - Migration for indexes
5. `tests/test_search.py` - Added full-text search tests

## Next Steps

Task 17.2 is complete. The search service now supports:
- ✅ Full-text search on title and description
- ✅ All filter types (location, job type, experience, salary, etc.)
- ✅ Pagination
- ✅ Sorting by quality and date

Ready for integration with the search API endpoint.
