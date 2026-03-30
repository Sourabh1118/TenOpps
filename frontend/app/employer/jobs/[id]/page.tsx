'use client'

import { useQuery } from '@tanstack/react-query'
import { jobsApi } from '@/lib/api/jobs'
import { applicationsApi } from '@/lib/api/applications'
import { useParams, useSearchParams } from 'next/navigation'
import { ProtectedRoute } from '@/components/auth/ProtectedRoute'
import Link from 'next/link'
import { formatDistanceToNow, format } from 'date-fns'
import { JobStatus } from '@/types'

const statusConfig: Record<JobStatus, { label: string; className: string }> = {
  ACTIVE: { label: 'Active', className: 'bg-green-100 text-green-800' },
  EXPIRED: { label: 'Expired', className: 'bg-yellow-100 text-yellow-800' },
  FILLED: { label: 'Filled', className: 'bg-blue-100 text-blue-800' },
  DELETED: { label: 'Deleted', className: 'bg-gray-100 text-gray-800' },
}

export default function EmployerJobDetailsPage() {
  return (
    <ProtectedRoute requiredRole="employer">
      <JobDetailsContent />
    </ProtectedRoute>
  )
}

function JobDetailsContent() {
  const params = useParams()
  const searchParams = useSearchParams()
  const jobId = params.id as string
  const posted = searchParams.get('posted') === 'true'
  const updated = searchParams.get('updated') === 'true'

  // Fetch job details
  const { data: job, isLoading: jobLoading } = useQuery({
    queryKey: ['job', jobId],
    queryFn: () => jobsApi.getJobById(jobId),
  })

  // Fetch applications for this job
  const { data: applicationsData, isLoading: appsLoading } = useQuery({
    queryKey: ['job-applications', jobId],
    queryFn: () => applicationsApi.getApplicationsForJob(jobId),
    enabled: !!job && job.sourceType === 'direct',
  })

  const isLoading = jobLoading || appsLoading

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 py-8 px-4 sm:px-6 lg:px-8">
        <div className="max-w-5xl mx-auto">
          <div className="h-8 bg-gray-200 rounded w-64 mb-8 animate-pulse"></div>
          <div className="bg-white shadow rounded-lg p-8 animate-pulse">
            <div className="h-8 bg-gray-200 rounded w-3/4 mb-4"></div>
            <div className="h-4 bg-gray-200 rounded w-1/2 mb-8"></div>
            <div className="space-y-4">
              {[1, 2, 3].map((i) => (
                <div key={i} className="h-4 bg-gray-200 rounded"></div>
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
            <p className="text-red-600">The job you're looking for could not be found.</p>
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

  const statusInfo = statusConfig[job.status]
  const applications = applicationsData?.applications || []

  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4 sm:px-6 lg:px-8">
      <div className="max-w-5xl mx-auto">
        {/* Success Messages */}
        {posted && (
          <div className="mb-6 bg-green-50 border border-green-200 rounded-lg p-4">
            <div className="flex items-center">
              <svg
                className="w-5 h-5 text-green-600 mr-3"
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
              <p className="text-green-800 font-medium">Job posted successfully!</p>
            </div>
          </div>
        )}
        {updated && (
          <div className="mb-6 bg-green-50 border border-green-200 rounded-lg p-4">
            <div className="flex items-center">
              <svg
                className="w-5 h-5 text-green-600 mr-3"
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
              <p className="text-green-800 font-medium">Job updated successfully!</p>
            </div>
          </div>
        )}

        {/* Header */}
        <div className="mb-6">
          <Link
            href="/employer/jobs"
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
            Back to My Jobs
          </Link>
        </div>

        {/* Job Details Card */}
        <div className="bg-white shadow rounded-lg p-6 md:p-8 mb-6">
          <div className="flex items-start justify-between mb-6">
            <div className="flex-1">
              <div className="flex items-center gap-3 mb-2">
                <h1 className="text-3xl font-bold text-gray-900">{job.title}</h1>
                {job.featured && (
                  <span className="px-3 py-1 text-sm font-medium bg-yellow-100 text-yellow-800 rounded-full">
                    ⭐ Featured
                  </span>
                )}
              </div>
              <p className="text-xl text-gray-700 mb-4">{job.company}</p>
              <div className="flex flex-wrap items-center gap-4 text-gray-600">
                <span className="flex items-center gap-1">
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
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
                {job.remote && (
                  <span className="px-2 py-1 bg-blue-100 text-blue-800 text-sm font-medium rounded">
                    Remote
                  </span>
                )}
                <span className="px-2 py-1 bg-gray-100 text-gray-800 text-sm font-medium rounded">
                  {job.jobType.replace('_', ' ')}
                </span>
                <span className="px-2 py-1 bg-gray-100 text-gray-800 text-sm font-medium rounded">
                  {job.experienceLevel}
                </span>
              </div>
            </div>
            <span className={`px-4 py-2 text-sm font-medium rounded-full ${statusInfo.className}`}>
              {statusInfo.label}
            </span>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 py-6 border-t border-b border-gray-200 mb-6">
            <div>
              <div className="text-3xl font-bold text-gray-900">{job.viewCount}</div>
              <div className="text-sm text-gray-600">Views</div>
            </div>
            <div>
              <div className="text-3xl font-bold text-gray-900">{job.applicationCount || 0}</div>
              <div className="text-sm text-gray-600">Applications</div>
            </div>
            <div>
              <div className="text-3xl font-bold text-gray-900">{job.qualityScore}</div>
              <div className="text-sm text-gray-600">Quality Score</div>
            </div>
            <div>
              <div className="text-sm font-medium text-gray-900">
                {formatDistanceToNow(new Date(job.postedAt), { addSuffix: true })}
              </div>
              <div className="text-sm text-gray-600">Posted</div>
            </div>
          </div>

          {/* Actions */}
          <div className="flex flex-wrap gap-3">
            <Link
              href={`/employer/jobs/${job.id}/edit`}
              className="px-4 py-2 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 transition-colors"
            >
              Edit Job
            </Link>
            <Link
              href={`/jobs/${job.id}`}
              target="_blank"
              className="px-4 py-2 bg-gray-100 text-gray-700 font-medium rounded-lg hover:bg-gray-200 transition-colors"
            >
              View Public Page
            </Link>
            {job.sourceType === 'direct' && applications.length > 0 && (
              <Link
                href={`#applications`}
                className="px-4 py-2 bg-green-100 text-green-700 font-medium rounded-lg hover:bg-green-200 transition-colors"
              >
                View Applications ({applications.length})
              </Link>
            )}
          </div>
        </div>

        {/* Job Description */}
        <div className="bg-white shadow rounded-lg p-6 md:p-8 mb-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Job Description</h2>
          <div 
            className="prose max-w-none text-gray-700"
            dangerouslySetInnerHTML={{ __html: job.description }}
          />

          {job.requirements && job.requirements.length > 0 && (
            <div className="mt-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-3">Requirements</h3>
              <ul className="list-disc list-inside space-y-2 text-gray-700">
                {job.requirements.map((req, index) => (
                  <li key={index}>{req}</li>
                ))}
              </ul>
            </div>
          )}

          {job.responsibilities && job.responsibilities.length > 0 && (
            <div className="mt-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-3">Responsibilities</h3>
              <ul className="list-disc list-inside space-y-2 text-gray-700">
                {job.responsibilities.map((resp, index) => (
                  <li key={index}>{resp}</li>
                ))}
              </ul>
            </div>
          )}

          {(job.salaryMin || job.salaryMax) && (
            <div className="mt-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-2">Salary Range</h3>
              <p className="text-gray-700">
                {job.salaryMin && job.salaryMax
                  ? `${job.salaryCurrency} ${job.salaryMin.toLocaleString()} - ${job.salaryMax.toLocaleString()}`
                  : job.salaryMin
                  ? `From ${job.salaryCurrency} ${job.salaryMin.toLocaleString()}`
                  : `Up to ${job.salaryCurrency} ${job.salaryMax?.toLocaleString()}`}
              </p>
            </div>
          )}

          {job.tags && job.tags.length > 0 && (
            <div className="mt-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-3">Tags</h3>
              <div className="flex flex-wrap gap-2">
                {job.tags.map((tag, index) => (
                  <span
                    key={index}
                    className="px-3 py-1 bg-blue-100 text-blue-800 text-sm font-medium rounded-full"
                  >
                    {tag}
                  </span>
                ))}
              </div>
            </div>
          )}

          <div className="mt-6 pt-6 border-t border-gray-200">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-gray-600">Posted:</span>
                <span className="ml-2 text-gray-900">
                  {format(new Date(job.postedAt), 'MMM d, yyyy')}
                </span>
              </div>
              <div>
                <span className="text-gray-600">Expires:</span>
                <span className="ml-2 text-gray-900">
                  {format(new Date(job.expiresAt), 'MMM d, yyyy')}
                </span>
              </div>
              <div>
                <span className="text-gray-600">Source:</span>
                <span className="ml-2 text-gray-900">{job.sourceType}</span>
              </div>
              {job.sourceUrl && (
                <div>
                  <span className="text-gray-600">Original URL:</span>
                  <a
                    href={job.sourceUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="ml-2 text-blue-600 hover:text-blue-700 hover:underline"
                  >
                    View Source
                  </a>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Applications Section */}
        {job.sourceType === 'direct' && (
          <div id="applications" className="bg-white shadow rounded-lg p-6 md:p-8">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">
              Applications ({applications.length})
            </h2>
            {applications.length === 0 ? (
              <div className="text-center py-8">
                <svg
                  className="mx-auto h-12 w-12 text-gray-400 mb-4"
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
                <p className="text-gray-600">No applications yet</p>
              </div>
            ) : (
              <div className="space-y-4">
                {applications.slice(0, 5).map((app) => (
                  <div
                    key={app.id}
                    className="p-4 border border-gray-200 rounded-lg hover:border-blue-300 transition-colors"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <p className="font-medium text-gray-900">{app.applicant_name}</p>
                        <p className="text-sm text-gray-600">
                          Applied {formatDistanceToNow(new Date(app.applied_at), { addSuffix: true })}
                        </p>
                      </div>
                      <span
                        className={`px-3 py-1 text-xs font-medium rounded-full ${
                          app.status === 'SUBMITTED'
                            ? 'bg-blue-100 text-blue-800'
                            : app.status === 'REVIEWED'
                            ? 'bg-purple-100 text-purple-800'
                            : app.status === 'SHORTLISTED'
                            ? 'bg-green-100 text-green-800'
                            : app.status === 'REJECTED'
                            ? 'bg-red-100 text-red-800'
                            : 'bg-emerald-100 text-emerald-800'
                        }`}
                      >
                        {app.status}
                      </span>
                    </div>
                    <div className="mt-2">
                      <a
                        href={app.resume}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-sm text-blue-600 hover:text-blue-700 hover:underline"
                      >
                        View Resume →
                      </a>
                    </div>
                  </div>
                ))}
                {applications.length > 5 && (
                  <Link
                    href="/employer/applications"
                    className="block text-center py-3 text-blue-600 hover:text-blue-700 font-medium"
                  >
                    View All Applications →
                  </Link>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
