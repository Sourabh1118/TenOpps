'use client'

import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { jobsApi } from '@/lib/api/jobs'
import { useRouter } from 'next/navigation'
import { ProtectedRoute } from '@/components/auth/ProtectedRoute'
import { JobPostingForm, JobFormData } from '@/components/employer/JobPostingForm'
import Link from 'next/link'

export default function PostJobPage() {
  return (
    <ProtectedRoute requiredRole="employer">
      <PostJobContent />
    </ProtectedRoute>
  )
}

function PostJobContent() {
  const router = useRouter()
  const queryClient = useQueryClient()
  const [error, setError] = useState<string | null>(null)

  const createJobMutation = useMutation({
    mutationFn: async (data: JobFormData) => {
      // Convert form data to API format
      const apiData = {
        title: data.title,
        company: data.company,
        location: data.location,
        remote: data.remote,
        job_type: data.jobType,
        experience_level: data.experienceLevel,
        description: data.description,
        requirements: data.requirements.length > 0 ? data.requirements : undefined,
        responsibilities: data.responsibilities.length > 0 ? data.responsibilities : undefined,
        salary_min: data.salaryMin,
        salary_max: data.salaryMax,
        salary_currency: data.salaryCurrency,
        tags: data.tags.length > 0 ? data.tags : undefined,
        expires_at: new Date(data.expiresAt).toISOString(),
      }

      return jobsApi.createDirectJob(apiData)
    },
    onSuccess: (response) => {
      // Invalidate queries to refresh data
      queryClient.invalidateQueries({ queryKey: ['employer-jobs'] })
      queryClient.invalidateQueries({ queryKey: ['subscription-info'] })

      // Redirect to job details page
      router.push(`/employer/jobs/${response.job_id}?posted=true`)
    },
    onError: (error: any) => {
      if (error.response?.status === 403) {
        setError('You have exceeded your monthly posting quota. Please upgrade your subscription.')
      } else {
        setError(error.response?.data?.detail || error.message || 'Failed to create job posting')
      }
    },
  })

  const handleSubmit = async (data: JobFormData) => {
    setError(null)
    await createJobMutation.mutateAsync(data)
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4 sm:px-6 lg:px-8">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <Link
            href="/employer/dashboard"
            className="inline-flex items-center text-sm text-gray-600 hover:text-gray-900 mb-4"
          >
            <svg
              className="w-4 h-4 mr-1"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M15 19l-7-7 7-7"
              />
            </svg>
            Back to Dashboard
          </Link>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Post a New Job</h1>
          <p className="text-gray-600">
            Fill out the form below to create a new job posting
          </p>
        </div>

        {/* Error Message */}
        {error && (
          <div className="mb-6 bg-red-50 border border-red-200 rounded-lg p-4">
            <div className="flex items-start">
              <svg
                className="w-5 h-5 text-red-600 mt-0.5 mr-3"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
              <div className="flex-1">
                <h3 className="text-sm font-medium text-red-800">Error Creating Job</h3>
                <p className="text-sm text-red-700 mt-1">{error}</p>
                {error.includes('quota') && (
                  <Link
                    href="/employer/subscription"
                    className="inline-block mt-2 text-sm font-medium text-red-800 hover:text-red-900 underline"
                  >
                    Upgrade Subscription →
                  </Link>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Form */}
        <div className="bg-white shadow rounded-lg p-6 md:p-8">
          <JobPostingForm
            onSubmit={handleSubmit}
            submitLabel="Post Job"
            isSubmitting={createJobMutation.isPending}
          />
        </div>

        {/* Help Text */}
        <div className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
          <h3 className="text-sm font-medium text-blue-900 mb-2">Tips for a Great Job Posting</h3>
          <ul className="text-sm text-blue-800 space-y-1 list-disc list-inside">
            <li>Use a clear, descriptive job title</li>
            <li>Provide detailed requirements and responsibilities</li>
            <li>Include salary range to attract qualified candidates</li>
            <li>Add relevant tags to improve discoverability</li>
            <li>Proofread your posting before submitting</li>
          </ul>
        </div>
      </div>
    </div>
  )
}
