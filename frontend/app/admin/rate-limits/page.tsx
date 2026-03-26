'use client'

import { useEffect, useState, useCallback } from 'react'
import { getRateLimitStats, getViolators, clearUserViolations, getUserViolations, type RateLimitStats } from '@/lib/api/admin'

export default function AdminRateLimitsPage() {
  const [stats, setStats] = useState<RateLimitStats | null>(null)
  const [violators, setViolators] = useState<string[]>([])
  const [timeWindow, setTimeWindow] = useState(24)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [clearing, setClearing] = useState<string | null>(null)
  const [detailsUser, setDetailsUser] = useState<string | null>(null)
  const [details, setDetails] = useState<any | null>(null)
  const [detailsLoading, setDetailsLoading] = useState(false)

  const load = useCallback(async () => {
    try {
      setLoading(true); setError(null)
      const [s, v] = await Promise.all([getRateLimitStats(timeWindow, 10), getViolators(timeWindow)])
      setStats(s); setViolators(v.violators)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load rate limit data')
    } finally { setLoading(false) }
  }, [timeWindow])

  useEffect(() => { load() }, [load])

  const handleClear = async (userId: string) => {
    setClearing(userId)
    try {
      await clearUserViolations(userId)
      await load()
    } catch { alert('Failed to clear violations') }
    finally { setClearing(null) }
  }

  const handleViewDetails = async (userId: string) => {
    setDetailsUser(userId)
    setDetailsLoading(true)
    setDetails(null)
    try {
      const res = await getUserViolations(userId)
      setDetails(res)
    } catch { setDetails(null) }
    finally { setDetailsLoading(false) }
  }

  return (
    <div className="p-8">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900">Rate Limit Monitor</h1>
        <p className="text-gray-500 mt-1">Monitor and manage API rate limit violations</p>
      </div>

      {/* Time Window */}
      <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-4 mb-6 flex items-center gap-4">
        <label className="text-sm font-medium text-gray-700">Time Window:</label>
        <select
          value={timeWindow}
          onChange={e => { setTimeWindow(Number(e.target.value)) }}
          className="px-4 py-2 border border-gray-200 rounded-lg text-sm outline-none"
        >
          <option value={1}>Last Hour</option>
          <option value={24}>Last 24 Hours</option>
          <option value={168}>Last Week</option>
        </select>
        <button onClick={load} className="px-4 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700">Refresh</button>
      </div>

      {error && <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-4 text-red-700 text-sm">{error}</div>}

      {loading ? (
        <div className="text-center py-12 text-gray-400">Loading...</div>
      ) : (
        <>
          {/* Stats Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
            <div className="bg-red-50 border border-red-200 rounded-xl p-5">
              <p className="text-sm text-red-600 font-medium">Total Violators</p>
              <p className="text-4xl font-bold text-red-700 mt-1">{stats?.total_violators ?? 0}</p>
              <p className="text-xs text-red-500 mt-1">in last {timeWindow}h</p>
            </div>
            <div className="bg-white border border-gray-100 rounded-xl p-5 col-span-2">
              <p className="text-sm font-semibold text-gray-700 mb-3">Top 5 Violators</p>
              {stats?.top_violators?.length ? (
                <div className="space-y-2">
                  {stats.top_violators.slice(0, 5).map((v, i) => (
                    <div key={v.user_id} className="flex items-center justify-between">
                      <span className="text-xs font-mono text-gray-500">#{i+1} {v.user_id.substring(0, 30)}...</span>
                      <span className="text-xs font-bold text-red-600">{v.violation_count} violations</span>
                    </div>
                  ))}
                </div>
              ) : <p className="text-gray-400 text-sm">No violations</p>}
            </div>
          </div>

          {/* All Violators */}
          <div className="bg-white rounded-xl border border-gray-100 shadow-sm overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-100">
              <h2 className="font-semibold text-gray-900">All Violators ({violators.length})</h2>
            </div>
            {violators.length === 0 ? (
              <div className="py-12 text-center text-gray-400">
                <div className="text-4xl mb-2">✅</div>
                <p>No violations in the selected time window</p>
              </div>
            ) : (
              <table className="w-full text-sm">
                <thead className="bg-gray-50 border-b border-gray-100">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase">User ID / IP</th>
                    <th className="px-6 py-3 text-right text-xs font-semibold text-gray-500 uppercase">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-50">
                  {violators.map(uid => (
                    <tr key={uid} className="hover:bg-gray-50">
                      <td className="px-6 py-3 font-mono text-gray-700 text-xs">{uid}</td>
                      <td className="px-6 py-3 text-right">
                        <div className="flex gap-2 justify-end">
                          <button
                            onClick={() => handleViewDetails(uid)}
                            className="px-3 py-1 text-xs bg-blue-100 text-blue-700 hover:bg-blue-200 rounded-lg font-medium"
                          >View Details</button>
                          <button
                            onClick={() => handleClear(uid)}
                            disabled={clearing === uid}
                            className="px-3 py-1 text-xs bg-red-100 text-red-700 hover:bg-red-200 rounded-lg font-medium disabled:opacity-50"
                          >{clearing === uid ? 'Clearing...' : 'Clear'}</button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </>
      )}

      {/* Details Modal */}
      {detailsUser && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-2xl max-w-2xl w-full max-h-[80vh] flex flex-col">
            <div className="px-6 py-4 border-b border-gray-100 flex justify-between items-center">
              <h3 className="font-semibold text-gray-900 text-sm font-mono">{detailsUser}</h3>
              <button onClick={() => { setDetailsUser(null); setDetails(null) }} className="text-gray-400 hover:text-gray-600 text-xl">×</button>
            </div>
            <div className="overflow-auto p-6">
              {detailsLoading ? (
                <p className="text-gray-400 text-center py-8">Loading...</p>
              ) : details?.violations?.length ? (
                <table className="w-full text-xs">
                  <thead>
                    <tr className="border-b border-gray-100">
                      <th className="text-left py-2 text-gray-500">Time</th>
                      <th className="text-left py-2 text-gray-500">Path</th>
                      <th className="text-center py-2 text-gray-500">Count</th>
                      <th className="text-center py-2 text-gray-500">Limit</th>
                    </tr>
                  </thead>
                  <tbody>
                    {details.violations.map((v: any, i: number) => (
                      <tr key={i} className="border-b border-gray-50">
                        <td className="py-2 text-gray-600">{new Date(v.timestamp).toLocaleString()}</td>
                        <td className="py-2 font-mono text-gray-700">{v.path}</td>
                        <td className="py-2 text-center font-bold text-red-600">{v.count}</td>
                        <td className="py-2 text-center text-gray-500">{v.limit}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              ) : (
                <p className="text-gray-400 text-center py-8">No violation details found</p>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
