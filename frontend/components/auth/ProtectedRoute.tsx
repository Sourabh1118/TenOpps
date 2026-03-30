'use client'

import { useEffect, ReactNode } from 'react'
import { useRouter } from 'next/navigation'
import { useAuthStore } from '@/lib/store'

interface ProtectedRouteProps {
  children: ReactNode
  requiredRole?: 'employer' | 'job_seeker' | 'admin'
  redirectTo?: string
}

export function ProtectedRoute({ 
  children, 
  requiredRole,
  redirectTo = '/login' 
}: ProtectedRouteProps) {
  const router = useRouter()
  const { isAuthenticated, user, _hasHydrated } = useAuthStore()

  useEffect(() => {
    // Wait for hydration before checking auth
    if (!_hasHydrated) return

    // Check if user is authenticated
    if (!isAuthenticated) {
      router.push(redirectTo)
      return
    }

    // Check if user has required role
    if (requiredRole && user?.role !== requiredRole) {
      // Redirect to appropriate page based on user role
      if (user?.role === 'employer') {
        router.push('/employer/dashboard')
      } else if (user?.role === 'job_seeker') {
        router.push('/jobs')
      } else {
        router.push('/')
      }
    }
  }, [isAuthenticated, user, requiredRole, redirectTo, router, _hasHydrated])

  // Don't render children if not hydrated, not authenticated, or wrong role
  if (!_hasHydrated || !isAuthenticated) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">{!_hasHydrated ? 'Loading session...' : 'Redirecting to login...'}</p>
        </div>
      </div>
    )
  }

  if (requiredRole && user?.role !== requiredRole) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Redirecting...</p>
        </div>
      </div>
    )
  }

  return <>{children}</>
}
