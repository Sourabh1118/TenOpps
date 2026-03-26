'use client'

import { useEffect, useState, useCallback } from 'react'
import { getUsers, deleteUser, updateUserStatus, type UserListItem } from '@/lib/api/admin'

const ROLES = ['all', 'admin', 'employer', 'job_seeker'] as const
type RoleFilter = typeof ROLES[number]

export default function AdminUsersPage() {
  const [users, setUsers] = useState<UserListItem[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [role, setRole] = useState<RoleFilter>('all')
  const [search, setSearch] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [actionLoading, setActionLoading] = useState<string | null>(null)
  const [confirmDelete, setConfirmDelete] = useState<UserListItem | null>(null)
  const limit = 50

  const load = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      const params: any = { page, limit }
      if (role !== 'all') params.role = role
      const res = await getUsers(params)
      setUsers(res.users)
      setTotal(res.total)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load users')
    } finally {
      setLoading(false)
    }
  }, [page, role])

  useEffect(() => { load() }, [load])

  const filtered = users.filter(u =>
    u.email.toLowerCase().includes(search.toLowerCase()) ||
    (u.full_name ?? '').toLowerCase().includes(search.toLowerCase()) ||
    (u.company_name ?? '').toLowerCase().includes(search.toLowerCase())
  )

  const handleBan = async (u: UserListItem) => {
    const newStatus = (u as any).status === 'banned' ? 'active' : 'banned'
    setActionLoading(u.id)
    try {
      await updateUserStatus(u.id, newStatus as any)
      await load()
    } catch { alert('Action failed') }
    finally { setActionLoading(null) }
  }

  const handleDelete = async (u: UserListItem) => {
    setActionLoading(u.id)
    try {
      await deleteUser(u.id)
      setConfirmDelete(null)
      await load()
    } catch { alert('Delete failed') }
    finally { setActionLoading(null) }
  }

  const roleBadge = (r: string) => {
    const map: Record<string, string> = { admin: 'bg-purple-100 text-purple-800', employer: 'bg-blue-100 text-blue-800', job_seeker: 'bg-green-100 text-green-800' }
    return map[r] || 'bg-gray-100 text-gray-800'
  }

  return (
    <div className="p-8">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900">User Management</h1>
        <p className="text-gray-500 mt-1">Total: {total.toLocaleString()} users</p>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-4 mb-6 flex flex-wrap gap-4">
        <input
          type="text"
          placeholder="Search by email or name..."
          value={search}
          onChange={e => setSearch(e.target.value)}
          className="flex-1 min-w-[200px] px-4 py-2 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
        />
        <select
          value={role}
          onChange={e => { setRole(e.target.value as RoleFilter); setPage(1) }}
          className="px-4 py-2 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 outline-none"
        >
          <option value="all">All Roles</option>
          <option value="admin">Admins</option>
          <option value="employer">Employers</option>
          <option value="job_seeker">Job Seekers</option>
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
                <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">User</th>
                <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Role</th>
                <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Company / Name</th>
                <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Joined</th>
                <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {loading ? (
                <tr><td colSpan={5} className="py-12 text-center text-gray-400">Loading...</td></tr>
              ) : filtered.length === 0 ? (
                <tr><td colSpan={5} className="py-12 text-center text-gray-400">No users found</td></tr>
              ) : (
                filtered.map(u => (
                  <tr key={u.id} className="hover:bg-gray-50 transition-colors">
                    <td className="px-6 py-4 font-medium text-gray-900">{u.email}</td>
                    <td className="px-6 py-4">
                      <span className={`px-2 py-1 rounded-full text-xs font-semibold ${roleBadge(u.role)}`}>
                        {u.role.replace('_', ' ')}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-gray-600">{u.company_name ?? u.full_name ?? '—'}</td>
                    <td className="px-6 py-4 text-gray-500">{new Date(u.created_at).toLocaleDateString()}</td>
                    <td className="px-6 py-4">
                      <div className="flex gap-2">
                        {u.role !== 'admin' && (
                          <>
                            <button
                              onClick={() => handleBan(u)}
                              disabled={actionLoading === u.id}
                              className="px-3 py-1 text-xs bg-yellow-100 text-yellow-800 hover:bg-yellow-200 rounded-lg font-medium disabled:opacity-50"
                            >
                              {(u as any).status === 'banned' ? 'Unban' : 'Ban'}
                            </button>
                            <button
                              onClick={() => setConfirmDelete(u)}
                              disabled={actionLoading === u.id}
                              className="px-3 py-1 text-xs bg-red-100 text-red-700 hover:bg-red-200 rounded-lg font-medium disabled:opacity-50"
                            >
                              Delete
                            </button>
                          </>
                        )}
                      </div>
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

      {/* Delete Confirmation Modal */}
      {confirmDelete && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-2xl p-6 max-w-sm w-full mx-4 shadow-2xl">
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Delete User?</h3>
            <p className="text-gray-600 text-sm mb-4">Are you sure you want to permanently delete <strong>{confirmDelete.email}</strong>? This cannot be undone.</p>
            <div className="flex gap-3">
              <button onClick={() => setConfirmDelete(null)} className="flex-1 py-2 border border-gray-200 rounded-lg text-sm hover:bg-gray-50">Cancel</button>
              <button onClick={() => handleDelete(confirmDelete)} disabled={!!actionLoading} className="flex-1 py-2 bg-red-600 text-white rounded-lg text-sm hover:bg-red-700 disabled:opacity-50">
                {actionLoading ? 'Deleting...' : 'Delete'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
