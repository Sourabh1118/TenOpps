'use client'

import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { loginSchema, LoginFormData } from '@/lib/validations/auth'
import { authApi } from '@/lib/api/auth'
import { useAuthStore } from '@/lib/store'

export function LoginForm() {
  const router = useRouter()
  const setAuth = useAuthStore((state) => state.setAuth)
  const [error, setError] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
  })

  const onSubmit = async (data: LoginFormData) => {
    setIsLoading(true)
    setError(null)

    try {
      const response = await authApi.login(data)
      
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

      // Redirect based on role
      if (response.role === 'employer') {
        router.push('/employer/dashboard')
      } else {
        router.push('/jobs')
      }
    } catch (err: unknown) {
      console.error('Login error:', err)
      const error = err as { response?: { status?: number; data?: { detail?: string } } }
      if (error.response?.status === 401) {
        setError('Invalid email or password')
      } else if (error.response?.status === 429) {
        setError('Too many login attempts. Please try again later.')
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
          placeholder="you@example.com"
        />
        {errors.email && (
          <p className="mt-1 text-sm text-red-600">{errors.email.message}</p>
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
      </div>

      <button
        type="submit"
        disabled={isLoading}
        className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {isLoading ? 'Signing in...' : 'Sign in'}
      </button>

      <div className="text-sm text-center space-y-2">
        <p className="text-gray-600">
          Don&apos;t have an account?{' '}
          <Link href="/register/job-seeker" className="text-blue-600 hover:text-blue-500">
            Register as Job Seeker
          </Link>
          {' or '}
          <Link href="/register/employer" className="text-blue-600 hover:text-blue-500">
            Register as Employer
          </Link>
        </p>
      </div>
    </form>
  )
}
