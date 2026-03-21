# API Client Utilities Guide

## Overview

The API client utilities provide typed, centralized access to all backend endpoints with automatic JWT token handling, token refresh, and error handling.

## Architecture

### Core Components

1. **API Client (`lib/api-client.ts`)**
   - Axios instance with base URL configuration
   - Request interceptor for JWT token attachment
   - Response interceptor for 401 handling and token refresh
   - Request queuing during token refresh

2. **Typed API Clients (`lib/api/*.ts`)**
   - `auth.ts` - Authentication endpoints
   - `jobs.ts` - Job management endpoints
   - `search.ts` - Job search endpoints
   - `applications.ts` - Application management endpoints
   - `subscriptions.ts` - Subscription management endpoints
   - `url-import.ts` - URL import endpoints
   - `analytics.ts` - Analytics endpoints
   - `admin.ts` - Admin endpoints

## Features

### 1. Automatic JWT Token Handling

The request interceptor automatically attaches the JWT access token to all requests:

```typescript
// Token is automatically attached from localStorage
const jobs = await jobsApi.getJobsByEmployer(employerId)
```

### 2. Token Refresh on 401

When a request receives a 401 response, the interceptor:
1. Attempts to refresh the token using the refresh token
2. Queues any concurrent requests
3. Retries the original request with the new token
4. Processes all queued requests
5. Redirects to login if refresh fails

```typescript
// Automatic token refresh - no manual handling needed
try {
  const job = await jobsApi.getJobById(jobId)
} catch (error) {
  // Only reaches here if refresh fails
  // User is automatically redirected to login
}
```

### 3. Request Queuing

Multiple concurrent requests that receive 401 are queued and processed after token refresh:

```typescript
// All three requests will be queued and retried after refresh
const [jobs, applications, subscription] = await Promise.all([
  jobsApi.getJobsByEmployer(employerId),
  applicationsApi.getMyApplications(),
  subscriptionsApi.getSubscriptionInfo(),
])
```

## Usage Examples

### Authentication

```typescript
import { authApi } from '@/lib/api'

// Login
const response = await authApi.login({
  email: 'user@example.com',
  password: 'password123',
})

// Store tokens
localStorage.setItem('accessToken', response.access_token)
localStorage.setItem('refreshToken', response.refresh_token)

// Register employer
const employerResponse = await authApi.registerEmployer({
  email: 'employer@example.com',
  password: 'password123',
  company_name: 'Tech Corp',
  company_website: 'https://techcorp.com',
})

// Logout
await authApi.logout(refreshToken)
```

### Job Management

```typescript
import { jobsApi } from '@/lib/api'

// Create a job
const createResponse = await jobsApi.createDirectJob({
  title: 'Senior Software Engineer',
  company: 'Tech Corp',
  location: 'San Francisco, CA',
  remote: true,
  job_type: 'FULL_TIME',
  experience_level: 'SENIOR',
  description: 'We are looking for...',
  requirements: ['5+ years experience', 'Python expertise'],
  salary_min: 150000,
  salary_max: 200000,
  salary_currency: 'USD',
  expires_at: '2024-12-31T23:59:59Z',
  featured: false,
  tags: ['python', 'backend', 'remote'],
})

// Get job by ID
const job = await jobsApi.getJobById(jobId)

// Update job
const updatedJob = await jobsApi.updateJob(jobId, {
  title: 'Updated Title',
  description: 'Updated description',
})

// Feature a job
await jobsApi.featureJob(jobId)

// Mark as filled
await jobsApi.markJobAsFilled(jobId)

// Delete job
await jobsApi.deleteJob(jobId)
```

### Job Search

```typescript
import { searchApi } from '@/lib/api'

// Search with filters
const results = await searchApi.searchJobs({
  query: 'software engineer',
  location: 'San Francisco',
  jobType: ['FULL_TIME', 'CONTRACT'],
  experienceLevel: ['MID', 'SENIOR'],
  salaryMin: 100000,
  remote: true,
  postedWithin: 7,
  page: 1,
  page_size: 20,
})

console.log(`Found ${results.total} jobs`)
results.jobs.forEach(job => {
  console.log(`${job.title} at ${job.company}`)
})
```

### Applications

```typescript
import { applicationsApi } from '@/lib/api'

// Submit application (job seeker)
const submitResponse = await applicationsApi.submitApplication({
  job_id: jobId,
  resume: 'https://storage.example.com/resumes/john-doe.pdf',
  cover_letter: 'I am excited to apply...',
})

// Get my applications (job seeker)
const myApps = await applicationsApi.getMyApplications()

// Get applications for a job (employer)
const jobApps = await applicationsApi.getApplicationsForJob(jobId)

// Update application status (employer)
await applicationsApi.updateApplicationStatus(applicationId, {
  status: 'SHORTLISTED',
  employer_notes: 'Strong candidate, schedule interview',
})
```

### Subscriptions

