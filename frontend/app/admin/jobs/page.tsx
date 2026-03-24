'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuthStore } from '@/lib/store'

export default function AdminJobsPage() {
  const router = useRouter()
  const { isAuthenticated, user } = useAuthStore()
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!isAuthenticated || user?.role !== 'admin') {
      router.push('/login')
    } else {
      setLoading(false)
    }
  }, [isAuthenticated, user, router])

  if (loading) {
    return <div className="flex justify-center items-center min-h-screen">Loading...</div>
  }

  return <JobsContent />
}

function JobsContent() {
  return (
    <div className="container mx-auto px-4 py-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Job Management</h1>
        <p className="text-gray-600 mt-2">Monitor and moderate all job postings</p>
      </div>

      {/* Coming Soon */}
      <div className="bg-white rounded-lg shadow-md p-12 text-center">
        <div className="text-6xl mb-4">💼</div>
        <h2 className="text-2xl font-semibold text-gray-900 mb-2">Job Management Coming Soon</h2>
        <p className="text-gray-600 mb-6">
          This section will allow you to view, moderate, and manage all job postings on the platform.
        </p>
        <div className="text-left max-w-md mx-auto bg-gray-50 rounded-lg p-6">
          <h3 className="font-semibold text-gray-900 mb-3">Planned Features:</h3>
          <ul className="space-y-2 text-gray-700">
            <li className="flex items-start gap-2">
              <span className="text-green-600">✓</span>
              <span>View all jobs across the platform</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-green-600">✓</span>
              <span>Approve or reject job postings</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-green-600">✓</span>
              <span>Flag inappropriate content</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-green-600">✓</span>
              <span>Edit or remove jobs</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-green-600">✓</span>
              <span>View job analytics and trends</span>
            </li>
          </ul>
        </div>
      </div>
    </div>
  )
}
