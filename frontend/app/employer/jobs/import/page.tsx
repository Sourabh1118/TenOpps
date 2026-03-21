'use client'

import { useState, useEffect } from 'react'
import { useMutation } from '@tanstack/react-query'
import { urlImportApi } from '@/lib/api/url-import'
import { useRouter } from 'next/navigation'
import { ProtectedRoute } from '@/components/auth/ProtectedRoute'
import Link from 'next/link'

export default function ImportJobPage() {
  return (
    <ProtectedRoute requiredRole="employer">
      <ImportJobContent />
    </ProtectedRoute>
  )
}

function ImportJobContent() {
  const router = useRouter()
  const [url, setUrl] = useState('')
  const [urlError, setUrlError] = useState('')
  const [taskId, setTaskId] = useState<string | null>(null)
  const [importStatus, setImportStatus] = useState<'idle' | 'importing' | 'polling' | 'success' | 'error'>('idle')
  const [statusMessage, setStatusMessage] = useState('')
  const [jobId, setJobId] = useState<string | null>(null)

  const importMutation = useMutation({
    mutationFn: async (url: string) => {
      return urlImportApi.importJobFromURL({ url })
    },
    onSuccess: (response) => {
      setTaskId(response.task_id)
      setImportStatus('polling')
      setStatusMessage('Import started. Fetching job details...')
    },
    onError: (error: any) => {
      setImportStatus('error')
      if (error.response?.status === 403) {
        setStatusMessage('You have exceeded your import quota. Please upgrade your subscription.')
      } else if (error.response?.status === 400) {
        setStatusMessage(error.response?.data?.detail || 'Invalid URL or unsupported domain')
      } else {
        setStatusMessage(error.response?.data?.detail || error.message || 'Failed to start import')
      }
    },
  })

  // Poll for import status
  useEffect(() => {
    if (!taskId || importStatus !== 'polling') return

    const pollInterval = setInterval(async () => {
      try {
        const status = await urlImportApi.getImportStatus(taskId)

        if (status.status === 'COMPLETED') {
          setImportStatus('success')
          setJobId(status.job_id || null)
          setStatusMessage('Job imported successfully!')
          clearInterval(pollInterval)
        } else if (status.status === 'FAILED') {
          setImportStatus('error')
          setStatusMessage(status.error_message || 'Import failed')
          clearInterval(pollInterval)
        } else {
          setStatusMessage(`Import in progress... (${status.status})`)
        }
      } catch (error: any) {
        setImportStatus('error')
        setStatusMessage('Failed to check import status')
        clearInterval(pollInterval)
      }
    }, 2000) // Poll every 2 seconds

    return () => clearInterval(pollInterval)
  }, [taskId, importStatus])

  const validateUrl = (url: string): boolean => {
    setUrlError('')

    if (!url.trim()) {
      setUrlError('URL is required')
      return false
    }

    try {
      const urlObj = new URL(url)
      if (!['http:', 'https:'].includes(urlObj.protocol)) {
        setUrlError('URL must use HTTP or HTTPS protocol')
        return false
      }
    } catch {
      setUrlError('Invalid URL format')
      return false
    }

    return true
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!validateUrl(url)) {
      return
    }

    setImportStatus('importing')
    setStatusMessage('Starting import...')
    await importMutation.mutateAsync(url)
  }

  const handleReset = () => {
    setUrl('')
    setUrlError('')
    setTaskId(null)
    setImportStatus('idle')
    setStatusMessage('')
    setJobId(null)
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4 sm:px-6 lg:px-8">
      <div className="max-w-3xl mx-auto">
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
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Import Job from URL</h1>
          <p className="text-gray-600">
            Import a job posting by providing a URL from a supported platform
          </p>
        </div>

        {/* Import Form */}
        {importStatus === 'idle' && (
          <div className="bg-white shadow rounded-lg p-6 md:p-8">
            <form onSubmit={handleSubmit}>
              <div className="mb-6">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Job URL <span className="text-red-500">*</span>
                </label>
                <input
                  type="url"
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="https://www.linkedin.com/jobs/view/..."
                />
                {urlError && <p className="text-sm text-red-600 mt-2">{urlError}</p>}
                <p className="text-sm text-gray-500 mt-2">
                  Paste the URL of a job posting from LinkedIn, Indeed, or other supported platforms
                </p>
              </div>

              <button
                type="submit"
                className="w-full px-6 py-3 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 transition-colors"
              >
                Import Job
              </button>
            </form>

            {/* Supported Platforms */}
            <div className="mt-8 pt-6 border-t border-gray-200">
              <h3 className="text-sm font-medium text-gray-900 mb-3">Supported Platforms</h3>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                {['LinkedIn', 'Indeed', 'Monster', 'Naukri'].map((platform) => (
                  <div
                    key={platform}
                    className="flex items-center justify-center p-3 bg-gray-50 rounded-lg border border-gray-200"
                  >
                    <span className="text-sm font-medium text-gray-700">{platform}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Import Progress */}
        {(importStatus === 'importing' || importStatus === 'polling') && (
          <div className="bg-white shadow rounded-lg p-8">
            <div className="text-center">
              <div className="inline-flex items-center justify-center w-16 h-16 bg-blue-100 rounded-full mb-4">
                <svg
                  className="animate-spin h-8 w-8 text-blue-600"
                  fill="none"
                  viewBox="0 0 24 24"
                >
                  <circle
                    className="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="4"
                  ></circle>
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                  ></path>
                </svg>
              </div>
              <h2 className="text-xl font-semibold text-gray-900 mb-2">Importing Job</h2>
              <p className="text-gray-600 mb-4">{statusMessage}</p>
              <div className="w-full bg-gray-200 rounded-full h-2 mb-4">
                <div className="bg-blue-600 h-2 rounded-full animate-pulse" style={{ width: '60%' }}></div>
              </div>
              <p className="text-sm text-gray-500">This may take a few moments...</p>
            </div>
          </div>
        )}

        {/* Success State */}
        {importStatus === 'success' && (
          <div className="bg-white shadow rounded-lg p-8">
            <div className="text-center">
              <div className="inline-flex items-center justify-center w-16 h-16 bg-green-100 rounded-full mb-4">
                <svg
                  className="w-8 h-8 text-green-600"
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
              <h2 className="text-xl font-semibold text-gray-900 mb-2">Import Successful!</h2>
              <p className="text-gray-600 mb-6">{statusMessage}</p>

              <div className="flex flex-col sm:flex-row gap-3 justify-center">
                {jobId && (
                  <Link
                    href={`/employer/jobs/${jobId}`}
                    className="px-6 py-3 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 transition-colors"
                  >
                    View Job Details
                  </Link>
                )}
                <button
                  onClick={handleReset}
                  className="px-6 py-3 bg-white text-gray-700 font-medium rounded-lg border border-gray-300 hover:bg-gray-50 transition-colors"
                >
                  Import Another Job
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Error State */}
        {importStatus === 'error' && (
          <div className="bg-white shadow rounded-lg p-8">
            <div className="text-center">
              <div className="inline-flex items-center justify-center w-16 h-16 bg-red-100 rounded-full mb-4">
                <svg
                  className="w-8 h-8 text-red-600"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M6 18L18 6M6 6l12 12"
                  />
                </svg>
              </div>
              <h2 className="text-xl font-semibold text-gray-900 mb-2">Import Failed</h2>
              <p className="text-gray-600 mb-6">{statusMessage}</p>

              <div className="flex flex-col sm:flex-row gap-3 justify-center">
                <button
                  onClick={handleReset}
                  className="px-6 py-3 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 transition-colors"
                >
                  Try Again
                </button>
                {statusMessage.includes('quota') && (
                  <Link
                    href="/employer/subscription"
                    className="px-6 py-3 bg-white text-gray-700 font-medium rounded-lg border border-gray-300 hover:bg-gray-50 transition-colors"
                  >
                    Upgrade Subscription
                  </Link>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Help Section */}
        <div className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
          <h3 className="text-sm font-medium text-blue-900 mb-2">How URL Import Works</h3>
          <ul className="text-sm text-blue-800 space-y-1 list-disc list-inside">
            <li>Paste a job URL from a supported platform</li>
            <li>Our system automatically extracts job details</li>
            <li>The job is added to your account with proper attribution</li>
            <li>You can edit the imported job details if needed</li>
            <li>Import counts against your monthly quota</li>
          </ul>
        </div>
      </div>
    </div>
  )
}
