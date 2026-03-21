# Search API Quick Reference

## Endpoint
```
GET /api/jobs/search
```

## Query Parameters

### Full-Text Search
- **query** (string, optional, max 200 chars)
  - Full-text search on job title and description
  - Example: `query=software+engineer`

### Location Filter
- **location** (string, optional, max 200 chars)
  - Exact match on job location
  - Example: `location=San+Francisco`

### Job Type Filter
- **jobType** (array of enum, optional)
  - Filter by job types (can specify multiple)
  - Values: `FULL_TIME`, `PART_TIME`, `CONTRACT`, `FREELANCE`, `INTERNSHIP`, `FELLOWSHIP`, `ACADEMIC`
  - Example: `jobType=FULL_TIME&jobType=CONTRACT`

### Experience Level Filter
- **experienceLevel** (array of enum, optional)
  - Filter by experience levels (can specify multiple)
  - Values: `ENTRY`, `MID`, `SENIOR`, `LEAD`, `EXECUTIVE`
  - Example: `experienceLevel=SENIOR&experienceLevel=LEAD`

### Salary Filters
- **salaryMin** (integer, optional, >= 0)
  - Minimum salary filter (jobs with salary >= this value)
  - Example: `salaryMin=100000`

- **salaryMax** (integer, optional, >= 0)
  - Maximum salary filter (jobs with salary <= this value)
  - Example: `salaryMax=200000`

### Remote Filter
- **remote** (boolean, optional)
  - Filter for remote jobs only
  - Example: `remote=true`

### Posted Within Filter
- **postedWithin** (integer, optional, 1-365)
  - Filter jobs posted within this many days
  - Example: `postedWithin=7` (last 7 days)

### Source Type Filter
- **sourceType** (array of enum, optional)
  - Filter by source types (can specify multiple)
  - Values: `DIRECT`, `URL_IMPORT`, `AGGREGATED`
  - Example: `sourceType=DIRECT&sourceType=URL_IMPORT`

### Pagination
- **page** (integer, optional, default: 1, >= 1)
  - Page number (1-indexed)
  - Example: `page=2`

- **page_size** (integer, optional, default: 20, 1-100)
  - Number of results per page (max 100)
  - Example: `page_size=50`

## Response Format

```json
{
  "jobs": [
    {
      "id": "uuid",
      "title": "Senior Software Engineer",
      "company": "TechCorp",
      "location": "San Francisco",
      "remote": true,
      "jobType": "FULL_TIME",
      "experienceLevel": "SENIOR",
      "description": "Job description...",
      "salaryMin": 120000,
      "salaryMax": 180000,
      "salaryCurrency": "USD",
      "sourceType": "DIRECT",
      "sourceUrl": "https://example.com/job",
      "qualityScore": 85.0,
      "postedAt": "2024-01-15T10:30:00Z",
      "expiresAt": "2024-02-14T10:30:00Z",
      "featured": false,
      "tags": ["python", "backend"]
    }
  ],
  "total": 42,
  "page": 1,
  "pageSize": 20,
  "totalPages": 3
}
```

## Response Fields

### Job Object
- **id**: Unique job identifier (UUID)
- **title**: Job title
- **company**: Company name
- **location**: Job location
- **remote**: Whether job is remote
- **jobType**: Type of employment
- **experienceLevel**: Required experience level
- **description**: Full job description
- **salaryMin**: Minimum salary (nullable)
- **salaryMax**: Maximum salary (nullable)
- **salaryCurrency**: Salary currency code (default: USD)
- **sourceType**: How job was added to platform
- **sourceUrl**: Original job posting URL (nullable)
- **qualityScore**: Quality score (0-100)
- **postedAt**: When job was posted (ISO 8601)
- **expiresAt**: When job expires (ISO 8601)
- **featured**: Whether job is featured
- **tags**: Array of job tags (nullable)

### Pagination Metadata
- **total**: Total number of matching jobs
- **page**: Current page number
- **pageSize**: Number of results per page
- **totalPages**: Total number of pages

## Usage Examples

### 1. Basic Search
Search for "software engineer" jobs:
```bash
curl "http://localhost:8000/api/jobs/search?query=software+engineer"
```

### 2. Location-Based Search
Find remote jobs in San Francisco:
```bash
curl "http://localhost:8000/api/jobs/search?location=San+Francisco&remote=true"
```

### 3. Filtered Search
Full-time senior positions with salary range:
```bash
curl "http://localhost:8000/api/jobs/search?jobType=FULL_TIME&experienceLevel=SENIOR&salaryMin=100000&salaryMax=200000"
```

### 4. Recent Jobs
Jobs posted in the last 7 days:
```bash
curl "http://localhost:8000/api/jobs/search?postedWithin=7"
```

### 5. Multiple Filters
Complex search with multiple criteria:
```bash
curl "http://localhost:8000/api/jobs/search?query=python&location=New+York&remote=true&jobType=FULL_TIME&jobType=CONTRACT&salaryMin=80000&page=1&page_size=20"
```

### 6. Pagination
Get second page of results:
```bash
curl "http://localhost:8000/api/jobs/search?query=developer&page=2&page_size=10"
```

### 7. Direct Posts Only
Only show jobs posted directly by employers:
```bash
curl "http://localhost:8000/api/jobs/search?sourceType=DIRECT"
```

