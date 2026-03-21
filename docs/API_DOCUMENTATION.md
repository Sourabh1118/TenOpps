# Job Aggregation Platform - API Documentation

## Overview

The Job Aggregation Platform API is a RESTful API built with FastAPI that provides endpoints for job seekers, employers, and administrators. The API supports automated job aggregation, direct job posting, application tracking, and subscription management.

**Base URL**: `https://api.jobplatform.com/api`

**API Version**: 1.0.0

**Authentication**: JWT Bearer tokens

## Table of Contents

1. [Authentication](#authentication)
2. [Error Handling](#error-handling)
3. [Rate Limiting](#rate-limiting)
4. [Endpoints](#endpoints)
   - [Authentication](#authentication-endpoints)
   - [Jobs](#jobs-endpoints)
   - [Search](#search-endpoints)
   - [Applications](#applications-endpoints)
   - [Subscriptions](#subscriptions-endpoints)
   - [URL Import](#url-import-endpoints)
   - [Analytics](#analytics-endpoints)
   - [Privacy](#privacy-endpoints)

---

## Authentication

The API uses JWT (JSON Web Tokens) for authentication. Tokens are issued upon successful login and must be included in the `Authorization` header for protected endpoints.

### Token Types

1. **Access Token**: Short-lived token (15 minutes) for API requests
2. **Refresh Token**: Long-lived token (7 days) for obtaining new access tokens

### Authentication Flow

```
1. User logs in with credentials
2. Server returns access_token and refresh_token
3. Client includes access_token in Authorization header
4. When access_token expires, use refresh_token to get new access_token
```

### Authorization Header Format

```
Authorization: Bearer <access_token>
```

### Example

```bash
curl -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  https://api.jobplatform.com/api/jobs/123
```

---

## Error Handling

The API uses standard HTTP status codes and returns error details in JSON format.

### HTTP Status Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request - Invalid input |
| 401 | Unauthorized - Invalid or missing token |
| 403 | Forbidden - Insufficient permissions or quota exceeded |
| 404 | Not Found |
| 409 | Conflict - Resource already exists |
| 422 | Unprocessable Entity - Validation error |
| 429 | Too Many Requests - Rate limit exceeded |
| 500 | Internal Server Error |
| 503 | Service Unavailable |

### Error Response Format

```json
{
  "detail": "Error message describing what went wrong",
  "error_code": "SPECIFIC_ERROR_CODE",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Common Error Codes

- `INVALID_CREDENTIALS`: Login failed due to incorrect email or password
- `TOKEN_EXPIRED`: JWT token has expired
- `QUOTA_EXCEEDED`: Subscription quota limit reached
- `VALIDATION_ERROR`: Input validation failed
- `RESOURCE_NOT_FOUND`: Requested resource does not exist
- `DUPLICATE_RESOURCE`: Resource already exists
- `RATE_LIMIT_EXCEEDED`: Too many requests

---

## Rate Limiting

API requests are rate-limited based on subscription tier:

| Tier | Rate Limit |
|------|------------|
| Free | 100 requests/minute |
| Basic | 200 requests/minute |
| Premium | 500 requests/minute |

### Rate Limit Headers

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1642248600
```

### Rate Limit Exceeded Response

```json
{
  "detail": "Too many requests. Please try again later.",
  "retry_after": 60
}
```

**HTTP Status**: 429 Too Many Requests

**Headers**: `Retry-After: 60`

---

## Endpoints

### Authentication Endpoints

#### POST /auth/register/employer

Register a new employer account.

**Authentication**: None required

**Request Body**:
```json
{
  "email": "employer@company.com",
  "password": "SecurePass123!",
  "company_name": "Tech Corp",
  "company_website": "https://techcorp.com",
  "company_description": "Leading technology company"
}
```

**Password Requirements**:
- Minimum 8 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one digit
- At least one special character

**Response** (201 Created):
```json
{
  "user_id": "123e4567-e89b-12d3-a456-426614174000",
  "role": "employer",
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Errors**:
- 400: Weak password or invalid input
- 409: Email already registered

---

#### POST /auth/register/job-seeker

Register a new job seeker account.

**Authentication**: None required

**Request Body**:
```json
{
  "email": "jobseeker@example.com",
  "password": "SecurePass123!",
  "full_name": "John Doe",
  "phone": "+1234567890"
}
```

**Response** (201 Created):
```json
{
  "user_id": "123e4567-e89b-12d3-a456-426614174000",
  "role": "job_seeker",
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Errors**:
- 400: Weak password or invalid input
- 409: Email already registered

---

#### POST /auth/login

Login with email and password.

**Authentication**: None required

**Request Body**:
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!"
}
```

**Response** (200 OK):
```json
{
  "user_id": "123e4567-e89b-12d3-a456-426614174000",
  "role": "employer",
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Errors**:
- 401: Invalid email or password
- 429: Too many login attempts (5 per 15 minutes per IP)

---

#### POST /auth/refresh

Refresh access token using refresh token.

**Authentication**: Refresh token required

**Headers**:
```
Authorization: Bearer <refresh_token>
```

**Response** (200 OK):
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Errors**:
- 401: Invalid or expired refresh token

---

#### POST /auth/logout

Logout and invalidate refresh token.

**Authentication**: Required

**Request Body**:
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response** (200 OK):
```json
{
  "message": "Successfully logged out",
  "detail": "Refresh token has been invalidated"
}
```

**Errors**:
- 401: Invalid or expired token

---

### Jobs Endpoints

#### POST /jobs/direct

Create a direct job posting (employers only).

**Authentication**: Required (employer role)

**Request Body**:
```json
{
  "title": "Senior Python Developer",
  "company": "Tech Corp",
  "location": "San Francisco, CA",
  "remote": true,
  "job_type": "full_time",
  "experience_level": "senior",
  "description": "We are looking for an experienced Python developer...",
  "requirements": ["5+ years Python", "Django/FastAPI experience"],
  "responsibilities": ["Build APIs", "Mentor junior developers"],
  "salary_min": 120000,
  "salary_max": 180000,
  "salary_currency": "USD",
  "expires_at": "2024-03-15T00:00:00Z",
  "featured": false,
  "tags": ["python", "backend", "api"]
}
```

**Field Constraints**:
- `title`: 10-200 characters
- `company`: 2-100 characters
- `description`: 50-5000 characters
- `expires_at`: Within 90 days from now
- `salary_min` < `salary_max` (if both provided)

**Job Types**: `full_time`, `part_time`, `contract`, `freelance`, `internship`, `fellowship`, `academic`

**Experience Levels**: `entry`, `mid`, `senior`, `lead`, `executive`

**Response** (201 Created):
```json
{
  "job_id": "123e4567-e89b-12d3-a456-426614174000",
  "message": "Job posted successfully"
}
```

**Errors**:
- 400: Invalid input or validation error
- 403: Monthly posting quota exceeded
- 403: Featured post quota exceeded (if featured=true)

---

#### GET /jobs/{job_id}

Get a single job by ID.

**Authentication**: None required

**Path Parameters**:
- `job_id` (UUID): Job identifier

**Response** (200 OK):
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "title": "Senior Python Developer",
  "company": "Tech Corp",
  "location": "San Francisco, CA",
  "remote": true,
  "job_type": "full_time",
  "experience_level": "senior",
  "description": "We are looking for...",
  "requirements": ["5+ years Python", "Django/FastAPI experience"],
  "responsibilities": ["Build APIs", "Mentor junior developers"],
  "salary_min": 120000,
  "salary_max": 180000,
  "salary_currency": "USD",
  "source_type": "direct",
  "source_url": null,
  "source_platform": null,
  "employer_id": "456e7890-e89b-12d3-a456-426614174000",
  "quality_score": 95.0,
  "status": "active",
  "posted_at": "2024-01-15T10:00:00Z",
  "expires_at": "2024-03-15T00:00:00Z",
  "created_at": "2024-01-15T10:00:00Z",
  "updated_at": "2024-01-15T10:00:00Z",
  "application_count": 15,
  "view_count": 234,
  "featured": false,
  "tags": ["python", "backend", "api"]
}
```

**Errors**:
- 404: Job not found

---

#### GET /jobs/employer/{employer_id}

Get all jobs for a specific employer.

**Authentication**: Required (employer role, must own jobs)

**Path Parameters**:
- `employer_id` (UUID): Employer identifier

**Query Parameters**:
- `status_filter` (optional): Filter by status (`active`, `expired`, `filled`, `deleted`)

**Response** (200 OK):
```json
{
  "jobs": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "title": "Senior Python Developer",
      "company": "Tech Corp",
      "status": "active",
      "posted_at": "2024-01-15T10:00:00Z",
      "application_count": 15,
      "view_count": 234,
      ...
    }
  ],
  "total": 25,
  "page": 1,
  "page_size": 25
}
```

**Errors**:
- 403: Cannot view other employer's jobs

---

#### PATCH /jobs/{job_id}

Update a job posting.

**Authentication**: Required (employer role, must own job)

**Path Parameters**:
- `job_id` (UUID): Job identifier

**Request Body** (all fields optional):
```json
{
  "description": "Updated job description...",
  "salary_min": 130000,
  "salary_max": 190000,
  "requirements": ["Updated requirements"],
  "responsibilities": ["Updated responsibilities"]
}
```

**Response** (200 OK):
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "title": "Senior Python Developer",
  ...
}
```

**Errors**:
- 403: Cannot update other employer's jobs
- 404: Job not found

---

#### DELETE /jobs/{job_id}

Mark a job as deleted.

**Authentication**: Required (employer role, must own job)

**Path Parameters**:
- `job_id` (UUID): Job identifier

**Response** (200 OK):
```json
{
  "message": "Job deleted successfully"
}
```

**Errors**:
- 403: Cannot delete other employer's jobs
- 404: Job not found

---

#### POST /jobs/{job_id}/mark-filled

Mark a job as filled.

**Authentication**: Required (employer role, must own job)

**Path Parameters**:
- `job_id` (UUID): Job identifier

**Response** (200 OK):
```json
{
  "message": "Job marked as filled"
}
```

**Errors**:
- 403: Cannot update other employer's jobs
- 404: Job not found

---

#### POST /jobs/{job_id}/feature

Feature a job posting for enhanced visibility.

**Authentication**: Required (employer role, must own job)

**Path Parameters**:
- `job_id` (UUID): Job identifier

**Response** (200 OK):
```json
{
  "message": "Job featured successfully"
}
```

**Errors**:
- 400: Job is already featured
- 403: Featured post quota exceeded
- 403: Cannot feature other employer's jobs
- 404: Job not found

---

#### POST /jobs/{job_id}/reactivate

Reactivate an expired job with a new expiration date.

**Authentication**: Required (employer role, must own job)

**Path Parameters**:
- `job_id` (UUID): Job identifier

**Request Body**:
```json
{
  "expires_at": "2024-06-15T00:00:00Z"
}
```

**Response** (200 OK):
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "title": "Senior Python Developer",
  "status": "active",
  "expires_at": "2024-06-15T00:00:00Z",
  ...
}
```

**Errors**:
- 400: Job is not expired
- 403: Cannot reactivate other employer's jobs
- 404: Job not found

---

### Search Endpoints

#### GET /search

Search for jobs with filters.

**Authentication**: None required

**Query Parameters**:
- `query` (string, optional): Full-text search query
- `location` (string, optional): Job location
- `job_type` (array, optional): Job types (e.g., `full_time`, `part_time`)
- `experience_level` (array, optional): Experience levels (e.g., `senior`, `mid`)
- `salary_min` (number, optional): Minimum salary
- `salary_max` (number, optional): Maximum salary
- `remote` (boolean, optional): Remote jobs only
- `posted_within` (number, optional): Posted within X days
- `source_type` (array, optional): Source types (`direct`, `url_import`, `aggregated`)
- `page` (number, optional, default: 1): Page number
- `page_size` (number, optional, default: 20, max: 100): Results per page

**Example Request**:
```
GET /search?query=python&location=San Francisco&job_type=full_time&salary_min=100000&remote=true&page=1&page_size=20
```

**Response** (200 OK):
```json
{
  "jobs": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "title": "Senior Python Developer",
      "company": "Tech Corp",
      "location": "San Francisco, CA",
      "remote": true,
      "job_type": "full_time",
      "experience_level": "senior",
      "salary_min": 120000,
      "salary_max": 180000,
      "quality_score": 95.0,
      "posted_at": "2024-01-15T10:00:00Z",
      "featured": false,
      ...
    }
  ],
  "total": 150,
  "page": 1,
  "page_size": 20,
  "total_pages": 8
}
```

**Notes**:
- Featured jobs appear first in results
- Results are sorted by quality_score DESC, then posted_at DESC
- Popular searches are cached for 5 minutes
- Expired and deleted jobs are excluded

---

### Applications Endpoints

#### POST /applications

Submit a job application (job seekers only).

**Authentication**: Required (job_seeker role)

**Request Body** (multipart/form-data):
```
job_id: 123e4567-e89b-12d3-a456-426614174000
resume: <file> (PDF, DOC, DOCX, max 5MB)
cover_letter: Optional cover letter text
```

**Response** (201 Created):
```json
{
  "application_id": "789e0123-e89b-12d3-a456-426614174000",
  "message": "Application submitted successfully"
}
```

**Errors**:
- 400: Invalid file type or size
- 400: Cannot apply to aggregated jobs (only direct posts)
- 404: Job not found

---

#### GET /applications/my-applications

Get all applications for the authenticated job seeker.

**Authentication**: Required (job_seeker role)

**Response** (200 OK):
```json
{
  "applications": [
    {
      "id": "789e0123-e89b-12d3-a456-426614174000",
      "job_id": "123e4567-e89b-12d3-a456-426614174000",
      "job_title": "Senior Python Developer",
      "company": "Tech Corp",
      "status": "reviewed",
      "applied_at": "2024-01-16T14:30:00Z",
      "updated_at": "2024-01-17T09:15:00Z"
    }
  ],
  "total": 12
}
```

**Application Statuses**: `submitted`, `reviewed`, `shortlisted`, `rejected`, `accepted`

---

#### GET /applications/job/{job_id}

Get all applications for a specific job (employers only).

**Authentication**: Required (employer role, must own job)

**Path Parameters**:
- `job_id` (UUID): Job identifier

**Response** (200 OK):
```json
{
  "applications": [
    {
      "id": "789e0123-e89b-12d3-a456-426614174000",
      "job_seeker_id": "456e7890-e89b-12d3-a456-426614174000",
      "applicant_name": "John Doe",
      "resume_url": "https://storage.example.com/resumes/...",
      "cover_letter": "I am very interested in this position...",
      "status": "submitted",
      "applied_at": "2024-01-16T14:30:00Z",
      "updated_at": "2024-01-16T14:30:00Z",
      "employer_notes": null
    }
  ],
  "total": 15
}
```

**Errors**:
- 403: Requires basic or premium subscription tier
- 403: Cannot view applications for other employer's jobs
- 404: Job not found

---

#### PATCH /applications/{application_id}

Update application status (employers only).

**Authentication**: Required (employer role, must own job)

**Path Parameters**:
- `application_id` (UUID): Application identifier

**Request Body**:
```json
{
  "status": "shortlisted",
  "employer_notes": "Strong candidate, schedule interview"
}
```

**Response** (200 OK):
```json
{
  "id": "789e0123-e89b-12d3-a456-426614174000",
  "status": "shortlisted",
  "employer_notes": "Strong candidate, schedule interview",
  "updated_at": "2024-01-17T09:15:00Z"
}
```

**Errors**:
- 400: Invalid status value
- 403: Cannot update applications for other employer's jobs
- 404: Application not found

---

### Subscriptions Endpoints

#### GET /subscription

Get current subscription details for authenticated employer.

**Authentication**: Required (employer role)

**Response** (200 OK):
```json
{
  "employer_id": "123e4567-e89b-12d3-a456-426614174000",
  "subscription_tier": "basic",
  "subscription_start_date": "2024-01-01T00:00:00Z",
  "subscription_end_date": "2024-02-01T00:00:00Z",
  "monthly_posts_used": 5,
  "monthly_posts_limit": 20,
  "featured_posts_used": 1,
  "featured_posts_limit": 2,
  "features": {
    "application_tracking": true,
    "analytics_access": false
  }
}
```

---

#### POST /subscription/upgrade

Upgrade subscription tier.

**Authentication**: Required (employer role)

**Request Body**:
```json
{
  "tier": "premium"
}
```

**Response** (200 OK):
```json
{
  "message": "Subscription upgraded successfully",
  "checkout_url": "https://checkout.stripe.com/..."
}
```

**Notes**:
- Returns Stripe checkout URL for payment
- Subscription is updated after successful payment via webhook

---

### URL Import Endpoints

#### POST /url-import

Import a job from external URL.

**Authentication**: Required (employer role)

**Request Body**:
```json
{
  "url": "https://www.linkedin.com/jobs/view/123456789"
}
```

**Response** (202 Accepted):
```json
{
  "task_id": "abc123def456",
  "message": "Import task queued",
  "status_url": "/api/url-import/status/abc123def456"
}
```

**Errors**:
- 400: Invalid URL format
- 400: Domain not whitelisted
- 403: Import quota exceeded

**Supported Domains**:
- linkedin.com
- indeed.com
- naukri.com
- monster.com
- glassdoor.com

---

#### GET /url-import/status/{task_id}

Get import task status.

**Authentication**: Required (employer role)

**Path Parameters**:
- `task_id` (string): Task identifier

**Response** (200 OK):
```json
{
  "task_id": "abc123def456",
  "status": "completed",
  "job_id": "123e4567-e89b-12d3-a456-426614174000",
  "message": "Job imported successfully"
}
```

**Task Statuses**: `pending`, `running`, `completed`, `failed`

**Failed Response**:
```json
{
  "task_id": "abc123def456",
  "status": "failed",
  "error_message": "Failed to extract job details from URL"
}
```

---

### Analytics Endpoints

#### GET /analytics/job/{job_id}

Get analytics for a specific job (premium employers only).

**Authentication**: Required (employer role, premium tier, must own job)

**Path Parameters**:
- `job_id` (UUID): Job identifier

**Response** (200 OK):
```json
{
  "job_id": "123e4567-e89b-12d3-a456-426614174000",
  "views": 234,
  "applications": 15,
  "conversion_rate": 6.4,
  "views_by_day": [
    {"date": "2024-01-15", "views": 45},
    {"date": "2024-01-16", "views": 67},
    {"date": "2024-01-17", "views": 52}
  ],
  "applications_by_day": [
    {"date": "2024-01-15", "applications": 3},
    {"date": "2024-01-16", "applications": 5},
    {"date": "2024-01-17", "applications": 2}
  ]
}
```

**Errors**:
- 403: Requires premium subscription tier
- 403: Cannot view analytics for other employer's jobs
- 404: Job not found

---

### Privacy Endpoints

#### POST /privacy/export-data

Export all user data (GDPR compliance).

**Authentication**: Required

**Response** (200 OK):
```json
{
  "user_id": "123e4567-e89b-12d3-a456-426614174000",
  "email": "user@example.com",
  "role": "job_seeker",
  "created_at": "2024-01-01T00:00:00Z",
  "profile": {...},
  "applications": [...],
  "activity_history": [...]
}
```

---

#### POST /privacy/delete-account

Request account deletion.

**Authentication**: Required

**Response** (200 OK):
```json
{
  "message": "Account deletion scheduled",
  "deletion_date": "2024-02-15T00:00:00Z",
  "details": "Your account and all personal data will be permanently deleted in 30 days"
}
```

---

## Webhooks

### Stripe Webhook

**Endpoint**: `/api/stripe/webhook`

**Method**: POST

**Authentication**: Stripe signature verification

**Events Handled**:
- `checkout.session.completed`: Subscription upgrade successful
- `invoice.payment_succeeded`: Recurring payment successful
- `invoice.payment_failed`: Payment failed

**Request Headers**:
```
Stripe-Signature: t=1234567890,v1=abc123...
```

---

## OpenAPI/Swagger Documentation

Interactive API documentation is available at:

**Swagger UI**: `https://api.jobplatform.com/docs`

**ReDoc**: `https://api.jobplatform.com/redoc`

**OpenAPI JSON**: `https://api.jobplatform.com/openapi.json`

---

## Code Examples

### Python

```python
import requests

# Login
response = requests.post(
    "https://api.jobplatform.com/api/auth/login",
    json={"email": "user@example.com", "password": "SecurePass123!"}
)
tokens = response.json()
access_token = tokens["access_token"]

# Search jobs
headers = {"Authorization": f"Bearer {access_token}"}
response = requests.get(
    "https://api.jobplatform.com/api/search",
    params={"query": "python", "remote": True},
    headers=headers
)
jobs = response.json()
```

### JavaScript

```javascript
// Login
const loginResponse = await fetch('https://api.jobplatform.com/api/auth/login', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    email: 'user@example.com',
    password: 'SecurePass123!'
  })
});
const tokens = await loginResponse.json();

// Search jobs
const searchResponse = await fetch(
  'https://api.jobplatform.com/api/search?query=python&remote=true',
  {
    headers: {'Authorization': `Bearer ${tokens.access_token}`}
  }
);
const jobs = await searchResponse.json();
```

### cURL

```bash
# Login
curl -X POST https://api.jobplatform.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"SecurePass123!"}'

# Search jobs
curl -X GET "https://api.jobplatform.com/api/search?query=python&remote=true" \
  -H "Authorization: Bearer <access_token>"
```

---

## Support

For API support, contact:
- Email: api-support@jobplatform.com
- Documentation: https://docs.jobplatform.com
- Status Page: https://status.jobplatform.com
