'use client'

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { jobsApi } from '@/lib/api/jobs'
import { applicationsApi } from '@/lib/api/applications'
import { useAuthStore } from '@/lib/store'
import { ProtectedRoute } from '@/components/auth/ProtectedRoute'
import Link from 'next/link'
import { formatDistanceToNow } from 'date-fns'
import { ApplicationStatus } from '@/types'

const statusConfig: Record<ApplicationStatus, { label: string; className: string }> = {
  SUBMITTED: { label: 'Submitted', className: 'bg-blue-100 text-blue-800' },
  REVIEWED: { label: 'Reviewed', className: 'bg-purple-100 text-purple-800' },
  SHORTLISTED: { label: 'Shortlisted', className: 'bg-green-100 text-green-800' },
  REJECTED: { label: 'Rejected', className: 'bg-red-100 text-red-800' },
  ACCEPTED: { label: 'Accepted', className: 'bg-emerald-100 text-emerald-800' },
}

export default function EmployerApplicationsPage() {
  return (
    <ProtectedRoute requiredRole="employer">
      <ApplicationsContent />
    </ProtectedRoute>
  )
}

function ApplicationsContent() {
  const { user } = useAuthStore()
  const queryClient = useQueryClient()
  const [selectedJob, setSelectedJob] = useState<string>('ALL')
  const [editingNotes, setEditingNotes] = useState<string | null>(null)
  const [notesText, setNotesText] = useState('')

  // Fetch employer's jobs
  const { data: jobsData } = useQuery({
    queryKey: ['employer-jobs', user?.id],
    queryFn: () => jobsApi.getJobsByEmployer(user?.id || '', 1, 100),
    enabled: !!user?.id,
  })

  const jobs = jobsData?.jobs.filter((job) => job.sourceType === 'direct') || []

  // Fetch applications for selected job or all jobs
  const { data: allApplications, isLoading } = useQuery({
    queryKey: ['all-applications', jobs.map((j) => j.id)],
    queryFn: async () => {
      const results = await Promise.all(
        jobs.map((job) =>
          applicationsApi.getApplicationsForJob(job.id).then((data) => ({
            jobId: job.id,
            jobTitle: job.title,
            applications: data.applications,
          }))
        )
      )
      return results
    },
    enabled: jobs.length > 0,
  })

  // Update application status mutation
  const updateStatusMutation = useMutation({
    mutationFn: ({ applicationId, status }: { applicationId: string; status: ApplicationStatus }) =>
      applicationsApi.updateApplicationStatus(applicationId, { status }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['all-applications'] })
    },
  })

  // Update employer notes mutation
  const updateNotesMutation = useMutation({
    mutationFn: ({ applicationId, notes }: { applicationId: string; notes: string }) =>
      applicationsApi.updateApplicationStatus(applicationId, { employer_notes: notes, status: 'REVIEWED' as ApplicationStatus }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['all-applications'] })
      setEditingNotes(null)
      setNotesText('')
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

  // Flatten and filter applications
  const allApps = allApplications?.flatMap((job) =>
    job.applications.map((app) => ({
      ...app,
      jobId: job.jobId,
      jobTitle: job.jobTitle,
    }))
  ) || []

  const filteredApplications = selectedJob === 'ALL'
    ? allApps
    : allApps.filter((app) => app.jobId === selectedJob)

  const handleStatusChange = (applicationId: string, status: ApplicationStatus) => {
    updateStatusMutation.mutate({ applicationId, status })
  }

  const handleSaveNotes = (applicationId: string) => {
    updateNotesMutation.mutate({ applicationId, notes: notesText })
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Applications</h1>
          <p className="text-gray-600">Manage applications for your job postings</p>
        </div>

        {/* Job Filter */}
        <div className="bg-white shadow rounded-lg p-4 mb-6">
          <label className="block text-sm font-medium text-gray-700 mb-2">Filter by Job</label>
          <select
            value={selectedJob}
            onChange={(e) => setSelectedJob(e.target.value)}
            className="w-full md:w-96 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="ALL">All Jobs ({allApps.length} applications)</option>
            {jobs.map((job) => {
              const count = allApps.filter((app) => app.jobId === job.id).length
              return (
                <option key={job.id} value={job.id}>
                  {job.title} ({count} applications)
                </option>
              )
            })}
          </select>
        </div>

        {/* Applications List */}
        {filteredApplications.length === 0 ? (
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
            <p className="text-gray-600">
              {selectedJob === 'ALL'
                ? 'You haven\'t received any applications yet'
                : 'This job hasn\'t received any applications yet'}
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            {filteredApplications.map((app) => {
              const statusInfo = statusConfig[app.status]
              const appliedAgo = formatDistanceToNow(new Date(app.applied_at), { addSuffix: true })

              return (
                <div
                  key={app.id}
                  className="bg-white shadow rounded-lg p-6 hover:shadow-md transition-shadow"
                >
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex-1">
                      <h3 className="text-lg font-semibold text-gray-900 mb-1">
                        {app.applicant_name}
                      </h3>
                      <Link
                        href={`/employer/jobs/${app.jobId}`}
                        className="text-blue-600 hover:text-blue-700 hover:underline text-sm"
                      >
                        {app.jobTitle}
                      </Link>
                      <p className="text-sm text-gray-600 mt-1">Applied {appliedAgo}</p>
                    </div>
                    <span className={`px-3 py-1 text-sm font-medium rounded-full ${statusInfo.className}`}>
                      {statusInfo.label}
                    </span>
                  </div>

                  {/* Application Details */}
                  <div className="border-t border-gray-200 pt-4 mt-4">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                      <div>
                        <span className="text-sm text-gray-600">Resume:</span>
                        <a
                          href={app.resume}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="ml-2 text-sm text-blue-600 hover:text-blue-700 hover:underline"
                        >
                          View Resume →
                        </a>
                      </div>
                      <div>
                        <span className="text-sm text-gray-600">Status:</span>
                        <select
                          value={app.status}
                          onChange={(e) => handleStatusChange(app.id, e.target.value as ApplicationStatus)}
                          disabled={updateStatusMutation.isPending}
                          className="ml-2 text-sm px-3 py-1 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        >
                          {Object.entries(statusConfig).map(([value, config]) => (
                            <option key={value} value={value}>
                              {config.label}
                            </option>
                          ))}
                        </select>
                      </div>
                    </div>

                    {app.cover_letter && (
                      <div className="mb-4">
                        <span className="text-sm font-medium text-gray-700">Cover Letter:</span>
                        <p className="mt-1 text-sm text-gray-700 bg-gray-50 p-3 rounded">
                          {app.cover_letter}
                        </p>
                      </div>
                    )}

                    {/* Employer Notes */}
                    <div>
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-sm font-medium text-gray-700">Employer Notes:</span>
                        {editingNotes !== app.id && (
                          <button
                            onClick={() => {
                              setEditingNotes(app.id)
                              setNotesText(app.employer_notes || '')
                            }}
                            className="text-sm text-blue-600 hover:text-blue-700"
                          >
                            {app.employer_notes ? 'Edit' : 'Add Notes'}
                          </button>
                        )}
                      </div>
                      {editingNotes === app.id ? (
                        <div>
                          <textarea
                            value={notesText}
                            onChange={(e) => setNotesText(e.target.value)}
                            rows={3}
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
                            placeholder="Add notes about this applicant..."
                          />
                          <div className="flex gap-2 mt-2">
                            <button
                              onClick={() => handleSaveNotes(app.id)}
                              disabled={updateNotesMutation.isPending}
                              className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 disabled:bg-gray-400"
                            >
                              Save
                            </button>
                            <button
                              onClick={() => {
                                setEditingNotes(null)
                                setNotesText('')
                              }}
                              className="px-4 py-2 bg-gray-100 text-gray-700 text-sm font-medium rounded-lg hover:bg-gray-200"
                            >
                              Cancel
                            </button>
                          </div>
                        </div>
                      ) : (
                        <p className="text-sm text-gray-700 bg-gray-50 p-3 rounded">
                          {app.employer_notes || 'No notes yet'}
                        </p>
                      )}
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        )}

        {/* Summary Stats */}
        {filteredApplications.length > 0 && (
          <div className="mt-8 bg-white shadow rounded-lg p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Application Summary</h2>
            <div className="grid grid-cols-2 sm:grid-cols-5 gap-4">
              {Object.entries(statusConfig).map(([status, config]) => {
                const count = filteredApplications.filter((app) => app.status === status).length
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
