import { Metadata } from 'next'
import { JobSeekerRegistrationForm } from '@/components/auth/JobSeekerRegistrationForm'

export const metadata: Metadata = {
  title: 'Register as Job Seeker | Job Aggregation Platform',
  description: 'Create your job seeker account',
}

export default function JobSeekerRegistrationPage() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
            Create your job seeker account
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            Start your journey to find your dream job
          </p>
        </div>
        <div className="mt-8 bg-white py-8 px-4 shadow sm:rounded-lg sm:px-10">
          <JobSeekerRegistrationForm />
        </div>
      </div>
    </div>
  )
}
