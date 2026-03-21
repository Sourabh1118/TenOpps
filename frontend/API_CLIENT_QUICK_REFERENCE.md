# API Client Quick Reference

## Import

```typescript
import { 
  authApi, 
  jobsApi, 
  searchApi, 
  applicationsApi, 
  subscriptionsApi,
  urlImportApi,
  analyticsApi,
  adminApi 
} from '@/lib/api'
```

## Authentication

```typescript
// Login
const { access_token, refresh_token } = await authApi.login({ email, password })

// Register Employer
await authApi.registerEmployer({ email, password, company_name })

// Register Job Seeker
await authApi.registerJobSeeker({ email, password, full_name })

// Logout
await authApi.logout(refreshToken)

// Refresh Token (automatic via interceptor)
const { access_token } = await authApi.refreshToken(refreshToken)
```

## Jobs

```typescript
// Create
const { job_id } = await jobsApi.createDirectJob({ title, company, ... })

// Read
const job = await jobsApi.getJobById(jobId)
const { jobs, total } = await jobsApi.getJobsByEmployer(employerId, page, pageSize)

// Update
const updated = await jobsApi.updateJob(jobId, { title, description })

// Delete
await jobsApi.deleteJob(jobId)

// Actions
await jobsApi.markJobAsFilled(jobId)
await jobsApi.featureJob(jobId)
await jobsApi.incrementViewCount(jobId)
await jobsApi.reactivateJob(jobId, { expires_at })
```

## Search

```typescript
const results = await searchApi.searchJobs({
  query: 'software engineer',
  location: 'San Francisco',
  jobType: ['FULL_TIME'],
  experienceLevel: ['SENIOR'],
  salaryMin: 100000,
  remote: true,
  postedWithin: 7,
  page: 1,
  page_size: 20,
})
```

## Applications

```typescript
// Submit (Job Seeker)
const { application_id } = await applicationsApi.submitApplication({
  job_id: jobId,
  resume: 'https://...',
  cover_letter: '...',
})

// Get My Applications (Job Seeker)
const { applications } = await applicationsApi.getMyApplications()

// Get Job Applications (Employer)
const { applications } = await applicationsApi.getApplicationsForJob(jobId)

// Update Status (Employer)
await applicationsApi.updateApplicationStatus(applicationId, {
  status: 'SHORTLISTED',
  employer_notes: '...',
})
```

## Subscriptions

```typescript
// Get Info
const subscription = await subscriptionsApi.getSubscriptionInfo()

// Update
await subscriptionsApi.updateSubscription({ new_tier: 'PREMIUM' })
```

## URL Import

```typescript
// Import
const { task_id } = await urlImportApi.importJobFromURL({ url })

// Check Status
const status = await urlImportApi.getImportStatus(task_id)
```

## Analytics

```typescript
// Employer Summary
const summary = await analyticsApi.getEmployerAnalyticsSummary(30)

// Job Analytics
const analytics = await analyticsApi.getJobAnalytics(jobId)

// Popular Searches
const searches = await analyticsApi.getPopularSearches(10)

// Scraping Metrics
const metrics = await analyticsApi.getScrapingMetrics()

// System Health (Admin)
const health = await analyticsApi.getSystemHealthMetrics()

// Slow Requests (Admin)
const slow = await analyticsApi.getSlowAPIRequests(1000, 50)
```

## Admin

```typescript
// Rate Limit Violations
const violations = await adminApi.getRateLimitViolations(userId)
const violators = await adminApi.getRateLimitViolators(10)
const stats = await adminApi.getRateLimitStats()

// Clear Violations
await adminApi.clearRateLimitViolations(userId)
```

## Error Handling

```typescript
import { AxiosError } from 'axios'

try {
  const job = await jobsApi.getJobById(jobId)
} catch (error) {
  if (error instanceof AxiosError) {
    // 401 handled automatically by interceptor
    if (error.response?.status === 404) {
      console.error('Not found')
    } else if (error.response?.status === 403) {
      console.error('Access denied')
    } else {
      console.error(error.response?.data?.detail)
    }
  }
}
```

## Token Management

Tokens are managed automatically:
- Access token attached to all requests
- 401 triggers automatic refresh
- Failed refresh redirects to login
- No manual token handling needed

## Configuration

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_API_BASE_PATH=/api
```

## Best Practices

1. ✅ Use typed API clients (not raw `apiClient`)
2. ✅ Let interceptor handle 401 errors
3. ✅ Handle other errors (403, 404, 500)
4. ✅ Use TypeScript types from imports
5. ✅ Wrap in React Query for caching

## React Query Example

```typescript
import { useQuery } from '@tanstack/react-query'
import { jobsApi } from '@/lib/api'

function useJob(jobId: string) {
  return useQuery({
    queryKey: ['job', jobId],
    queryFn: () => jobsApi.getJobById(jobId),
  })
}

// Usage
const { data: job, isLoading, error } = useJob(jobId)
```
