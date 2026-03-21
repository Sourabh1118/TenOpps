# Layout and Navigation Components Guide

This guide explains how to use the layout and navigation components created for the Job Aggregation Platform.

## Components Overview

### 1. MainLayout Component

The `MainLayout` component provides a consistent page structure with header, main content area, and footer.

**Location:** `frontend/components/layout/MainLayout.tsx`

**Usage:**
```tsx
import { MainLayout } from '@/components/layout'

export default function MyPage() {
  return (
    <MainLayout>
      <h1>Page Content</h1>
      <p>Your page content goes here</p>
    </MainLayout>
  )
}
```

**Features:**
- Automatically includes Header and Footer
- Ensures consistent layout across all pages
- Handles flex layout for sticky footer

### 2. Header Component

The `Header` component provides navigation with authentication state management.

**Location:** `frontend/components/layout/Header.tsx`

**Features:**
- **Responsive Design:** Mobile hamburger menu for small screens, full navigation for desktop
- **Authentication Aware:** Shows different navigation based on login state
- **Role-Based Navigation:** Different menu items for employers vs job seekers
- **Sticky Header:** Stays at top of page while scrolling
- **Mobile Menu:** Collapsible navigation for mobile devices

**Navigation Items:**
- **Public:** Home, Search Jobs, Login, Sign Up
- **Employer:** Home, Search Jobs, Post Job, Dashboard, Logout
- **Job Seeker:** Home, Search Jobs, My Applications, Logout

### 3. Footer Component

The `Footer` component provides site-wide links and information.

**Location:** `frontend/components/layout/Footer.tsx`

**Features:**
- Four-column layout on desktop, single column on mobile
- Links for job seekers, employers, and company information
- Copyright notice with dynamic year

### 4. ProtectedRoute Component

The `ProtectedRoute` component restricts access to authenticated users and specific roles.

**Location:** `frontend/components/auth/ProtectedRoute.tsx`

**Usage:**

**Basic Protection (any authenticated user):**
```tsx
import { ProtectedRoute } from '@/components/auth'

export default function DashboardPage() {
  return (
    <ProtectedRoute>
      <MainLayout>
        <h1>Dashboard</h1>
        <p>Only authenticated users can see this</p>
      </MainLayout>
    </ProtectedRoute>
  )
}
```

**Role-Based Protection (employer only):**
```tsx
import { ProtectedRoute } from '@/components/auth'

export default function PostJobPage() {
  return (
    <ProtectedRoute requiredRole="employer">
      <MainLayout>
        <h1>Post a Job</h1>
        <p>Only employers can see this</p>
      </MainLayout>
    </ProtectedRoute>
  )
}
```

**Custom Redirect:**
```tsx
<ProtectedRoute redirectTo="/custom-login">
  <YourContent />
</ProtectedRoute>
```

**Props:**
- `children`: React nodes to render if authorized
- `requiredRole?`: Optional role requirement ('employer' | 'job_seeker' | 'admin')
- `redirectTo?`: Custom redirect path (default: '/login')

**Behavior:**
- Redirects unauthenticated users to login page
- Redirects users with wrong role to their appropriate dashboard
- Shows loading spinner during redirect
- Automatically checks authentication state on mount

## Authentication State Management

The components use Zustand for authentication state management.

**Store Location:** `frontend/lib/store.ts`

**Available State:**
```typescript
interface AuthState {
  user: User | null
  tokens: AuthTokens | null
  isAuthenticated: boolean
  setAuth: (user: User, tokens: AuthTokens) => void
  clearAuth: () => void
}
```

**Usage in Components:**
```tsx
'use client'

import { useAuthStore } from '@/lib/store'

export function MyComponent() {
  const { isAuthenticated, user, setAuth, clearAuth } = useAuthStore()
  
  // Use authentication state
  if (isAuthenticated) {
    return <p>Welcome, {user?.email}</p>
  }
  
  return <p>Please log in</p>
}
```

