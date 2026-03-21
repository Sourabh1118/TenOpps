# Job Application Interface - Quick Reference Guide

## Overview
The job application interface allows job seekers to apply to direct job postings and track their application status.

## Key Components

### 1. ApplicationForm Component
**Location:** `frontend/components/applications/ApplicationForm.tsx`

**Usage:**
```tsx
import { ApplicationForm } from '@/components/applications'

<ApplicationForm
  jobId="job-uuid"
  jobTitle="Senior Developer"
  company="Tech Corp"
  onSubmit={async (data) => {
    // Handle submission
    await submitApplication(data)
  }}
  onCancel={() => router.back()}
  isSubmitting={false}
/>
```

**Props:**
- `jobId`: string - UUID of the job
- `jobTitle`: string - Job title to display
- `company`: string - Company name to display
- `onSubmit`: (data: { resume: File; coverLetter?: string }) => Promise<void>
- `onCancel`: () => void
- `isSubmitting`: boolean

**Features:**
- File upload with drag-and-drop
- File validation (PDF, DOC, DOCX, max 5MB)
- Upload progress indicator
- Optional cover letter
- Form validation with Zod

---

## Pages

### 2. Application Submission Page
**Route:** `/jobs/[id]/apply`
**File:** `frontend/app/jobs/[id]/apply/page.tsx`

**Features:**
- Authentication check (job seeker only)
- Direct post validation
- Application form
- Success confirmation
- Error handling

**User Flow:**
1. User clicks "Apply Now" on job detail page
2. Redirected to application page
3. Fills out form (resume required, cover letter optional)
4. Submits application
5. Sees success message
6. Can navigate to "My Applications" or browse more jobs

**Error States:**
- Not authenticated → Login/Register prompt
- Not a job seeker → Role error
- Not a direct post → External link message
- Already applied → 409 error message
- Submission failed → Generic error message

---

### 3. My Applications Page
**Route:** `/applications`
**File:** `frontend/app/applications/page.tsx`

**Features:**
- List of all applications
- Status badges with colors
- Application details (job, company, location, date)
- Resume and cover letter links
- Summary statistics
- Empty state with CTA

**Status Colors:**
- SUBMITTED: Blue
- REVIEWED: Purple
- SHORTLISTED: Green
- REJECTED: Red
- ACCEPTED: Emerald

---

## API Integration

### Submit Application
```typescript
import { applicationsApi } from '@/lib/api/applications'

const response = await applicationsApi.submitApplication({
  job_id: 'uuid',
  resume: 'https://storage.example.com/resume.pdf',
  cover_letter: 'Optional cover letter text'
})
// Returns: { application_id: 'uuid', message: 'Success' }
```

### Get My Applications
```typescript
const data = await applicationsApi.getMyApplications()
// Returns: { applications: [...], total: number }
```

---

## File Upload Implementation

### Current (Placeholder)
```typescript
const resumeUrl = `https://storage.example.com/resumes/${userId}/${fileName}`
```

### Production Implementation
```typescript
// 1. Upload file to storage
const formData = new FormData()
formData.append('file', resumeFile)

const uploadResponse = await fetch('/api/upload', {
  method: 'POST',
  body: formData,
})
const { url } = await uploadResponse.json()

// 2. Submit application with URL
await applicationsApi.submitApplication({
  job_id: jobId,
  resume: url,
  cover_letter: coverLetter,
})
```

---

## Validation Rules

### Resume Upload
- **Required:** Yes
- **Max Size:** 5MB
- **Formats:** PDF, DOC, DOCX
- **MIME Types:**
  - `application/pdf`
  - `application/msword`
  - `application/vnd.openxmlformats-officedocument.wordprocessingml.document`

### Cover Letter
- **Required:** No
- **Type:** Text
- **Max Length:** No limit (but reasonable length recommended)

---

## Authentication & Authorization

### Required Role
- User must be logged in
- User role must be `job_seeker`
- Employers cannot apply to jobs

### Protected Routes
- `/jobs/[id]/apply` - Job seeker only
- `/applications` - Job seeker only

### Auth Check Pattern
```typescript
const { user, isAuthenticated } = useAuthStore()

