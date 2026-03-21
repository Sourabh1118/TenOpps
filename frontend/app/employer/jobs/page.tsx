'use client'

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { jobsApi } from '@/lib/api/jobs'
import { useAuthStore } from '@/lib/store'
import { ProtectedRoute } from '@/components/auth/ProtectedRoute'
import Link from 'next/link'
import { formatDistanceToNow } from 'date-fns'
import { JobStatus } from '@/types'

const statusConfig: Record<JobStatus, { label: string; className: string }> = {
  ACTIVE: { label: 'Active', className: 'bg-green-100 text-green-800' },
  EXPIRED: { label: 'Expired', className: 'bg-yellow-100 text-yellow-800' },
  FILLED: { label: 'Filled', className: 'bg-blue-100 text-blue-800' },
  DELETED: { label: 'Deleted', className: 'bg-gray-100 text-gray-800' },
}

export default function MyJobsPage() {
  return (
    <ProtectedRoute requiredRole="employer">
      <MyJobsContent />
    </ProtectedRoute>
  )
}

function MyJobsContent() {
  const { user } = useAuthStore()
  const queryClient = useQueryClient()
  const [statusFilter, setStatusFilter] = useState<JobStatus | 'ALL'>('ALL')
  const [deleteConfirm, setDeleteConfirm] = useState<string | null>(null)

  // Fetch jobs
  const { data, isLoading, isError, error } = useQuery({
    queryKey: ['employer-jobs', user?.id],
    queryFn: () => jobsApi.getJobsByEmployer(user?.id || '', 1, 100),
    enabled: !!user?.id,
  })

  // Delete job mutation
  const deleteMutation = useMutation({
    mutationFn: (jobId: string) => jobsApi.deleteJob(jobId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['employer-jobs'] })
      setDeleteConfirm(null)
    },
  })

  // Mark as filled mutation
  const markFilledMutation = useMutation({
    mutationFn: (jobId: string) => jobsApi.markJobAsFilled(jobId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['employer-jobs'] })
    },
  })

  // Feature job mutation
  const featureMutation = useMutation({
    mutationFn: (jobId: string) => jobsApi.featureJob(jobId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['employer-jobs'] })
      queryClient.invalidateQueries({ queryKey: ['subscription-info'] })
    },
  })

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 py-8 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="h-8 bg-gray-200 rounded w-64 mb-8 animate-pulse"></div>
          <div className="space-y-4">
            {[1, 2, 3].map((i) => (
              <div key={i} className="bg-white shadow rounded-lg p-6 animate-pulse">
                <div className="h-6 bg-gray-200 rounded w-3/4 mb-4"></div>
                <div className="h-4 bg-gray-200 rounded w-1/2"></div>
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
            <h2 className="text-red-800 font-medium mb-2">Error Loading Jobs</h2>
            <p className="text-red-600">
              {error instanceof Error ? error.message : 'Failed to load jobs'}
            </p>
          </div>
        </div>
      </div>
    )
  }

  const jobs = data?.jobs || []
  const filteredJobs = statusFilter === 'ALL' ? jobs : jobs.filter((job) => job.status === statusFilter)

  const statusCounts = {
    ALL: jobs.length,
    ACTIVE: jobs.filter((j) => j.status === 'ACTIVE').length,
    EXPIRED: jobs.filter((j) => j.status === 'EXPIRED').length,
    FILLED: jobs.filter((j) => j.status === 'FILLED').length,
    DELETED: jobs.filter((j) => j.status === 'DELETED').length,
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 mb-2">My Jobs</h1>
            <p className="text-gray-600">Manage your job postings</p>
          </div>
          <div className="flex gap-3">
            <Link
              href="/employer/jobs/import"
              className="px-4 py-2 bg-white text-gray-700 font-medium rounded-lg border border-gray-300 hover:bg-gray-50 transition-colors"
            >
              Import from URL
            </Link>
            <Link
              href="/employer/jobs/post"
              className="px-4 py-2 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 transition-colors"
            >
              + Post New Job
            </Link>
          </div>
        </div>

        {/* Status Filter */}
        <div className="bg-white shadow rounded-lg p-4 mb-6">
          <div className="flex flex-wrap gap-2">
            {(['ALL', 'ACTIVE', 'EXPIRED', 'FILLED', 'DELETED'] as const).map((status) => (
              <button
                key={status}
                onClick={() => setStatusFilter(status)}
                className={`px-4 py-2 rounded-lg font-medium text-sm transition-colors ${
                  statusFilter === status
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                {status === 'ALL' ? 'All' : statusConfig[status].label} ({statusCounts[status]})
              </button>
            ))}
          </div>
        </div>

        {/* Jobs List */}
        {filteredJobs.length === 0 ? (
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
                d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
              />
            </svg>
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              {statusFilter === 'ALL' ? 'No Jobs Posted Yet' : `No ${statusConfig[statusFilter]?.label} Jobs`}
            </h3>
            <p className="text-gray-600 mb-6">
              {statusFilter === 'ALL'
                ? 'Get started by posting your first job'
                : 'Try selecting a different filter'}
            </p>
            {statusFilter === 'ALL' && (
              <Link
                href="/employer/jobs/post"
                className="inline-flex items-center px-6 py-3 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700"
              >
                Post Your First Job
              </Link>
            )}
          </div>
        ) : (
          <div className="space-y-4">
            {filteredJobs.map((job) => {
              const postedAgo = formatDistanceToNow(new Date(job.postedAt), { addSuffix: true })
              const statusInfo = statusConfig[job.status]

              return (
                <div
                  key={job.id}
                  className="bg-white shadow rounded-lg p-6 hover:shadow-md transition-shadow"
                >
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <Link
                          href={`/employer/jobs/${job.id}`}
                          className="text-xl font-semibold text-gray-900 hover:text-blue-600 transition-colors"
                        >
                          {job.title}
                        </Link>
                        {job.featured && (
                          <span className="px-2 py-1 text-xs font-medium bg-yellow-100 text-yellow-800 rounded-full">
                            ⭐ Featured
                          </span>
                        )}
                      </div>
                      <div className="flex items-center gap-4 text-sm text-gray-600">
                        <span className="flex items-center gap-1">
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
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
                          {job.location}
                        </span>
                        <span>Posted {postedAgo}</span>
                      </div>
                    </div>
                    <span className={`px-3 py-1 text-sm font-medium rounded-full ${statusInfo.className}`}>
                      {statusInfo.label}
                    </span>
                  </div>

                  {/* Stats */}
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 py-4 border-t border-b border-gray-200">
                    <div>
                      <div className="text-2xl font-bold text-gray-900">{job.viewCount}</div>
                      <div className="text-sm text-gray-600">Views</div>
                    </div>
                    <div>
                      <div className="text-2xl font-bold text-gray-900">{job.applicationCount || 0}</div>
                      <div className="text-sm text-gray-600">Applications</div>
                    </div>
                    <div>
                      <div className="text-2xl font-bold text-gray-900">{job.qualityScore}</div>
                      <div className="text-sm text-gray-600">Quality Score</div>
                    </div>
                    <div>
                      <div className="text-sm font-medium text-gray-900">{job.sourceType}</div>
                      <div className="text-sm text-gray-600">Source</div>
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="flex flex-wrap gap-2 mt-4">
                    <Link
                      href={`/employer/jobs/${job.id}`}
                      className="px-4 py-2 text-sm font-medium text-blue-600 bg-blue-50 rounded-lg hover:bg-blue-100 transition-colors"
                    >
                      View Details
                    </Link>
                    <Link
                      href={`/employer/jobs/${job.id}/edit`}
                      className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
                    >
                      Edit
                    </Link>
                    {job.status === 'ACTIVE' && (
                      <>
                        <button
                          onClick={() => markFilledMutation.mutate(job.id)}
                          disabled={markFilledMutation.isPending}
                          className="px-4 py-2 text-sm font-medium text-green-700 bg-green-50 rounded-lg hover:bg-green-100 transition-colors disabled:opacity-50"
                        >
                          Mark as Filled
                        </button>
                        {!job.featured && (
                          <button
                            onClick={() => featureMutation.mutate(job.id)}
                            disabled={featureMutation.isPending}
                            className="px-4 py-2 text-sm font-medium text-yellow-700 bg-yellow-50 rounded-lg hover:bg-yellow-100 transition-colors disabled:opacity-50"
                          >
                            ⭐ Feature
                          </button>
                        )}
                      </>
                    )}
                    {job.status !== 'DELETED' && (
                      <>
                        {deleteConfirm === job.id ? (
                          <div className="flex gap-2">
                            <button
                              onClick={() => deleteMutation.mutate(job.id)}
                              disabled={deleteMutation.isPending}
                              className="px-4 py-2 text-sm font-medium text-white bg-red-600 rounded-lg hover:bg-red-700 transition-colors disabled:opacity-50"
                            >
                              Confirm Delete
                            </button>
                            <button
                              onClick={() => setDeleteConfirm(null)}
                              className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
                            >
                              Cancel
                            </button>
                          </div>
                        ) : (
                          <button
                            onClick={() => setDeleteConfirm(job.id)}
                            className="px-4 py-2 text-sm font-medium text-red-700 bg-red-50 rounded-lg hover:bg-red-100 transition-colors"
                          >
                            Delete
                          </button>
                        )}
                      </>
                    )}
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}
