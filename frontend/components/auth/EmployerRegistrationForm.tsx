'use client'

import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { employerRegistrationSchema, EmployerRegistrationFormData } from '@/lib/validations/auth'
import { authApi } from '@/lib/api/auth'
import { useAuthStore } from '@/lib/store'

export function EmployerRegistrationForm() {
  const router = useRouter()
  const setAuth = useAuthStore((state) => state.setAuth)
  const [error, setError] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<EmployerRegistrationFormData>({
    resolver: zodResolver(employerRegistrationSchema),
  })

  const onSubmit = async (data: EmployerRegistrationFormData) => {
    setIsLoading(true)
    setError(null)

    try {
      const response = await authApi.registerEmployer({
        email: data.email,
        password: data.password,
        company_name: data.companyName,
        company_website: data.companyWebsite || undefined,
        company_description: data.companyDescription || undefined,
      })

      // Store auth data
      setAuth(
        {
          id: response.user_id,
          email: data.email,
          role: response.role,
          createdAt: new Date().toISOString(),
        },
        {
          accessToken: response.access_token,
          refreshToken: response.refresh_token,
          tokenType: response.token_type,
        }
      )

      // Redirect to employer dashboard
      router.push('/employer/dashboard')
    } catch (err: unknown) {
      console.error('Registration error:', err)
      const error = err as { response?: { status?: number; data?: { detail?: string } } }
      if (error.response?.status === 409) {
        setError('Email already registered')
      } else if (error.response?.status === 400) {
        setError(error.response?.data?.detail || 'Invalid input. Please check your data.')
      } else {
        setError('An error occurred. Please try again.')
      }
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
          {error}
        </div>
      )}

      <div>
        <label htmlFor="email" className="block text-sm font-medium text-gray-700">
          Email
        </label>
        <input
          {...register('email')}
          type="email"
          id="email"
          className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
          placeholder="you@company.com"
        />
        {errors.email && (
          <p className="mt-1 text-sm text-red-600">{errors.email.message}</p>
        )}
      </div>

      <div>
        <label htmlFor="companyName" className="block text-sm font-medium text-gray-700">
          Company Name
        </label>
        <input
          {...register('companyName')}
          type="text"
          id="companyName"
          className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
          placeholder="Tech Corp"
        />
        {errors.companyName && (
          <p className="mt-1 text-sm text-red-600">{errors.companyName.message}</p>
        )}
      </div>

      <div>
        <label htmlFor="companyWebsite" className="block text-sm font-medium text-gray-700">
          Company Website (optional)
        </label>
        <input
          {...register('companyWebsite')}
          type="url"
          id="companyWebsite"
          className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
          placeholder="https://company.com"
        />
        {errors.companyWebsite && (
          <p className="mt-1 text-sm text-red-600">{errors.companyWebsite.message}</p>
        )}
      </div>

      <div>
        <label htmlFor="companyDescription" className="block text-sm font-medium text-gray-700">
          Company Description (optional)
        </label>
        <textarea
          {...register('companyDescription')}
          id="companyDescription"
          rows={3}
          className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
          placeholder="Tell us about your company..."
        />
        {errors.companyDescription && (
          <p className="mt-1 text-sm text-red-600">{errors.companyDescription.message}</p>
        )}
      </div>

      <div>
        <label htmlFor="password" className="block text-sm font-medium text-gray-700">
          Password
        </label>
        <input
          {...register('password')}
          type="password"
          id="password"
          className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
          placeholder="••••••••"
        />
        {errors.password && (
          <p className="mt-1 text-sm text-red-600">{errors.password.message}</p>
        )}
        <p className="mt-1 text-xs text-gray-500">
          Must be at least 8 characters with uppercase, lowercase, number, and special character
        </p>
      </div>

      <div>
        <label htmlFor="confirmPassword" className="block text-sm font-medium text-gray-700">
          Confirm Password
        </label>
        <input
          {...register('confirmPassword')}
          type="password"
          id="confirmPassword"
          className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
          placeholder="••••••••"
        />
        {errors.confirmPassword && (
          <p className="mt-1 text-sm text-red-600">{errors.confirmPassword.message}</p>
        )}
      </div>

      <button
        type="submit"
        disabled={isLoading}
        className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {isLoading ? 'Creating account...' : 'Create account'}
      </button>

      <div className="text-sm text-center">
        <p className="text-gray-600">
          Already have an account?{' '}
          <Link href="/login" className="text-blue-600 hover:text-blue-500">
            Sign in
          </Link>
        </p>
      </div>
    </form>
  )
}
