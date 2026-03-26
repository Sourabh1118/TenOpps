'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { getPlatformStats, getRateLimitStats, type PlatformStats, type RateLimitStats } from '@/lib/api/admin'

export default function AdminDashboardPage() {
  const router = useRouter()
  const [stats, setStats] = useState<PlatformStats | null>(null)
  const [rateLimitStats, setRateLimitStats] = useState<RateLimitStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      setLoading(true)
      setError(null)
      const [s, r] = await Promise.all([getPlatformStats(), getRateLimitStats(24, 10)])
      setStats(s)
      setRateLimitStats(r)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load dashboard data')
    } finally {
      setLoading(false)
    }
  }

  if (loading) return <LoadingSpinner label="Loading dashboard..." />
  if (error) return <ErrorBlock message={error} onRetry={loadData} />

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
        <p className="text-gray-500 mt-1">Platform overview</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <StatCard label="Total Users" value={stats?.total_users ?? 0} icon="👥" color="blue" />
        <StatCard label="Active Jobs" value={stats?.active_jobs ?? 0} sub={`${stats?.total_jobs ?? 0} total`} icon="💼" color="green" />
        <StatCard label="Applications" value={stats?.total_applications ?? 0} sub={`${stats?.applications_today ?? 0} today`} icon="📝" color="purple" />
        <StatCard label="Rate Violations" value={rateLimitStats?.total_violators ?? 0} sub="Last 24h" icon="⚠️" color="red" />
      </div>

      {/* Two column row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        {/* User Breakdown */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">User Breakdown</h2>
          <UserBar label="Employers" count={stats?.total_employers ?? 0} total={stats?.total_users ?? 1} color="bg-blue-500" />
          <UserBar label="Job Seekers" count={stats?.total_job_seekers ?? 0} total={stats?.total_users ?? 1} color="bg-green-500" />
        </div>

        {/* Today's Activity */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Today's Activity</h2>
          <ActivityRow icon="📋" label="Jobs Posted" count={stats?.jobs_posted_today ?? 0} />
          <ActivityRow icon="✉️" label="Applications Submitted" count={stats?.applications_today ?? 0} />
        </div>
      </div>

      {/* Top Rate Violators */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Top Rate-Limit Violators (24h)</h2>
        {rateLimitStats?.top_violators && rateLimitStats.top_violators.length > 0 ? (
          <div className="space-y-2">
            {rateLimitStats.top_violators.map((v, i) => (
              <div key={v.user_id} className="flex items-center justify-between py-2 border-b border-gray-50 last:border-0">
                <span className="text-sm font-mono text-gray-600">#{i + 1} {v.user_id}</span>
                <span className="text-sm font-bold text-red-600">{v.violation_count} violations</span>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-gray-400 text-center py-6">✅ No violations in the last 24 hours</p>
        )}
      </div>
    </div>
  )
}

function StatCard({ label, value, sub, icon, color }: { label: string; value: number; sub?: string; icon: string; color: 'blue' | 'green' | 'purple' | 'red' }) {
  const bg = { blue: 'bg-blue-50 border-blue-200', green: 'bg-green-50 border-green-200', purple: 'bg-purple-50 border-purple-200', red: 'bg-red-50 border-red-200' }
  const text = { blue: 'text-blue-700', green: 'text-green-700', purple: 'text-purple-700', red: 'text-red-700' }
  return (
    <div className={`${bg[color]} border rounded-xl p-5`}>
      <div className="flex justify-between items-start">
        <span className="text-2xl">{icon}</span>
        <span className={`text-3xl font-bold ${text[color]}`}>{value.toLocaleString()}</span>
      </div>
      <p className="text-gray-700 font-medium mt-3">{label}</p>
      {sub && <p className="text-xs text-gray-500 mt-1">{sub}</p>}
    </div>
  )
}

function UserBar({ label, count, total, color }: { label: string; count: number; total: number; color: string }) {
  const pct = total > 0 ? Math.round((count / total) * 100) : 0
  return (
    <div className="mb-4">
      <div className="flex justify-between text-sm mb-1">
        <span className="text-gray-600">{label}</span>
        <span className="font-semibold">{count.toLocaleString()} ({pct}%)</span>
      </div>
      <div className="w-full bg-gray-100 rounded-full h-2">
        <div className={`${color} h-2 rounded-full transition-all`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  )
}

function ActivityRow({ icon, label, count }: { icon: string; label: string; count: number }) {
  return (
    <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg mb-2">
      <div className="flex items-center gap-2 text-gray-700">
        <span>{icon}</span><span className="text-sm">{label}</span>
      </div>
      <span className="text-xl font-bold text-gray-900">{count.toLocaleString()}</span>
    </div>
  )
}

export function LoadingSpinner({ label }: { label: string }) {
  return (
    <div className="flex justify-center items-center min-h-[400px]">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto" />
        <p className="mt-4 text-gray-500">{label}</p>
      </div>
    </div>
  )
}

export function ErrorBlock({ message, onRetry }: { message: string; onRetry: () => void }) {
  return (
    <div className="p-8">
      <div className="bg-red-50 border border-red-200 rounded-xl p-6">
        <h3 className="font-semibold text-red-800 mb-1">Error</h3>
        <p className="text-red-600 text-sm">{message}</p>
        <button onClick={onRetry} className="mt-3 px-4 py-2 bg-red-600 text-white text-sm rounded-lg hover:bg-red-700">Retry</button>
      </div>
    </div>
  )
}
