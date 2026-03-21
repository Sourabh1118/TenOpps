'use client'

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { jobsApi } from "@/lib/api/jobs"
import { useRouter, useParams } from 'next/navigation'
import { ProtectedRoute } from '@/components/auth/ProtectedRoute'
import { JobPostingForm, JobFormData } from '@/components/employer/JobPostingForm'
import Link from 'next/link'

export default function EditJobPage() {
  return (
    <ProtectedRoute requiredRole="employer">
      <EditJobContent />
    </ProtectedRoute>
  )
}

function EditJobContent() {
  const router = useRouter()
  const params = useParams()
  const queryClient = useQueryClient()
  const jobId = params.id as string
  const [error, setError] = useState<string | null>(null)

  // Fetch job details
  const { data: job, isLoading } = useQuery({
    queryKey: ['job', jobId],
    queryFn: () => jobsApi.getJobById(jobId),
  })

  // Update job mutation
  const updateJobMutation = useMutation({
    mutationFn: async (data: JobFormData) => {
      // Convert form data to API format
      const apiData = {
        title: data.title,
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

      return jobsApi.updateJob(jobId, apiData)
    },
    onSuccess: () => {
      // Invalidate queries to refresh data
      queryClient.invalidateQueries({ queryKey: ['job', jobId] })
      queryClient.invalidateQueries({ queryKey: ['employer-jobs'] })

      // Redirect to job details page
      router.push(`/employer/jobs/${jobId}?updated=true`)
    },
    onError: (error: any) => {
      setError(error.response?.data?.detail || error.message || 'Failed to update job')
    },
  })

  const handleSubmit = async (data: JobFormData) => {
    setError(null)
    await updateJobMutation.mutateAsync(data)
  }

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 py-8 px-4 sm:px-6 lg:px-8">
        <div className="max-w-4xl mx-auto">
          <div className="h-8 bg-gray-200 rounded w-64 mb-8 animate-pulse"></div>
          <div className="bg-white shadow rounded-lg p-8">
            <div className="space-y-6">
              {[1, 2, 3, 4].map((i) => (
                <div key={i}>
                  <div className="h-4 bg-gray-200 rounded w-24 mb-2 animate-pulse"></div>
                  <div className="h-10 bg-gray-200 rounded animate-pulse"></div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    )
  }

  if (!job) {
    return (
      <div className="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-4xl mx-auto">
          <div className="bg-red-50 border border-red-200 rounded-lg p-8">
            <h2 className="text-red-800 font-medium mb-2">Job Not Found</h2>
            <p className="text-red-600">The job you're trying to edit could not be found.</p>
            <Link
              href="/employer/jobs"
              className="inline-block mt-4 text-red-800 hover:text-red-900 underline"
            >
              Back to My Jobs
            </Link>
          </div>
        </div>
      </div>
    )
  }

  // Prepare initial data for form
  const initialData: Partial<JobFormData> = {
    title: job.title,
    company: job.company,
    location: job.location,
    remote: job.remote,
    jobType: job.jobType,
    experienceLevel: job.experienceLevel,
    description: job.description,
    requirements: job.requirements || [],
    responsibilities: job.responsibilities || [],
    salaryMin: job.salaryMin,
    salaryMax: job.salaryMax,
    salaryCurrency: job.salaryCurrency || 'USD',
    tags: job.tags || [],
    expiresAt: job.expiresAt.split('T')[0],
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4 sm:px-6 lg:px-8">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <Link
            href={`/employer/jobs/${jobId}`}
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
            Back to Job Details
          </Link>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Edit Job</h1>
          <p className="text-gray-600">Update your job posting details</p>
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
                <h3 className="text-sm font-medium text-red-800">Error Updating Job</h3>
                <p className="text-sm text-red-700 mt-1">{error}</p>
              </div>
            </div>
          </div>
        )}

        {/* Form */}
        <div className="bg-white shadow rounded-lg p-6 md:p-8">
          <JobPostingForm
            initialData={initialData}
            onSubmit={handleSubmit}
            submitLabel="Update Job"
            isSubmitting={updateJobMutation.isPending}
          />
        </div>
      </div>
    </div>
  )
}
