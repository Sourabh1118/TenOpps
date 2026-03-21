# Job API Quick Reference

## Overview
Quick reference guide for the Job API endpoints. All endpoints are prefixed with `/api/jobs`.

## Authentication
Most endpoints require employer authentication via JWT token:
```
Authorization: Bearer <access_token>
```

## Endpoints

### 1. Create Direct Job Post
**POST** `/api/jobs/direct`

**Auth:** Required (Employer)

**Request Body:**
```json
{
  "title": "Senior Python Developer",
  "company": "Tech Corp",
  "location": "San Francisco, CA",
  "remote": true,
  "job_type": "full_time",
  "experience_level": "senior",
  "description": "We are looking for an experienced Python developer...",
  "requirements": ["5+ years Python", "Django/FastAPI"],
  "responsibilities": ["Build APIs", "Mentor juniors"],
  "salary_min": 120000,
  "salary_max": 180000,
  "salary_currency": "USD",
  "expires_at": "2024-04-15T00:00:00Z",
  "featured": false,
  "tags": ["python", "backend"]
}
```

**Response (201):**
```json
{
  "job_id": "123e4567-e89b-12d3-a456-426614174000",
  "message": "Job posted successfully"
}
```

**Errors:**
- 400: Invalid input
- 401: Unauthorized
- 403: Quota exceeded
- 422: Validation error

---

### 2. Get Job by ID
**GET** `/api/jobs/{job_id}`

**Auth:** Not required

**Response (200):**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "title": "Senior Python Developer",
  "company": "Tech Corp",
  "location": "San Francisco, CA",
  "remote": true,
  "job_type": "full_time",
  "experience_level": "senior",
  "description": "...",
  "requirements": ["..."],
  "responsibilities": ["..."],
  "salary_min": 120000,
  "salary_max": 180000,
  "salary_currency": "USD",
  "source_type": "direct",
  "employer_id": "...",
  "quality_score": 95.0,
  "status": "active",
  "posted_at": "2024-03-15T10:00:00Z",
  "expires_at": "2024-04-15T00:00:00Z",
  "application_count": 15,
  "view_count": 234,
  "featured": false,
  "tags": ["python", "backend"]
}
```

**Errors:**
- 404: Job not found

---

### 3. Get Employer's Jobs
**GET** `/api/jobs/employer/{employer_id}`

**Auth:** Required (Employer - must match employer_id)

**Query Parameters:**
- `status_filter` (optional): Filter by status (active, expired, filled, deleted)

**Example:**
```
GET /api/jobs/employer/123e4567-e89b-12d3-a456-426614174000?status_filter=active
```

**Response (200):**
```json
{
  "jobs": [
    {
      "id": "...",
      "title": "...",
      ...
    }
  ],
  "total": 25,
  "page": 1,
  "page_size": 25
}
```

**Errors:**
- 401: Unauthorized
- 403: Forbidden (not your jobs)

---

### 4. Update Job
**PATCH** `/api/jobs/{job_id}`

**Auth:** Required (Employer - must own job)

**Request Body (all fields optional):**
```json
{
  "description": "Updated description...",
  "salary_min": 130000,
  "salary_max": 190000,
  "requirements": ["Updated requirements"],
  "tags": ["python", "backend", "api"]
}
```

**Response (200):**
```json
{
  "id": "...",
  "title": "...",
  "description": "Updated description...",
  "salary_min": 130000,
  "salary_max": 190000,
  "quality_score": 96.5,
  ...
}
```

**Notes:**
- Quality score is automatically recalculated if relevant fields change
- Only provided fields are updated

**Errors:**
- 401: Unauthorized
- 403: Forbidden (not your job)
- 404: Job not found
- 422: Validation error

---

### 5. Delete Job
**DELETE** `/api/jobs/{job_id}`

**Auth:** Required (Employer - must own job)

**Response (200):**
```json
{
  "message": "Job deleted successfully"
}
```

**Notes:**
- Soft delete - sets status to 'deleted'
- Job remains in database

**Errors:**
- 401: Unauthorized
- 403: Forbidden (not your job)
- 404: Job not found

---

### 6. Mark Job as Filled
**POST** `/api/jobs/{job_id}/mark-filled`

**Auth:** Required (Employer - must own job)

**Response (200):**
```json
{
  "message": "Job marked as filled"
}
```

**Notes:**
- Sets status to 'filled'
- Useful when position is filled

**Errors:**
- 401: Unauthorized
- 403: Forbidden (not your job)
- 404: Job not found

---

### 7. Increment View Count
**POST** `/api/jobs/{job_id}/increment-view`

**Auth:** Not required

**Response (200):**
```json
{
  "message": "View count incremented"
}
```

**Notes:**
- Call when job is viewed
- Uses Redis batching (updates DB every 10 views)
- Optimized for high traffic

**Errors:**
- 404: Job not found

---

## Validation Rules

### Title
- Minimum: 10 characters
- Maximum: 200 characters
- Required

### Company
- Minimum: 2 characters
- Maximum: 100 characters
- Required

### Description
- Minimum: 50 characters
- Maximum: 5000 characters
- Required

### Salary Range
- Both must be >= 0
- salary_min must be < salary_max
- Optional

### Expiration Date
- Must be in the future
- Must be within 90 days from now
- Required

## Job Types
- `full_time`
- `part_time`
- `contract`
- `freelance`
- `internship`
- `fellowship`
- `academic`

## Experience Levels
- `entry`
- `mid`
- `senior`
- `lead`
- `executive`

## Job Status
- `active` - Job is live and accepting applications
- `expired` - Job has passed expiration date
- `filled` - Position has been filled
- `deleted` - Job has been deleted by employer

## Source Types
- `direct` - Posted directly by employer
- `url_import` - Imported via URL by employer
- `aggregated` - Automatically scraped

## Quality Score
- Range: 0-100
- Higher score = better visibility in search
- Factors:
  - Source type (direct = highest)
  - Field completeness
  - Job freshness

## Example Usage with cURL

### Create Job
```bash
curl -X POST http://localhost:8000/api/jobs/direct \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Senior Python Developer",
    "company": "Tech Corp",
    "location": "San Francisco, CA",
    "remote": true,
    "job_type": "full_time",
    "experience_level": "senior",
    "description": "We are looking for an experienced Python developer...",
    "expires_at": "2024-04-15T00:00:00Z"
  }'
