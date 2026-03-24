'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuthStore } from '@/lib/store'
import { getPlatformStats, getRateLimitStats, type PlatformStats, type RateLimitStats } from '@/lib/api/admin'

export default function AdminDashboardPage() {
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

  return <DashboardContent />
}

function DashboardContent() {
  const [stats, setStats] = useState<PlatformStats | null>(null)
  const [rateLimitStats, setRateLimitStats] = useState<RateLimitStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadDashboardData()
  }, [])

  const loadDashboardData = async () => {
    try {
      setLoading(true)
      setError(null)
      
      // For now, use mock data since backend endpoints may not exist yet
      // TODO: Replace with actual API calls when backend is ready
      const mockStats: PlatformStats = {
        total_users: 0,
        total_employers: 0,
        total_job_seekers: 0,
        total_jobs: 0,
        total_applications: 0,
        active_jobs: 0,
        jobs_posted_today: 0,
        applications_today: 0
      }
      
      const mockRateLimitStats: RateLimitStats = {
        total_violators: 0,
        time_window_hours: 24,
        top_violators: []
      }
      
      setStats(mockStats)
      setRateLimitStats(mockRateLimitStats)
      
      // Uncomment when backend is ready:
      // const [statsData, rateLimitData] = await Promise.all([
      //   getPlatformStats(),
      //   getRateLimitStats(24, 10)
      // ])
      // setStats(statsData)
      // setRateLimitStats(rateLimitData)
      
    } catch (err: any) {
      console.error('Error loading dashboard data:', err)
      setError(err.response?.data?.detail || 'Failed to load dashboard data')
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
            <p className="mt-4 text-gray-600">Loading dashboard...</p>
          </div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="bg-red-50 border border-red-200 rounded-lg p-6">
          <h3 className="text-red-800 font-semibold mb-2">Error Loading Dashboard</h3>
          <p className="text-red-600">{error}</p>
          <button
            onClick={loadDashboardData}
            className="mt-4 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
          >
            Retry
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Admin Dashboard</h1>
        <p className="text-gray-600 mt-2">Platform overview and management</p>
      </div>

      {/* Quick Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <StatCard
          title="Total Users"
          value={stats?.total_users || 0}
          icon="👥"
          color="blue"
        />
        <StatCard
          title="Total Jobs"
          value={stats?.total_jobs || 0}
          subtitle={`${stats?.active_jobs || 0} active`}
          icon="💼"
          color="green"
        />
        <StatCard
          title="Applications"
          value={stats?.total_applications || 0}
          subtitle={`${stats?.applications_today || 0} today`}
          icon="📝"
          color="purple"
        />
        <StatCard
          title="Rate Limit Issues"
          value={rateLimitStats?.total_violators || 0}
          subtitle="Last 24 hours"
          icon="⚠️"
          color="red"
        />
      </div>

      {/* User Breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold mb-4">User Breakdown</h2>
          <div className="space-y-4">
            <UserTypeRow
              label="Employers"
              count={stats?.total_employers || 0}
              total={stats?.total_users || 0}
              color="blue"
            />
            <UserTypeRow
              label="Job Seekers"
              count={stats?.total_job_seekers || 0}
              total={stats?.total_users || 0}
              color="green"
            />
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold mb-4">Today's Activity</h2>
          <div className="space-y-4">
            <ActivityRow
              label="Jobs Posted"
              count={stats?.jobs_posted_today || 0}
              icon="📋"
            />
            <ActivityRow
              label="Applications Submitted"
              count={stats?.applications_today || 0}
              icon="✉️"
            />
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-xl font-semibold mb-4">Quick Actions</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <ActionButton
            label="Manage Users"
            description="View and manage all users"
            icon="👥"
            href="/admin/users"
          />
          <ActionButton
            label="Monitor Jobs"
            description="Review and moderate jobs"
            icon="💼"
            href="/admin/jobs"
          />
          <ActionButton
            label="Rate Limits"
            description="View rate limit violations"
            icon="⚠️"
            href="/admin/rate-limits"
          />
        </div>
      </div>
    </div>
  )
}

// Stat Card Component
function StatCard({
  title,
  value,
  subtitle,
  icon,
  color
}: {
  title: string
  value: number
  subtitle?: string
  icon: string
  color: 'blue' | 'green' | 'purple' | 'red'
}) {
  const colorClasses = {
    blue: 'bg-blue-50 border-blue-200',
    green: 'bg-green-50 border-green-200',
    purple: 'bg-purple-50 border-purple-200',
    red: 'bg-red-50 border-red-200'
  }

  return (
    <div className={`${colorClasses[color]} border rounded-lg p-6`}>
      <div className="flex items-center justify-between mb-2">
        <span className="text-2xl">{icon}</span>
        <span className="text-3xl font-bold text-gray-900">{value.toLocaleString()}</span>
      </div>
      <h3 className="text-gray-700 font-medium">{title}</h3>
      {subtitle && <p className="text-sm text-gray-500 mt-1">{subtitle}</p>}
    </div>
  )
}

// User Type Row Component
function UserTypeRow({
  label,
  count,
  total,
  color
}: {
  label: string
  count: number
  total: number
  color: 'blue' | 'green'
}) {
  const percentage = total > 0 ? Math.round((count / total) * 100) : 0
  const colorClasses = {
    blue: 'bg-blue-600',
    green: 'bg-green-600'
  }

  return (
    <div>
      <div className="flex justify-between mb-2">
        <span className="text-gray-700">{label}</span>
        <span className="font-semibold text-gray-900">{count.toLocaleString()}</span>
      </div>
      <div className="w-full bg-gray-200 rounded-full h-2">
        <div
          className={`${colorClasses[color]} h-2 rounded-full transition-all`}
          style={{ width: `${percentage}%` }}
        ></div>
      </div>
      <p className="text-sm text-gray-500 mt-1">{percentage}% of total users</p>
    </div>
  )
}

// Activity Row Component
function ActivityRow({ label, count, icon }: { label: string; count: number; icon: string }) {
  return (
    <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
      <div className="flex items-center gap-3">
        <span className="text-2xl">{icon}</span>
        <span className="text-gray-700">{label}</span>
      </div>
      <span className="text-2xl font-bold text-gray-900">{count.toLocaleString()}</span>
    </div>
  )
}

// Action Button Component
function ActionButton({
  label,
  description,
  icon,
  href
}: {
  label: string
  description: string
  icon: string
  href: string
}) {
  const router = useRouter()

  return (
    <button
      onClick={() => router.push(href)}
      className="text-left p-4 border border-gray-200 rounded-lg hover:border-blue-500 hover:shadow-md transition-all"
    >
      <div className="text-3xl mb-2">{icon}</div>
      <h3 className="font-semibold text-gray-900 mb-1">{label}</h3>
      <p className="text-sm text-gray-600">{description}</p>
    </button>
  )
}
