import { Metadata } from 'next'
import { EmployerRegistrationForm } from '@/components/auth/EmployerRegistrationForm'

export const metadata: Metadata = {
  title: 'Register as Employer | Job Aggregation Platform',
  description: 'Create your employer account',
}

export default function EmployerRegistrationPage() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
            Create your employer account
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            Post jobs and find the best talent
          </p>
        </div>
        <div className="mt-8 bg-white py-8 px-4 shadow sm:rounded-lg sm:px-10">
          <EmployerRegistrationForm />
        </div>
      </div>
    </div>
  )
}