```

### Get Job
```bash
curl http://localhost:8000/api/jobs/123e4567-e89b-12d3-a456-426614174000
```

### Update Job
```bash
curl -X PATCH http://localhost:8000/api/jobs/123e4567-e89b-12d3-a456-426614174000 \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Updated description",
    "salary_min": 130000
  }'
```

### Delete Job
```bash
curl -X DELETE http://localhost:8000/api/jobs/123e4567-e89b-12d3-a456-426614174000 \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Increment View
```bash
curl -X POST http://localhost:8000/api/jobs/123e4567-e89b-12d3-a456-426614174000/increment-view
```

## Common Errors

### 401 Unauthorized
- Missing or invalid JWT token
- Token expired
- Solution: Login again to get new token

### 403 Forbidden
- Quota exceeded
- Trying to access/modify another employer's job
- Solution: Check subscription or verify job ownership

### 404 Not Found
- Job ID doesn't exist
- Solution: Verify job ID is correct

### 422 Validation Error
- Invalid input data
- Field constraints violated
- Solution: Check validation rules above

## Tips

1. **Always validate locally first** - Use Pydantic schemas to validate before sending
2. **Handle quota limits** - Check subscription before posting
3. **Use batch view updates** - The API automatically batches view counts
4. **Monitor quality scores** - Higher scores = better visibility
5. **Set appropriate expiration** - Max 90 days, choose based on urgency
6. **Use featured wisely** - Limited quota, use for important positions
7. **Update regularly** - Keep job descriptions current to maintain quality score

## Integration Examples

### Python (requests)
```python
import requests
from datetime import datetime, timedelta

# Create job
token = "your_jwt_token"
headers = {"Authorization": f"Bearer {token}"}

job_data = {
    "title": "Senior Python Developer",
    "company": "Tech Corp",
    "location": "San Francisco, CA",
    "remote": True,
    "job_type": "full_time",
    "experience_level": "senior",
    "description": "We are looking for an experienced Python developer...",
    "expires_at": (datetime.utcnow() + timedelta(days=30)).isoformat()
}

response = requests.post(
    "http://localhost:8000/api/jobs/direct",
    json=job_data,
    headers=headers
)

if response.status_code == 201:
    job_id = response.json()["job_id"]
    print(f"Job created: {job_id}")
else:
    print(f"Error: {response.json()}")
```

### JavaScript (fetch)
```javascript
// Create job
const token = "your_jwt_token";

const jobData = {
  title: "Senior Python Developer",
  company: "Tech Corp",
  location: "San Francisco, CA",
  remote: true,
  job_type: "full_time",
  experience_level: "senior",
  description: "We are looking for an experienced Python developer...",
  expires_at: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString()
};

const response = await fetch("http://localhost:8000/api/jobs/direct", {
  method: "POST",
  headers: {
    "Authorization": `Bearer ${token}`,
    "Content-Type": "application/json"
  },
  body: JSON.stringify(jobData)
});

if (response.ok) {
  const data = await response.json();
  console.log("Job created:", data.job_id);
} else {
  const error = await response.json();
  console.error("Error:", error);
}
```

## Support

For issues or questions:
1. Check validation rules above
2. Verify authentication token
3. Check subscription quota
4. Review error messages
5. Consult TASK_7_COMPLETION.md for detailed implementation notes