### 8. Entry-Level Jobs
Find entry-level positions:
```bash
curl "http://localhost:8000/api/jobs/search?experienceLevel=ENTRY&postedWithin=30"
```

## JavaScript/TypeScript Example

```typescript
interface SearchParams {
  query?: string;
  location?: string;
  jobType?: string[];
  experienceLevel?: string[];
  salaryMin?: number;
  salaryMax?: number;
  remote?: boolean;
  postedWithin?: number;
  sourceType?: string[];
  page?: number;
  page_size?: number;
}

async function searchJobs(params: SearchParams) {
  const queryString = new URLSearchParams();
  
  // Add single-value parameters
  if (params.query) queryString.append('query', params.query);
  if (params.location) queryString.append('location', params.location);
  if (params.salaryMin) queryString.append('salaryMin', params.salaryMin.toString());
  if (params.salaryMax) queryString.append('salaryMax', params.salaryMax.toString());
  if (params.remote !== undefined) queryString.append('remote', params.remote.toString());
  if (params.postedWithin) queryString.append('postedWithin', params.postedWithin.toString());
  if (params.page) queryString.append('page', params.page.toString());
  if (params.page_size) queryString.append('page_size', params.page_size.toString());
  
  // Add array parameters
  params.jobType?.forEach(type => queryString.append('jobType', type));
  params.experienceLevel?.forEach(level => queryString.append('experienceLevel', level));
  params.sourceType?.forEach(type => queryString.append('sourceType', type));
  
  const response = await fetch(`/api/jobs/search?${queryString}`);
  return response.json();
}

// Usage
const results = await searchJobs({
  query: 'software engineer',
  location: 'San Francisco',
  remote: true,
  jobType: ['FULL_TIME'],
  experienceLevel: ['SENIOR', 'LEAD'],
  salaryMin: 120000,
  page: 1,
  page_size: 20
});

console.log(`Found ${results.total} jobs`);
results.jobs.forEach(job => {
  console.log(`${job.title} at ${job.company}`);
});
```

## Python Example

```python
import requests

def search_jobs(
    query=None,
    location=None,
    job_type=None,
    experience_level=None,
    salary_min=None,
    salary_max=None,
    remote=None,
    posted_within=None,
    source_type=None,
    page=1,
    page_size=20
):
    """Search for jobs using the API."""
    params = {}
    
    # Add parameters if provided
    if query:
        params['query'] = query
    if location:
        params['location'] = location
    if salary_min:
        params['salaryMin'] = salary_min
    if salary_max:
        params['salaryMax'] = salary_max
    if remote is not None:
        params['remote'] = remote
    if posted_within:
        params['postedWithin'] = posted_within
    if page:
        params['page'] = page
    if page_size:
        params['page_size'] = page_size
    
    # Add array parameters
    if job_type:
        params['jobType'] = job_type if isinstance(job_type, list) else [job_type]
    if experience_level:
        params['experienceLevel'] = experience_level if isinstance(experience_level, list) else [experience_level]
    if source_type:
        params['sourceType'] = source_type if isinstance(source_type, list) else [source_type]
    
    response = requests.get('http://localhost:8000/api/jobs/search', params=params)
    response.raise_for_status()
    return response.json()

# Usage
results = search_jobs(
    query='python developer',
    location='New York',
    remote=True,
    job_type=['FULL_TIME', 'CONTRACT'],
    experience_level=['MID', 'SENIOR'],
    salary_min=80000,
    page=1,
    page_size=20
)

print(f"Found {results['total']} jobs")
for job in results['jobs']:
    print(f"{job['title']} at {job['company']}")
```

## Error Responses

### 422 Validation Error
Invalid parameters:
```json
{
  "detail": [
    {
      "loc": ["query", "page_size"],
      "msg": "ensure this value is less than or equal to 100",
      "type": "value_error.number.not_le"
    }
  ]
}
```

### 500 Internal Server Error
Server error (rare):
```json
{
  "detail": "Internal server error"
}
```

## Performance Notes

### Caching
- Popular searches are cached for 5 minutes
- Cache hit returns results in ~1-5ms
- Cache miss queries database (~50-100ms)

### Pagination
- Maximum page size is 100 results
- Use smaller page sizes for faster response times
- Total count is accurate but may be expensive for large result sets

### Sorting
- Results are sorted by:
  1. Featured status (featured jobs first)
  2. Quality score (higher is better)
  3. Posted date (newer is better)

### Filters
- All filters are optional
- Multiple filters are combined with AND logic
- Array filters (jobType, experienceLevel, sourceType) use OR logic within the array

## Best Practices

1. **Use specific filters**: More specific searches are faster and more relevant
2. **Limit page size**: Use smaller page sizes (10-20) for better performance
3. **Cache on client**: Cache results on the client side for repeated searches
4. **Debounce search input**: Wait for user to stop typing before searching
5. **Show loading state**: Search can take 50-100ms, show loading indicator
6. **Handle empty results**: Always check if `total` is 0 before displaying jobs
7. **Use pagination**: Don't try to load all results at once
8. **Validate parameters**: Validate parameters on client before sending request

## Rate Limiting

- Rate limit: 100 requests per minute per user
- Exceeding rate limit returns 429 Too Many Requests
- Use caching to reduce API calls

## Support

For issues or questions:
- Check the API documentation at `/docs`
- Review the completion document at `TASK_17_COMPLETION.md`
- Run manual tests with `python test_search_api_manual.py`
