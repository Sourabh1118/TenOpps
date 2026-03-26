'use client'

import { useEffect, useState, useCallback } from 'react'
import { getAdminJobs, updateJobStatus, type AdminJobItem } from '@/lib/api/admin'

const SOURCES = ['all', 'linkedin', 'indeed', 'naukri', 'monster']

export default function AdminJobsPage() {
  const [jobs, setJobs] = useState<AdminJobItem[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('all')
  const [sourceFilter, setSourceFilter] = useState('all')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [actionLoading, setActionLoading] = useState<string | null>(null)
  const limit = 50

  const load = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      const params: any = { page, limit }
      if (search) params.search = search
      if (statusFilter !== 'all') params.status = statusFilter
      if (sourceFilter !== 'all') params.source = sourceFilter
      const res = await getAdminJobs(params)
      setJobs(res.jobs)
      setTotal(res.total)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load jobs')
    } finally {
      setLoading(false)
    }
  }, [page, search, statusFilter, sourceFilter])

  useEffect(() => { load() }, [load])

  const handleStatusToggle = async (job: AdminJobItem) => {
    const newStatus = job.status === 'active' ? 'expired' : 'active'
    setActionLoading(job.id)
    try {
      await updateJobStatus(job.id, newStatus as any)
      await load()
    } catch { alert('Failed to update job status') }
    finally { setActionLoading(null) }
  }

  const statusBadge = (s: string) => {
    const map: Record<string, string> = { active: 'bg-green-100 text-green-800', expired: 'bg-gray-100 text-gray-600', pending: 'bg-yellow-100 text-yellow-800' }
    return map[s] || 'bg-gray-100 text-gray-600'
  }

  const sourceBadge = (s: string | null) => {
    const map: Record<string, string> = { linkedin: 'bg-blue-100 text-blue-800', indeed: 'bg-indigo-100 text-indigo-800', naukri: 'bg-orange-100 text-orange-800', monster: 'bg-red-100 text-red-800' }
    return s ? (map[s] || 'bg-gray-100 text-gray-600') : 'bg-gray-100 text-gray-600'
  }

  return (
    <div className="p-8">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900">Job Management</h1>
        <p className="text-gray-500 mt-1">Total: {total.toLocaleString()} jobs</p>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-4 mb-6 flex flex-wrap gap-3">
        <input
          type="text"
          placeholder="Search title or company..."
          value={search}
          onChange={e => { setSearch(e.target.value); setPage(1) }}
          className="flex-1 min-w-[180px] px-4 py-2 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 outline-none"
        />
        <select
          value={statusFilter}
          onChange={e => { setStatusFilter(e.target.value); setPage(1) }}
          className="px-4 py-2 border border-gray-200 rounded-lg text-sm outline-none"
        >
          <option value="all">All Status</option>
          <option value="active">Active</option>
          <option value="expired">Expired</option>
        </select>
        <select
          value={sourceFilter}
          onChange={e => { setSourceFilter(e.target.value); setPage(1) }}
          className="px-4 py-2 border border-gray-200 rounded-lg text-sm outline-none"
        >
          {SOURCES.map(s => <option key={s} value={s}>{s === 'all' ? 'All Sources' : s.charAt(0).toUpperCase() + s.slice(1)}</option>)}
        </select>
        <button onClick={load} className="px-4 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700">Refresh</button>
      </div>

      {error && <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-4 text-red-700 text-sm">{error}</div>}

      {/* Table */}
      <div className="bg-white rounded-xl border border-gray-100 shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b border-gray-100">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Title</th>
                <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Company</th>
                <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Source</th>
                <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Status</th>
                <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Posted</th>
                <th className="px-6 py-3 text-center text-xs font-semibold text-gray-500 uppercase tracking-wider">Apps</th>
                <th className="px-6 py-3 text-center text-xs font-semibold text-gray-500 uppercase tracking-wider">Views</th>
                <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {loading ? (
                <tr><td colSpan={8} className="py-12 text-center text-gray-400">Loading...</td></tr>
              ) : jobs.length === 0 ? (
                <tr><td colSpan={8} className="py-12 text-center text-gray-400">No jobs found</td></tr>
              ) : (
                jobs.map(j => (
                  <tr key={j.id} className="hover:bg-gray-50 transition-colors">
                    <td className="px-6 py-4 font-medium text-gray-900 max-w-xs truncate">{j.title}</td>
                    <td className="px-6 py-4 text-gray-600">{j.company}</td>
                    <td className="px-6 py-4">
                      {j.source_platform ? (
                        <span className={`px-2 py-1 rounded-full text-xs font-semibold ${sourceBadge(j.source_platform)}`}>{j.source_platform}</span>
                      ) : <span className="text-gray-400 text-xs">{j.source_type}</span>}
                    </td>
                    <td className="px-6 py-4">
                      <span className={`px-2 py-1 rounded-full text-xs font-semibold ${statusBadge(j.status)}`}>{j.status}</span>
                    </td>
                    <td className="px-6 py-4 text-gray-500">{j.posted_at ? new Date(j.posted_at).toLocaleDateString() : '—'}</td>
                    <td className="px-6 py-4 text-center text-gray-700">{j.application_count}</td>
                    <td className="px-6 py-4 text-center text-gray-700">{j.view_count}</td>
                    <td className="px-6 py-4">
                      <button
                        onClick={() => handleStatusToggle(j)}
                        disabled={actionLoading === j.id}
                        className={`px-3 py-1 text-xs rounded-lg font-medium disabled:opacity-50 ${j.status === 'active' ? 'bg-red-100 text-red-700 hover:bg-red-200' : 'bg-green-100 text-green-700 hover:bg-green-200'}`}
                      >
                        {j.status === 'active' ? 'Deactivate' : 'Activate'}
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {total > limit && (
          <div className="px-6 py-4 border-t border-gray-100 flex items-center justify-between text-sm text-gray-600">
            <span>Showing {((page - 1) * limit) + 1}–{Math.min(page * limit, total)} of {total}</span>
            <div className="flex gap-2">
              <button onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1} className="px-3 py-1 border border-gray-200 rounded hover:bg-gray-50 disabled:opacity-40">Previous</button>
              <button onClick={() => setPage(p => p + 1)} disabled={page * limit >= total} className="px-3 py-1 border border-gray-200 rounded hover:bg-gray-50 disabled:opacity-40">Next</button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
