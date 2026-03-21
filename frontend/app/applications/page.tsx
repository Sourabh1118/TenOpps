'use client'

import { useQuery } from '@tanstack/react-query'
import { applicationsApi } from '@/lib/api/applications'
import { useAuthStore } from '@/lib/store'
import { formatDistanceToNow } from 'date-fns'
import Link from 'next/link'
import { ApplicationStatus } from '@/types'

const statusConfig: Record<ApplicationStatus, { label: string; className: string }> = {
  SUBMITTED: {
    label: 'Submitted',
    className: 'bg-blue-100 text-blue-800',
  },
  REVIEWED: {
    label: 'Reviewed',
    className: 'bg-purple-100 text-purple-800',
  },
  SHORTLISTED: {
    label: 'Shortlisted',
    className: 'bg-green-100 text-green-800',
  },
  REJECTED: {
    label: 'Rejected',
    className: 'bg-red-100 text-red-800',
  },
  ACCEPTED: {
    label: 'Accepted',
    className: 'bg-emerald-100 text-emerald-800',
  },
}

export default function MyApplicationsPage() {
  const { user, isAuthenticated } = useAuthStore()

  // Fetch applications
  const { data, isLoading, isError, error } = useQuery({
    queryKey: ['my-applications'],
    queryFn: () => applicationsApi.getMyApplications(),
    enabled: isAuthenticated && user?.role === 'job_seeker',
  })

  // Check authentication
  if (!isAuthenticated || user?.role !== 'job_seeker') {
    return (
      <div className="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-4xl mx-auto">
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-8 text-center">
            <h2 className="text-xl font-semibold text-gray-900 mb-2">
              Job Seeker Account Required
            </h2>
            <p className="text-gray-600 mb-6">
              You need to be logged in as a job seeker to view your applications.
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
      <div className="min-h-screen bg-gray-50 py-8 px-4 sm:px-6 lg:px-8">
        <div className="max-w-6xl mx-auto">
          <div className="mb-8">
            <div className="h-8 bg-gray-200 rounded w-64 mb-2 animate-pulse"></div>
            <div className="h-4 bg-gray-200 rounded w-96 animate-pulse"></div>
          </div>
          <div className="space-y-4">
            {[1, 2, 3].map((i) => (
              <div key={i} className="bg-white shadow rounded-lg p-6 animate-pulse">
                <div className="h-6 bg-gray-200 rounded w-3/4 mb-4"></div>
                <div className="h-4 bg-gray-200 rounded w-1/2 mb-2"></div>
                <div className="h-4 bg-gray-200 rounded w-1/3"></div>
              </div>
            ))}
          </div>
        </div>
      </div>
    )
  }

  if (isError) {
    return (
      <div className="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-4xl mx-auto">
          <div className="bg-red-50 border border-red-200 rounded-lg p-8">
            <h2 className="text-red-800 font-medium mb-2">Error Loading Applications</h2>
            <p className="text-red-600">
              {error instanceof Error ? error.message : 'Failed to load applications'}
            </p>
          </div>
        </div>
      </div>
    )
  }

  const applications = data?.applications || []

  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4 sm:px-6 lg:px-8">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">My Applications</h1>
          <p className="text-gray-600">
            Track the status of your job applications
          </p>
        </div>

        {/* Applications List */}
        {applications.length === 0 ? (
          <div className="bg-white shadow rounded-lg p-12 text-center">
            <svg
              className="mx-auto h-16 w-16 text-gray-400 mb-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
              />
            </svg>
            <h3 className="text-lg font-medium text-gray-900 mb-2">No Applications Yet</h3>
            <p className="text-gray-600 mb-6">
              You haven't applied to any jobs yet. Start browsing to find your next opportunity!
            </p>
            <Link
              href="/jobs"
              className="inline-flex items-center px-6 py-3 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700"
            >
              Browse Jobs
            </Link>
          </div>
        ) : (
          <div className="space-y-4">
            {applications.map((application) => {
              const appliedAgo = formatDistanceToNow(new Date(application.applied_at), {
                addSuffix: true,
              })
              const statusInfo = statusConfig[application.status]

              return (
                <div
                  key={application.id}
                  className="bg-white shadow rounded-lg p-6 hover:shadow-md transition-shadow"
                >
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex-1">
                      <Link
                        href={`/jobs/${application.job_id}`}
                        className="text-xl font-semibold text-gray-900 hover:text-blue-600 transition-colors"
                      >
                        {application.job_title}
                      </Link>
                      <p className="text-gray-700 font-medium mt-1">{application.company}</p>
                      <div className="flex items-center gap-2 mt-2 text-sm text-gray-600">
                        <svg
                          className="w-4 h-4"
                          fill="none"
                          stroke="currentColor"
                          viewBox="0 0 24 24"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"
                          />
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"
                          />
                        </svg>
                        <span>{application.location}</span>
                      </div>
                    </div>
                    <span
                      className={`px-3 py-1 text-sm font-medium rounded-full ${statusInfo.className}`}
                    >
                      {statusInfo.label}
                    </span>
                  </div>

                  <div className="border-t border-gray-200 pt-4 mt-4">
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-sm">
                      <div>
                        <span className="text-gray-500">Applied:</span>
                        <span className="ml-2 text-gray-900">{appliedAgo}</span>
                      </div>
                      <div>
                        <span className="text-gray-500">Resume:</span>
                        <a
                          href={application.resume}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="ml-2 text-blue-600 hover:text-blue-700 hover:underline"
                        >
                          View Resume
                        </a>
                      </div>
                      {application.cover_letter && (
                        <div className="sm:col-span-2">
                          <span className="text-gray-500">Cover Letter:</span>
                          <p className="mt-1 text-gray-700 text-sm line-clamp-2">
                            {application.cover_letter}
                          </p>
                        </div>
                      )}
                    </div>
                  </div>

                  <div className="mt-4 flex gap-3">
                    <Link
                      href={`/jobs/${application.job_id}`}
                      className="px-4 py-2 text-sm font-medium text-blue-600 bg-blue-50 rounded-lg hover:bg-blue-100 transition-colors"
                    >
                      View Job Details
                    </Link>
                  </div>
                </div>
              )
            })}
          </div>
        )}

        {/* Summary Stats */}
        {applications.length > 0 && (
          <div className="mt-8 bg-white shadow rounded-lg p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Application Summary</h2>
            <div className="grid grid-cols-2 sm:grid-cols-5 gap-4">
              {Object.entries(statusConfig).map(([status, config]) => {
                const count = applications.filter((app) => app.status === status).length
                return (
                  <div key={status} className="text-center">
                    <div className={`text-2xl font-bold ${config.className.split(' ')[1]}`}>
                      {count}
                    </div>
                    <div className="text-sm text-gray-600 mt-1">{config.label}</div>
                  </div>
                )
              })}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
