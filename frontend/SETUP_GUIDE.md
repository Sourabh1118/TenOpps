# Frontend Setup Guide

This guide will help you set up and run the Job Aggregation Platform frontend.

## Prerequisites

- Node.js 18.x or higher
- npm 9.x or higher
- Backend API running (see backend/SETUP_GUIDE.md)

## Quick Start

### 1. Install Dependencies

```bash
cd frontend
npm install
```

### 2. Configure Environment Variables

Create a `.env.local` file from the example:

```bash
cp .env.local.example .env.local
```

Edit `.env.local` and update the values:

```env
# API Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_API_BASE_PATH=/api

# Authentication
NEXT_PUBLIC_JWT_SECRET=your-jwt-secret-key-here

# Feature Flags
NEXT_PUBLIC_ENABLE_ANALYTICS=false
NEXT_PUBLIC_ENABLE_FEATURED_JOBS=true

# Environment
NEXT_PUBLIC_ENV=development
```

### 3. Run Development Server

```bash
npm run dev
```

The application will be available at [http://localhost:3000](http://localhost:3000)

## Available Scripts

- `npm run dev` - Start development server with hot reload
- `npm run build` - Build for production
- `npm start` - Start production server (requires build first)
- `npm run lint` - Run ESLint to check code quality

## Project Structure

```
frontend/
├── app/              # Next.js App Router pages
├── components/       # Reusable React components
├── hooks/           # Custom React hooks
├── lib/             # Utilities and configurations
├── types/           # TypeScript type definitions
└── public/          # Static assets
```

See [PROJECT_STRUCTURE.md](./PROJECT_STRUCTURE.md) for detailed structure documentation.

## Key Technologies

### Next.js 14 (App Router)

- Server and client components
- File-based routing
- Built-in optimization
- API routes (if needed)

### TypeScript

- Type safety for all components and functions
- IntelliSense support
- Compile-time error checking

### Tailwind CSS

- Utility-first CSS framework
- Responsive design utilities
- Custom theme configuration

### React Query

- Server state management
- Automatic caching and refetching
- Optimistic updates
- Background synchronization

### Zustand

- Lightweight state management
- Minimal boilerplate
- TypeScript support
- Persistence middleware

### Axios

- HTTP client for API calls
- Request/response interceptors
- Automatic token refresh
- Error handling

## Development Workflow

### 1. Creating New Pages

Create a new directory in `app/` with a `page.tsx` file:

```typescript
// app/jobs/page.tsx
export default function JobsPage() {
  return <div>Jobs Page</div>
}
```

### 2. Creating Components

Create components in `components/` directory:

```typescript
// components/JobCard.tsx
interface JobCardProps {
  job: Job
}

export function JobCard({ job }: JobCardProps) {
  return (
    <div className="border rounded-lg p-4">
      <h3>{job.title}</h3>
      <p>{job.company}</p>
    </div>
  )
}
```

### 3. Using React Query

```typescript
'use client'

import { useQuery } from '@tanstack/react-query'
import apiClient from '@/lib/api-client'

export function JobsList() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['jobs'],
    queryFn: async () => {
      const response = await apiClient.get('/jobs')
      return response.data
    },
  })

  if (isLoading) return <div>Loading...</div>
  if (error) return <div>Error loading jobs</div>

  return (
    <div>
      {data.jobs.map(job => (
        <JobCard key={job.id} job={job} />
      ))}
    </div>
  )
}
```

### 4. Using Zustand Store

```typescript
'use client'

import { useAuthStore } from '@/lib/store'

export function UserProfile() {
  const { user, isAuthenticated } = useAuthStore()

  if (!isAuthenticated) {
    return <div>Please log in</div>
  }

  return <div>Welcome, {user?.email}</div>
}
```

## API Integration

The frontend communicates with the backend API through the configured Axios client.

### Making API Calls

```typescript
import apiClient from '@/lib/api-client'

// GET request
const response = await apiClient.get('/jobs')

// POST request
const response = await apiClient.post('/jobs/direct', jobData)

// PATCH request
const response = await apiClient.patch(`/jobs/${id}`, updates)

// DELETE request
const response = await apiClient.delete(`/jobs/${id}`)
```

### Authentication

The API client automatically:
- Attaches JWT tokens to requests
- Refreshes expired tokens
- Redirects to login on auth failure

## Styling Guidelines

### Using Tailwind CSS

```typescript
// Basic styling
<div className="bg-blue-600 text-white p-4 rounded-lg">
  Content
</div>

// Responsive design
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
  Content
</div>

// Conditional classes with cn() utility
import { cn } from '@/lib/utils'

<div className={cn(
  "base-classes",
  isActive && "active-classes",
  isDisabled && "disabled-classes"
)}>
  Content
</div>
```

## Common Issues

### Issue: API calls fail with CORS errors

**Solution**: Ensure the backend is configured to allow requests from `http://localhost:3000`

### Issue: Environment variables not working

**Solution**: 
- Ensure variables start with `NEXT_PUBLIC_` for client-side access
- Restart the development server after changing `.env.local`

### Issue: Build fails with TypeScript errors

**Solution**: 
- Run `npm run lint` to see all errors
- Fix type errors in components
- Ensure all imports are correct

### Issue: Styles not applying

**Solution**:
- Check Tailwind configuration in `tailwind.config.ts`
- Ensure `globals.css` is imported in `layout.tsx`
- Clear `.next` cache and rebuild

## Production Deployment

### Build for Production

```bash
npm run build
```

This creates an optimized production build in `.next/` directory.

### Environment Variables for Production

Set these environment variables in your hosting platform:

```env
NEXT_PUBLIC_API_URL=https://api.yourdomain.com
NEXT_PUBLIC_API_BASE_PATH=/api
NEXT_PUBLIC_JWT_SECRET=your-production-secret
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_live_your_key
NEXT_PUBLIC_ENV=production
```

### Deployment Platforms

#### Vercel (Recommended)

1. Connect your GitHub repository
2. Configure environment variables
3. Deploy automatically on push

#### Other Platforms

- Netlify
- AWS Amplify
- Railway
- Render

## Next Steps

1. **Implement Authentication Pages**
   - Login page (`app/login/page.tsx`)
   - Register page (`app/register/page.tsx`)
   - Password reset flow

2. **Create Job Pages**
   - Job listing page (`app/jobs/page.tsx`)
   - Job detail page (`app/jobs/[id]/page.tsx`)
   - Search and filter UI

3. **Build Employer Dashboard**
   - Dashboard overview (`app/employer/dashboard/page.tsx`)
   - Post job form (`app/employer/post-job/page.tsx`)
   - Manage applications

4. **Add Application Flow**
   - Application form
   - Application tracking
   - Status updates

5. **Implement Subscription Management**
   - Pricing page
   - Subscription upgrade flow
   - Payment integration with Stripe

## Support

For issues or questions:
- Check the [PROJECT_STRUCTURE.md](./PROJECT_STRUCTURE.md) documentation
- Review the backend API documentation
- Check Next.js documentation: https://nextjs.org/docs
- Check React Query documentation: https://tanstack.com/query/latest

## License

This project is part of the Job Aggregation Platform.
