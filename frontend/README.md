# Job Aggregation Platform - Frontend

This is the frontend application for the Job Aggregation Platform, built with Next.js 14, TypeScript, and Tailwind CSS.

## Tech Stack

- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **State Management**: Zustand
- **Data Fetching**: React Query (@tanstack/react-query)
- **HTTP Client**: Axios
- **Form Handling**: React Hook Form
- **Validation**: Zod

## Project Structure

```
frontend/
├── app/                    # Next.js App Router pages
│   ├── layout.tsx         # Root layout with providers
│   ├── page.tsx           # Home page
│   └── providers.tsx      # React Query provider
├── components/            # Reusable React components
│   └── layout/           # Layout components (Header, Footer)
├── hooks/                # Custom React hooks
├── lib/                  # Utility functions and configurations
│   ├── api-client.ts    # Axios instance with interceptors
│   ├── react-query.ts   # React Query configuration
│   ├── store.ts         # Zustand store for global state
│   └── utils.ts         # Utility functions
├── types/               # TypeScript type definitions
│   └── index.ts        # Core types (Job, Employer, Application, etc.)
└── public/             # Static assets

```

## Getting Started

### Prerequisites

- Node.js 18+ and npm

### Installation

1. Install dependencies:
```bash
npm install
```

2. Create environment file:
```bash
cp .env.local.example .env.local
```

3. Update `.env.local` with your API endpoint:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Development

Run the development server:

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

### Build

Build for production:

```bash
npm run build
```

Start production server:

```bash
npm start
```

## Environment Variables

- `NEXT_PUBLIC_API_URL`: Backend API URL (default: http://localhost:8000)
- `NEXT_PUBLIC_API_BASE_PATH`: API base path (default: /api)
- `NEXT_PUBLIC_JWT_SECRET`: JWT secret for token validation
- `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY`: Stripe publishable key for payments

## Features

### For Job Seekers
- Browse and search jobs from multiple sources
- Advanced filtering (location, job type, salary, etc.)
- Apply to direct job postings
- Track application status

### For Employers
- Post jobs directly on the platform
- Import jobs from external URLs
- Manage applications
- Subscription management (Free, Basic, Premium)
- Feature job listings

## API Integration

The frontend communicates with the FastAPI backend through the configured API client (`lib/api-client.ts`). The client includes:

- Automatic JWT token attachment
- Token refresh on 401 errors
- Request/response interceptors
- Error handling

## State Management

- **Zustand**: Used for global authentication state
- **React Query**: Used for server state management (data fetching, caching, mutations)

## Styling

The project uses Tailwind CSS for styling. Configuration can be found in `tailwind.config.ts`.

## Type Safety

All API responses and data structures are typed using TypeScript interfaces defined in `types/index.ts`.

## Next Steps

1. Implement authentication pages (login, register)
2. Create job listing and detail pages
3. Build employer dashboard
4. Add application submission flow
5. Implement search and filtering UI
6. Add subscription management UI

## License

This project is part of the Job Aggregation Platform.