**Login Example:**
```tsx
import { useAuthStore } from '@/lib/store'
import { apiClient } from '@/lib/api-client'

async function handleLogin(email: string, password: string) {
  const { setAuth } = useAuthStore.getState()
  
  const response = await apiClient.post('/auth/login', { email, password })
  const { user, tokens } = response.data
  
  setAuth(user, tokens)
}
```

**Logout Example:**
```tsx
import { useAuthStore } from '@/lib/store'

function LogoutButton() {
  const { clearAuth } = useAuthStore()
  
  return (
    <button onClick={clearAuth}>
      Logout
    </button>
  )
}
```

## Page Examples

### Public Page
```tsx
// app/about/page.tsx
import { MainLayout } from '@/components/layout'

export default function AboutPage() {
  return (
    <MainLayout>
      <div className="container mx-auto px-4 py-8">
        <h1 className="text-3xl font-bold mb-4">About Us</h1>
        <p>This page is accessible to everyone</p>
      </div>
    </MainLayout>
  )
}
```

### Protected Page (Any Authenticated User)
```tsx
// app/profile/page.tsx
import { ProtectedRoute } from '@/components/auth'
import { MainLayout } from '@/components/layout'

export default function ProfilePage() {
  return (
    <ProtectedRoute>
      <MainLayout>
        <div className="container mx-auto px-4 py-8">
          <h1 className="text-3xl font-bold mb-4">My Profile</h1>
          <p>Only authenticated users can see this</p>
        </div>
      </MainLayout>
    </ProtectedRoute>
  )
}
```

### Employer-Only Page
```tsx
// app/employer/dashboard/page.tsx
import { ProtectedRoute } from '@/components/auth'
import { MainLayout } from '@/components/layout'

export default function EmployerDashboard() {
  return (
    <ProtectedRoute requiredRole="employer">
      <MainLayout>
        <div className="container mx-auto px-4 py-8">
          <h1 className="text-3xl font-bold mb-4">Employer Dashboard</h1>
          <p>Only employers can see this</p>
        </div>
      </MainLayout>
    </ProtectedRoute>
  )
}
```

### Job Seeker-Only Page
```tsx
// app/applications/page.tsx
import { ProtectedRoute } from '@/components/auth'
import { MainLayout } from '@/components/layout'

export default function ApplicationsPage() {
  return (
    <ProtectedRoute requiredRole="job_seeker">
      <MainLayout>
        <div className="container mx-auto px-4 py-8">
          <h1 className="text-3xl font-bold mb-4">My Applications</h1>
          <p>Only job seekers can see this</p>
        </div>
      </MainLayout>
    </ProtectedRoute>
  )
}
```

## Responsive Design

All components are fully responsive:

### Breakpoints (Tailwind CSS)
- **Mobile:** < 768px (md breakpoint)
- **Desktop:** >= 768px

### Header Behavior
- **Mobile:** Hamburger menu icon, collapsible navigation
- **Desktop:** Full horizontal navigation bar

### Footer Behavior
- **Mobile:** Single column layout
- **Desktop:** Four-column grid layout

## Styling

Components use Tailwind CSS for styling:

- **Colors:** Blue theme (blue-600, blue-700, blue-800)
- **Spacing:** Consistent padding and margins
- **Typography:** Geist Sans font family
- **Transitions:** Smooth hover effects on interactive elements

## Testing the Components

1. **Test Authentication Flow:**
   - Visit a protected page while logged out → should redirect to login
   - Log in and visit protected page → should show content
   - Log out → should redirect to login

2. **Test Role-Based Access:**
   - Log in as employer → should see employer navigation
   - Try to access job seeker page → should redirect to employer dashboard
   - Log in as job seeker → should see job seeker navigation

3. **Test Responsive Design:**
   - Resize browser to mobile width → should show hamburger menu
   - Click hamburger → should show mobile navigation
   - Click link → should close mobile menu
   - Resize to desktop → should show full navigation

## Next Steps

With these foundational components in place, you can now:

1. Create authentication pages (login, register)
2. Build job search and listing pages
3. Implement employer dashboard
4. Add job seeker application tracking
5. Create job posting forms

All pages should use `MainLayout` for consistency and `ProtectedRoute` where authentication is required.
