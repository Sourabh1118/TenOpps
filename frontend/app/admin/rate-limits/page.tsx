'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuthStore } from '@/lib/store'
import { getRateLimitStats, getViolators, type RateLimitStats } from '@/lib/api/admin'

export default function AdminRateLimitsPage() {
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

  return <RateLimitsContent />
}

function RateLimitsContent() {
  const [stats, setStats] = useState<RateLimitStats | null>(null)
  const [violators, setViolators] = useState<string[]>([])
  const [timeWindow, setTimeWindow] = useState(24)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadRateLimitData()
  }, [timeWindow])

  const loadRateLimitData = async () => {
    try {
      setLoading(true)
      setError(null)
      
      const [statsData, violatorsData] = await Promise.all([
        getRateLimitStats(timeWindow, 10),
        getViolators(timeWindow)
      ])
      
      setStats(statsData)
      setViolators(violatorsData.violators)
    } catch (err: any) {
      console.error('Error loading rate limit data:', err)
      setError(err.response?.data?.detail || 'Failed to load rate limit data')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="flex justify-center items-center min-h-[400px]">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
            <p className="mt-4 text-gray-600">Loading rate limit data...</p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Rate Limit Monitoring</h1>
        <p className="text-gray-600 mt-2">Monitor and manage rate limit violations</p>
      </div>

      {/* Time Window Selector */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Time Window
        </label>
        <select
          value={timeWindow}
          onChange={(e) => setTimeWindow(Number(e.target.value))}
          className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        >
          <option value={1}>Last Hour</option>
          <option value={24}>Last 24 Hours</option>
          <option value={168}>Last Week</option>
        </select>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-6 mb-6">
          <h3 className="text-red-800 font-semibold mb-2">Error</h3>
          <p className="text-red-600">{error}</p>
          <button
            onClick={loadRateLimitData}
            className="mt-4 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
          >
            Retry
          </button>
        </div>
      )}

      {/* Stats Overview */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold mb-4">Overview</h2>
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <span className="text-gray-700">Total Violators</span>
              <span className="text-2xl font-bold text-red-600">
                {stats?.total_violators || 0}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-700">Time Window</span>
              <span className="text-lg font-semibold text-gray-900">
                {stats?.time_window_hours || 0} hours
              </span>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold mb-4">Top Violators</h2>
          {stats?.top_violators && stats.top_violators.length > 0 ? (
            <div className="space-y-2">
              {stats.top_violators.slice(0, 5).map((violator, index) => (
                <div key={violator.user_id} className="flex justify-between items-center p-2 bg-gray-50 rounded">
                  <span className="text-sm text-gray-700 font-mono truncate">
                    {index + 1}. {violator.user_id.substring(0, 20)}...
                  </span>
                  <span className="text-sm font-semibold text-red-600">
                    {violator.violation_count} violations
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-gray-500 text-center py-4">No violations in this time window</p>
          )}
        </div>
      </div>

      {/* All Violators List */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-xl font-semibold mb-4">All Violators</h2>
        {violators.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {violators.map((userId) => (
              <div key={userId} className="p-4 border border-gray-200 rounded-lg">
                <p className="text-sm font-mono text-gray-700 truncate">{userId}</p>
                <button className="mt-2 text-sm text-blue-600 hover:text-blue-800">
                  View Details
                </button>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-12">
            <div className="text-4xl mb-2">✅</div>
            <p className="text-gray-500">No rate limit violations in the selected time window</p>
          </div>
        )}
      </div>
    </div>
  )
}