if (!isAuthenticated || user?.role !== 'job_seeker') {
  // Show login/register prompt
  return <AuthPrompt />
}
```

---

## React Query Integration

### Query Keys
```typescript
// Get my applications
['my-applications']

// Get job details (for apply page)
['job', jobId]
```

### Mutations
```typescript
const submitMutation = useMutation({
  mutationFn: async (data) => {
    // Upload file and submit application
  },
  onSuccess: () => {
    // Show success message
  },
  onError: (error) => {
    // Handle error
  },
})
```

---

## Styling Guidelines

### Tailwind Classes
- Primary buttons: `bg-blue-600 hover:bg-blue-700`
- Secondary buttons: `bg-white border border-gray-300 hover:bg-gray-50`
- Success messages: `bg-green-50 border-green-200 text-green-700`
- Error messages: `bg-red-50 border-red-200 text-red-700`
- Warning messages: `bg-yellow-50 border-yellow-200 text-yellow-700`

### Responsive Breakpoints
- Mobile: Default (< 640px)
- Tablet: `sm:` (≥ 640px)
- Desktop: `lg:` (≥ 1024px)

---

## Common Patterns

### Loading State
```tsx
if (isLoading) {
  return (
    <div className="animate-pulse">
      <div className="h-8 bg-gray-200 rounded w-3/4 mb-4"></div>
      <div className="h-6 bg-gray-200 rounded w-1/2"></div>
    </div>
  )
}
```

### Error State
```tsx
if (isError) {
  return (
    <div className="bg-red-50 border border-red-200 rounded-lg p-8">
      <h2 className="text-red-800 font-medium mb-2">Error</h2>
      <p className="text-red-600">{error.message}</p>
    </div>
  )
}
```

### Empty State
```tsx
if (items.length === 0) {
  return (
    <div className="text-center p-12">
      <svg className="mx-auto h-16 w-16 text-gray-400 mb-4">...</svg>
      <h3 className="text-lg font-medium text-gray-900 mb-2">No Items</h3>
      <p className="text-gray-600 mb-6">Description</p>
      <button>Call to Action</button>
    </div>
  )
}
```

---

## Testing Checklist

### Unit Tests
- [ ] ApplicationForm validation
- [ ] File size validation
- [ ] File type validation
- [ ] Form submission
- [ ] Error handling

### Integration Tests
- [ ] Submit application flow
- [ ] View applications flow
- [ ] Authentication checks
- [ ] API error handling

### E2E Tests
- [ ] Complete application submission
- [ ] View submitted applications
- [ ] Status badge display
- [ ] Navigation flows

---

## Troubleshooting

### Issue: File upload fails
**Solution:** Check file size (< 5MB) and format (PDF, DOC, DOCX)

### Issue: "Already applied" error
**Solution:** User has already submitted an application for this job

### Issue: Cannot apply to job
**Solution:** Job must be a direct post (not aggregated from external sources)

### Issue: Not seeing applications
**Solution:** Ensure user is logged in as job seeker and has submitted applications

### Issue: TypeScript errors
**Solution:** Run `npm run build` to check for type errors

---

## Future Enhancements

1. **Real File Upload**
   - Integrate with AWS S3 or similar
   - Add file compression
   - Support multiple file formats

2. **Application Management**
   - Withdraw application
   - Edit before review
   - Application timeline

3. **Notifications**
   - Email on status change
   - Push notifications
   - In-app notifications

4. **Analytics**
   - Application views
   - Response rate
   - Time to response

5. **Enhanced Features**
   - Save draft applications
   - Application templates
   - Bulk apply
   - Cover letter AI assistance

---

## Related Documentation
- [API Client Guide](./API_CLIENT_GUIDE.md)
- [Authentication Guide](./AUTHENTICATION_IMPLEMENTATION_SUMMARY.md)
- [Task 28 Completion](./TASK_28_COMPLETION.md)
