'use client'

import { useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { useQuery, useMutation } from '@tanstack/react-query'
import { jobsApi } from '@/lib/api/jobs'
import { applicationsApi } from '@/lib/api/applications'
import { ApplicationForm } from '@/components/applications/ApplicationForm'
import { useAuthStore } from '@/lib/store'
import Link from 'next/link'

export default function ApplyPage() {
  const params = useParams()
  const router = useRouter()
  const jobId = params.id as string
  const { user, isAuthenticated } = useAuthStore()
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)

  // Fetch job details
  const { data: job, isLoading, isError } = useQuery({
    queryKey: ['job', jobId],
    queryFn: () => jobsApi.getJobById(jobId),
  })

  // Submit application mutation
  const submitMutation = useMutation({
    mutationFn: async (data: { resume: File; coverLetter?: string }) => {
      // In a real app, you would upload the file to storage first
      // For now, we'll simulate this with a placeholder URL
      const resumeUrl = `https://storage.example.com/resumes/${user?.id}/${data.resume.name}`
      
      return applicationsApi.submitApplication({
        job_id: jobId,
        resume: resumeUrl,
        cover_letter: data.coverLetter,
      })
    },
    onSuccess: () => {
      setSuccess(true)
      setError(null)
    },
    onError: (err: any) => {
      console.error('Application submission error:', err)
      if (err.response?.status === 409) {
        setError('You have already applied to this job.')
      } else if (err.response?.status === 400) {
        setError(err.response?.data?.detail || 'This job is not accepting applications.')
      } else {
        setError('Failed to submit application. Please try again.')
      }
    },
  })

  // Check authentication
  if (!isAuthenticated || user?.role !== 'job_seeker') {
    return (
      <div className="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-2xl mx-auto">
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-8 text-center">
            <svg
              className="mx-auto h-12 w-12 text-yellow-600 mb-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
              />
            </svg>
            <h2 className="text-xl font-semibold text-gray-900 mb-2">
              Job Seeker Account Required
            </h2>
            <p className="text-gray-600 mb-6">
              You need to be logged in as a job seeker to apply for jobs.
            </p>
            <div className="flex gap-3 justify-center">
              <Link
                href="/login"
                className="px-6 py-2 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700"
              >
                Log In
              </Link>
              <Link
                href="/register/job-seeker"
                className="px-6 py-2 bg-white text-gray-700 font-medium rounded-lg border border-gray-300 hover:bg-gray-50"
              >
                Register
              </Link>
            </div>
          </div>
        </div>
      </div>
    )
  }

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-2xl mx-auto">
          <div className="bg-white shadow rounded-lg p-8 animate-pulse">
            <div className="h-8 bg-gray-200 rounded w-3/4 mb-4"></div>
            <div className="h-6 bg-gray-200 rounded w-1/2 mb-8"></div>
            <div className="space-y-4">
              <div className="h-32 bg-gray-200 rounded"></div>
              <div className="h-48 bg-gray-200 rounded"></div>
            </div>
          </div>
        </div>
      </div>
    )
  }

  if (isError || !job) {
    return (
      <div className="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-2xl mx-auto">
          <div className="bg-red-50 border border-red-200 rounded-lg p-8 text-center">
            <h2 className="text-red-800 font-medium mb-2">Job Not Found</h2>
            <p className="text-red-600 mb-4">
              The job you're trying to apply to could not be found.
            </p>
            <button
              onClick={() => router.push('/jobs')}
              className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700"
            >
              Back to Jobs
            </button>
          </div>
        </div>
      </div>
    )
  }

  // Check if job is a direct post
  if (job.sourceType !== 'direct') {
    return (
      <div className="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-2xl mx-auto">
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-8 text-center">
            <h2 className="text-yellow-800 font-medium mb-2">Cannot Apply</h2>
            <p className="text-yellow-700 mb-4">
              This job is hosted on an external platform. Please visit the original job posting to apply.
            </p>
            <div className="flex gap-3 justify-center">
              <a
                href={job.sourceUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="px-6 py-2 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700"
              >
                View Original Posting
              </a>
              <button
                onClick={() => router.push(`/jobs/${jobId}`)}
                className="px-6 py-2 bg-white text-gray-700 font-medium rounded-lg border border-gray-300 hover:bg-gray-50"
              >
                Back to Job
              </button>
            </div>
          </div>
        </div>
      </div>
    )
  }

  // Success state
  if (success) {
    return (
      <div className="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-2xl mx-auto">
          <div className="bg-green-50 border border-green-200 rounded-lg p-8 text-center">
            <div className="mx-auto flex items-center justify-center h-16 w-16 rounded-full bg-green-100 mb-4">
              <svg
                className="h-10 w-10 text-green-600"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M5 13l4 4L19 7"
                />
              </svg>
            </div>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">Application Submitted!</h2>
            <p className="text-gray-600 mb-6">
              Your application for <span className="font-medium">{job.title}</span> at{' '}
              <span className="font-medium">{job.company}</span> has been successfully submitted.
            </p>
            <p className="text-sm text-gray-500 mb-8">
              The employer will review your application and contact you if they're interested.
            </p>
            <div className="flex gap-3 justify-center">
              <button
                onClick={() => router.push('/applications')}
                className="px-6 py-2 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700"
              >
                View My Applications
              </button>
              <button
                onClick={() => router.push('/jobs')}
                className="px-6 py-2 bg-white text-gray-700 font-medium rounded-lg border border-gray-300 hover:bg-gray-50"
              >
                Browse More Jobs
              </button>
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4 sm:px-6 lg:px-8">
      <div className="max-w-2xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <Link
            href={`/jobs/${jobId}`}
            className="inline-flex items-center text-sm text-gray-600 hover:text-gray-900 mb-4"
          >
            <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
            Back to Job Details
          </Link>
          <h1 className="text-3xl font-bold text-gray-900">Apply for Position</h1>
        </div>

        {/* Error Message */}
        {error && (
          <div className="mb-6 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
            {error}
          </div>
        )}

        {/* Application Form */}
        <div className="bg-white shadow rounded-lg p-8">
          <ApplicationForm
            jobId={jobId}
            jobTitle={job.title}
            company={job.company}
            onSubmit={async (data) => {
              await submitMutation.mutateAsync(data)
            }}
            onCancel={() => router.push(`/jobs/${jobId}`)}
            isSubmitting={submitMutation.isPending}
          />
        </div>
      </div>
    </div>
  )
}
