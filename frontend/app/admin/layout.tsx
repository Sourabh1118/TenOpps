'use client'

import { useEffect, useState } from 'react'
import { useRouter, usePathname } from 'next/navigation'
import Link from 'next/link'
import { useAuthStore } from '@/lib/store'

const navItems = [
  { href: '/admin/dashboard', label: 'Dashboard', icon: '📊' },
  { href: '/admin/users',     label: 'Users',     icon: '👥' },
  { href: '/admin/jobs',      label: 'Jobs',      icon: '💼' },
  { href: '/admin/scraping',  label: 'Scraping',  icon: '🤖' },
  { href: '/admin/rate-limits', label: 'Rate Limits', icon: '⚠️' },
]

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter()
  const pathname = usePathname()
  const { isAuthenticated, user, clearAuth } = useAuthStore()
  const [checking, setChecking] = useState(true)

  useEffect(() => {
    if (!isAuthenticated || user?.role !== 'admin') {
      router.push('/login')
    } else {
      setChecking(false)
    }
  }, [isAuthenticated, user, router])

  if (checking) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto" />
          <p className="mt-4 text-gray-600">Checking access...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="flex min-h-screen bg-gray-50">
      {/* Sidebar */}
      <aside className="w-64 bg-gray-900 text-white flex flex-col">
        {/* Brand */}
        <div className="px-6 py-5 border-b border-gray-700">
          <h1 className="text-xl font-bold text-white">TenOpps Admin</h1>
          <p className="text-xs text-gray-400 mt-1">Platform Management</p>
        </div>

        {/* Navigation */}
        <nav className="flex-1 px-4 py-6 space-y-1">
          {navItems.map((item) => {
            const isActive = pathname === item.href || pathname?.startsWith(item.href + '/')
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-blue-600 text-white'
                    : 'text-gray-300 hover:bg-gray-800 hover:text-white'
                }`}
              >
                <span className="text-base">{item.icon}</span>
                {item.label}
              </Link>
            )
          })}
        </nav>

        {/* Admin Info + Logout */}
        <div className="px-4 py-4 border-t border-gray-700">
          <div className="px-4 py-2 mb-2 text-xs text-gray-400">
            <p className="font-medium text-gray-300 truncate">{user?.email}</p>
            <p className="capitalize text-gray-500">{user?.role}</p>
          </div>
          <button
            onClick={() => { clearAuth(); router.push('/login') }}
            className="w-full flex items-center gap-2 px-4 py-2 text-sm text-gray-300 hover:text-white hover:bg-gray-800 rounded-lg transition-colors"
          >
            <span>🚪</span> Logout
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-auto">
        {children}
      </main>
    </div>
  )
}
