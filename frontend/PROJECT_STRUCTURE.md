# Frontend Project Structure

## Overview

This document describes the structure and organization of the Job Aggregation Platform frontend application.

## Directory Structure

```
frontend/
├── app/                          # Next.js 14 App Router
│   ├── fonts/                   # Custom fonts (Geist Sans, Geist Mono)
│   ├── favicon.ico              # Site favicon
│   ├── globals.css              # Global styles and Tailwind directives
│   ├── layout.tsx               # Root layout with metadata and providers
│   ├── page.tsx                 # Home page
│   └── providers.tsx            # Client-side providers (React Query)
│
├── components/                   # Reusable React components
│   └── layout/                  # Layout components
│       ├── Header.tsx           # Site header with navigation
│       └── Footer.tsx           # Site footer
│
├── hooks/                       # Custom React hooks
│   └── .gitkeep                # Placeholder for future hooks
│
├── lib/                         # Utility functions and configurations
│   ├── api-client.ts           # Axios instance with auth interceptors
│   ├── react-query.ts          # React Query client configuration
│   ├── store.ts                # Zustand store for auth state
│   └── utils.ts                # Utility functions (formatting, etc.)
│
├── types/                       # TypeScript type definitions
│   ├── index.ts                # Core types (Job, Employer, Application, etc.)
│   └── .gitkeep                # Placeholder
│
├── public/                      # Static assets
│
├── .env.local.example          # Environment variables template
├── .eslintrc.json              # ESLint configuration
├── .gitignore                  # Git ignore rules
├── next.config.mjs             # Next.js configuration
├── next-env.d.ts               # Next.js TypeScript declarations
├── package.json                # Dependencies and scripts
├── postcss.config.mjs          # PostCSS configuration
├── PROJECT_STRUCTURE.md        # This file
├── README.md                   # Project documentation
├── tailwind.config.ts          # Tailwind CSS configuration
└── tsconfig.json               # TypeScript configuration
```

## Key Files

### Configuration Files

- **next.config.mjs**: Next.js configuration (experimental features, etc.)
- **tailwind.config.ts**: Tailwind CSS theme and plugin configuration
- **tsconfig.json**: TypeScript compiler options and path aliases
- **.env.local.example**: Template for environment variables

### Core Application Files

- **app/layout.tsx**: Root layout that wraps all pages
- **app/providers.tsx**: Client-side providers (React Query)
- **app/page.tsx**: Home page component
- **app/globals.css**: Global styles and Tailwind directives

### Library Files

- **lib/api-client.ts**: Configured Axios instance with:
  - Automatic JWT token attachment
  - Token refresh on 401 errors
  - Request/response interceptors
  
- **lib/react-query.ts**: React Query client with:
  - 5-minute stale time
  - 10-minute garbage collection time
  - Retry configuration
  
- **lib/store.ts**: Zustand store for:
  - Authentication state
  - User information
  - Token management
  
- **lib/utils.ts**: Utility functions for:
  - Class name merging (cn)
  - Salary formatting
  - Date formatting
  - Relative time formatting

### Type Definitions

- **types/index.ts**: Core TypeScript interfaces including:
  - Job, Employer, Application models
  - Enums (JobType, ExperienceLevel, SourceType, etc.)
  - API request/response types
  - Search filters and pagination types

## Component Organization

### Layout Components

Located in `components/layout/`:

- **Header.tsx**: Site header with:
  - Logo and navigation
  - Authentication state-aware menu
  - Role-based navigation (employer vs job seeker)
  
- **Footer.tsx**: Site footer with:
  - Company information
  - Navigation links
  - Copyright notice

## State Management

### Global State (Zustand)

- **Auth State**: User authentication, tokens, login/logout
- Persisted to localStorage
- Accessed via `useAuthStore` hook

### Server State (React Query)

- API data fetching and caching
- Automatic background refetching
- Optimistic updates for mutations
- Accessed via `useQuery` and `useMutation` hooks

## Styling

### Tailwind CSS

- Utility-first CSS framework
- Custom theme configuration in `tailwind.config.ts`
- Global styles in `app/globals.css`
- Component-specific styles using Tailwind classes

### Fonts

- **Geist Sans**: Primary font for body text
- **Geist Mono**: Monospace font for code

## API Integration

### Axios Client

The API client (`lib/api-client.ts`) handles:

1. **Base Configuration**
   - Base URL from environment variables
   - 30-second timeout
   - JSON content type

2. **Request Interceptor**
   - Attaches JWT token from localStorage
   - Adds Authorization header

3. **Response Interceptor**
   - Handles 401 errors (token expiration)
   - Attempts token refresh
   - Retries failed requests with new token
   - Redirects to login on refresh failure

## Environment Variables

Required environment variables (see `.env.local.example`):

- `NEXT_PUBLIC_API_URL`: Backend API URL
- `NEXT_PUBLIC_API_BASE_PATH`: API base path (default: /api)
- `NEXT_PUBLIC_JWT_SECRET`: JWT secret for validation
- `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY`: Stripe key for payments
- `NEXT_PUBLIC_ENV`: Environment (development/production)

## Future Structure

As the application grows, additional directories will be added:

```
app/
├── (auth)/                      # Auth pages (login, register)
├── jobs/                        # Job listing and detail pages
├── employer/                    # Employer dashboard pages
├── applications/                # Application tracking pages
└── api/                         # API routes (if needed)

components/
├── ui/                          # UI components (buttons, inputs, etc.)
├── forms/                       # Form components
├── job/                         # Job-related components
└── employer/                    # Employer-specific components

hooks/
├── useAuth.ts                   # Authentication hook
├── useJobs.ts                   # Job fetching hooks
└── useApplications.ts           # Application hooks
```

## Development Workflow

1. **Start Development Server**: `npm run dev`
2. **Build for Production**: `npm run build`
3. **Start Production Server**: `npm start`
4. **Lint Code**: `npm run lint`

## Best Practices

1. **Component Organization**
   - Keep components small and focused
   - Use composition over inheritance
   - Extract reusable logic into custom hooks

2. **Type Safety**
   - Define types for all API responses
   - Use TypeScript strict mode
   - Avoid `any` types

3. **State Management**
   - Use Zustand for global UI state
   - Use React Query for server state
   - Keep component state local when possible

4. **Styling**
   - Use Tailwind utility classes
   - Extract repeated patterns into components
   - Use the `cn()` utility for conditional classes

5. **API Calls**
   - Always use the configured API client
   - Handle loading and error states
   - Use React Query for caching and refetching