```typescript
import { subscriptionsApi } from '@/lib/api'

// Get subscription info
const subscription = await subscriptionsApi.getSubscriptionInfo()
console.log(`Tier: ${subscription.tier}`)
console.log(`Posts used: ${subscription.monthly_posts_used}/${subscription.monthly_posts_limit}`)

// Update subscription
const updateResponse = await subscriptionsApi.updateSubscription({
  new_tier: 'PREMIUM',
})
```

### URL Import

```typescript
import { urlImportApi } from '@/lib/api'

// Import job from URL
const importResponse = await urlImportApi.importJobFromURL({
  url: 'https://linkedin.com/jobs/view/123456',
})

console.log(`Import task ID: ${importResponse.task_id}`)

// Poll for status
const checkStatus = async (taskId: string) => {
  const status = await urlImportApi.getImportStatus(taskId)
  
  if (status.status === 'COMPLETED') {
    console.log(`Job imported: ${status.job_id}`)
  } else if (status.status === 'FAILED') {
    console.error(`Import failed: ${status.error_message}`)
  } else {
    // Still processing, check again later
    setTimeout(() => checkStatus(taskId), 2000)
  }
}

checkStatus(importResponse.task_id)
```

### Analytics

```typescript
import { analyticsApi } from '@/lib/api'

// Get employer analytics summary
const summary = await analyticsApi.getEmployerAnalyticsSummary(30)
console.log(`Total jobs: ${summary.total_jobs}`)
console.log(`Total views: ${summary.total_views}`)
console.log(`Total applications: ${summary.total_applications}`)

// Get job analytics
const jobAnalytics = await analyticsApi.getJobAnalytics(jobId)
console.log(`Views: ${jobAnalytics.view_count}`)
console.log(`Applications: ${jobAnalytics.application_count}`)

// Get popular searches
const popularSearches = await analyticsApi.getPopularSearches(10)
popularSearches.forEach(search => {
  console.log(`${search.query}: ${search.count} searches`)
})
```

### Admin

```typescript
import { adminApi } from '@/lib/api'

// Get rate limit violations
const violations = await adminApi.getRateLimitViolations(userId)

// Get top violators
const violators = await adminApi.getRateLimitViolators(10)

// Get rate limit stats
const stats = await adminApi.getRateLimitStats()

// Clear violations
await adminApi.clearRateLimitViolations(userId)
```

## Error Handling

### Standard Error Handling

```typescript
import { AxiosError } from 'axios'

try {
  const job = await jobsApi.getJobById(jobId)
} catch (error) {
  if (error instanceof AxiosError) {
    if (error.response?.status === 404) {
      console.error('Job not found')
    } else if (error.response?.status === 403) {
      console.error('Access denied')
    } else {
      console.error('API error:', error.response?.data?.detail)
    }
  }
}
```

### Automatic 401 Handling

401 errors are handled automatically by the interceptor. You only need to handle other error cases:

```typescript
try {
  const jobs = await jobsApi.getJobsByEmployer(employerId)
} catch (error) {
  // 401 is handled automatically
  // This only catches other errors (403, 404, 500, etc.)
  console.error('Error fetching jobs:', error)
}
```

## Configuration

### Environment Variables

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_API_BASE_PATH=/api
```

### Timeout Configuration

The default timeout is 30 seconds. To modify:

```typescript
// In lib/api-client.ts
const apiClient = axios.create({
  baseURL: `${API_URL}${API_BASE_PATH}`,
  timeout: 60000, // 60 seconds
  headers: {
    'Content-Type': 'application/json',
  },
})
```

## Testing

### Unit Tests

Tests are located in `lib/api/__tests__/`:

```bash
npm run test lib/api
```

### Mock API Client

For component testing:

```typescript
import { vi } from 'vitest'
import { jobsApi } from '@/lib/api'

vi.mock('@/lib/api', () => ({
  jobsApi: {
    getJobById: vi.fn(),
    createDirectJob: vi.fn(),
  },
}))

// In test
vi.mocked(jobsApi.getJobById).mockResolvedValue(mockJob)
```

## Best Practices

1. **Always use typed API clients** - Don't use `apiClient` directly
2. **Handle errors appropriately** - 401 is automatic, handle others
3. **Use TypeScript types** - Import types from `@/lib/api`
4. **Don't store tokens manually** - The interceptor handles this
5. **Use React Query for caching** - Wrap API calls in React Query hooks

## Requirements Validation

This implementation satisfies:

- **Requirement 12.5**: JWT token handling with automatic refresh
- **Requirement 12.6**: 401 error handling and token refresh logic
- All API endpoints are typed and accessible through client functions
- Request/response interceptors properly configured
- Token refresh queue prevents multiple refresh attempts
- Automatic redirect to login on refresh failure

## Related Files

- `lib/api-client.ts` - Core axios instance with interceptors
- `lib/api/*.ts` - Typed API client functions
- `lib/api/index.ts` - Central exports
- `lib/store.ts` - Auth state management
- `components/auth/ProtectedRoute.tsx` - Route protection
