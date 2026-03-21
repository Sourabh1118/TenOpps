# Quick Start: Layout Components

## TL;DR

```tsx
// Public page
import { MainLayout } from '@/components/layout'

export default function Page() {
  return (
    <MainLayout>
      <div className="container mx-auto px-4 py-8">
        <h1>Your Content</h1>
      </div>
    </MainLayout>
  )
}

// Protected page
import { ProtectedRoute } from '@/components/auth'
import { MainLayout } from '@/components/layout'

export default function Page() {
  return (
    <ProtectedRoute requiredRole="employer">
      <MainLayout>
        <div className="container mx-auto px-4 py-8">
          <h1>Employer Only</h1>
        </div>
      </MainLayout>
    </ProtectedRoute>
  )
}

// Use auth state
'use client'
import { useAuthStore } from '@/lib/store'

export function Component() {
  const { isAuthenticated, user, setAuth, clearAuth } = useAuthStore()
  // ...
}
```

## Components

| Component | Purpose | Import |
|-----------|---------|--------|
| `MainLayout` | Page wrapper with header/footer | `@/components/layout` |
| `Header` | Navigation bar (auto-included in MainLayout) | `@/components/layout` |
| `Footer` | Site footer (auto-included in MainLayout) | `@/components/layout` |
| `ProtectedRoute` | Restrict access to authenticated users | `@/components/auth` |

## Auth Store

```tsx
const { 
  isAuthenticated,  // boolean
  user,             // User | null
  tokens,           // AuthTokens | null
  setAuth,          // (user, tokens) => void
  clearAuth         // () => void
} = useAuthStore()
```

## Protected Routes

```tsx
// Any authenticated user
<ProtectedRoute>
  <Content />
</ProtectedRoute>

// Employer only
<ProtectedRoute requiredRole="employer">
  <Content />
</ProtectedRoute>

// Job seeker only
<ProtectedRoute requiredRole="job_seeker">
  <Content />
</ProtectedRoute>

// Custom redirect
<ProtectedRoute redirectTo="/custom-login">
  <Content />
</ProtectedRoute>
```

## Navigation Items

**Public:** Home, Search Jobs, Login, Sign Up

**Employer:** Home, Search Jobs, Post Job, Dashboard, Logout

**Job Seeker:** Home, Search Jobs, My Applications, Logout

## Responsive

- **Mobile:** < 768px (hamburger menu)
- **Desktop:** >= 768px (full navigation)

## Styling

- **Theme:** Blue (blue-600, blue-700, blue-800)
- **Font:** Geist Sans
- **Framework:** Tailwind CSS

## Files

```
frontend/
├── components/
│   ├── auth/
│   │   ├── ProtectedRoute.tsx
│   │   └── index.ts
│   └── layout/
│       ├── Header.tsx
│       ├── Footer.tsx
│       ├── MainLayout.tsx
│       └── index.ts
└── lib/
    └── store.ts
```

## Full Documentation

See `LAYOUT_COMPONENTS_GUIDE.md` for complete documentation.
