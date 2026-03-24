import { Metadata } from 'next'
import Link from 'next/link'

export const metadata: Metadata = {
  title: 'Register | Job Aggregation Platform',
  description: 'Create your account',
}

export default function RegisterPage() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
            Create your account
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            Choose your account type to get started
          </p>
        </div>
        
        <div className="mt-8 space-y-4">
          <Link
            href="/register/job-seeker"
            className="w-full flex flex-col items-center justify-center px-8 py-6 border-2 border-gray-300 rounded-lg shadow-sm hover:border-blue-500 hover:shadow-md transition-all bg-white"
          >
            <svg className="w-12 h-12 text-blue-600 mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
            </svg>
            <h3 className="text-xl font-semibold text-gray-900">Job Seeker</h3>
            <p className="mt-2 text-sm text-gray-600 text-center">
              Find your next opportunity
            </p>
          </Link>

          <Link
            href="/register/employer"
            className="w-full flex flex-col items-center justify-center px-8 py-6 border-2 border-gray-300 rounded-lg shadow-sm hover:border-blue-500 hover:shadow-md transition-all bg-white"
          >
            <svg className="w-12 h-12 text-blue-600 mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
            </svg>
            <h3 className="text-xl font-semibold text-gray-900">Employer</h3>
            <p className="mt-2 text-sm text-gray-600 text-center">
              Post jobs and find talent
            </p>
          </Link>
        </div>

        <div className="text-center">
          <p className="text-sm text-gray-600">
            Already have an account?{' '}
            <Link href="/login" className="text-blue-600 hover:text-blue-500 font-medium">
              Sign in
            </Link>
          </p>
        </div>
      </div>
    </div>
  )
}
