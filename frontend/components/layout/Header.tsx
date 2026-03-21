'use client'

import { useState } from 'react'
import Link from 'next/link'
import { useAuthStore } from '@/lib/store'

export function Header() {
  const { isAuthenticated, user, clearAuth } = useAuthStore()
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

  const handleLogout = () => {
    clearAuth()
    setMobileMenuOpen(false)
  }

  const closeMobileMenu = () => {
    setMobileMenuOpen(false)
  }

  return (
    <header className="border-b bg-white sticky top-0 z-50 shadow-sm">
      <div className="container mx-auto px-4 py-4">
        <div className="flex items-center justify-between">
          {/* Logo */}
          <Link href="/" className="text-2xl font-bold text-blue-600">
            JobHub
          </Link>

          {/* Desktop Navigation */}
          <nav className="hidden md:flex items-center gap-6">
            <Link href="/" className="hover:text-blue-600 transition-colors">
              Home
            </Link>
            <Link href="/jobs" className="hover:text-blue-600 transition-colors">
              Search Jobs
            </Link>
            
            {isAuthenticated ? (
              <>
                {user?.role === 'employer' && (
                  <>
                    <Link href="/employer/post-job" className="hover:text-blue-600 transition-colors">
                      Post Job
                    </Link>
                    <Link href="/employer/dashboard" className="hover:text-blue-600 transition-colors">
                      Dashboard
                    </Link>
                  </>
                )}
                {user?.role === 'job_seeker' && (
                  <Link href="/applications" className="hover:text-blue-600 transition-colors">
                    My Applications
                  </Link>
                )}
                <button
                  onClick={handleLogout}
                  className="px-4 py-2 bg-gray-200 rounded-lg hover:bg-gray-300 transition-colors"
                >
                  Logout
                </button>
              </>
            ) : (
              <>
                <Link href="/login" className="hover:text-blue-600 transition-colors">
                  Login
                </Link>
                <Link
                  href="/register"
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                >
                  Sign Up
                </Link>
              </>
            )}
          </nav>

          {/* Mobile Menu Button */}
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="md:hidden p-2 rounded-lg hover:bg-gray-100 transition-colors"
            aria-label="Toggle menu"
          >
            {mobileMenuOpen ? (
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            ) : (
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            )}
          </button>
        </div>

        {/* Mobile Navigation */}
        {mobileMenuOpen && (
          <nav className="md:hidden mt-4 pb-4 border-t pt-4">
            <div className="flex flex-col gap-4">
              <Link 
                href="/" 
                className="hover:text-blue-600 transition-colors"
                onClick={closeMobileMenu}
              >
                Home
              </Link>
              <Link 
                href="/jobs" 
                className="hover:text-blue-600 transition-colors"
                onClick={closeMobileMenu}
              >
                Search Jobs
              </Link>
              
              {isAuthenticated ? (
                <>
                  {user?.role === 'employer' && (
                    <>
                      <Link 
                        href="/employer/post-job" 
                        className="hover:text-blue-600 transition-colors"
                        onClick={closeMobileMenu}
                      >
                        Post Job
                      </Link>
                      <Link 
                        href="/employer/dashboard" 
                        className="hover:text-blue-600 transition-colors"
                        onClick={closeMobileMenu}
                      >
                        Dashboard
                      </Link>
                    </>
                  )}
                  {user?.role === 'job_seeker' && (
                    <Link 
                      href="/applications" 
                      className="hover:text-blue-600 transition-colors"
                      onClick={closeMobileMenu}
                    >
                      My Applications
                    </Link>
                  )}
                  <button
                    onClick={handleLogout}
                    className="px-4 py-2 bg-gray-200 rounded-lg hover:bg-gray-300 transition-colors text-left"
                  >
                    Logout
                  </button>
                </>
              ) : (
                <>
                  <Link 
                    href="/login" 
                    className="hover:text-blue-600 transition-colors"
                    onClick={closeMobileMenu}
                  >
                    Login
                  </Link>
                  <Link
                    href="/register"
                    className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-center"
                    onClick={closeMobileMenu}
                  >
                    Sign Up
                  </Link>
                </>
              )}
            </div>
          </nav>
        )}
      </div>
    </header>
  )
}
