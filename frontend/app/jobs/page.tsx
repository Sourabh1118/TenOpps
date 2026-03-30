'use client'

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { SearchFilters as SearchFiltersType } from '@/types'
import { searchApi } from '@/lib/api/search'
import { SearchBar } from '@/components/jobs/SearchBar'
import { SearchFilters } from '@/components/jobs/SearchFilters'
import { JobCard } from '@/components/jobs/JobCard'
import { JobListingSkeleton } from '@/components/jobs/JobCardSkeleton'
import { motion } from 'framer-motion'
import { AnimationWrapper, staggerContainer, staggerItem } from '@/components/ui/AnimationWrapper'

export default function JobsPage() {
  const [filters, setFilters] = useState<SearchFiltersType>({})
  const [page, setPage] = useState(1)
  const pageSize = 20

  // Fetch jobs with React Query
  const { data, isLoading, isError, error } = useQuery({
    queryKey: ['jobs', filters, page],
    queryFn: () => searchApi.searchJobs({ ...filters, page, page_size: pageSize }),
    placeholderData: (previousData) => previousData,
  })

  const handleSearch = (query: string) => {
    setFilters({ ...filters, query: query || undefined })
    setPage(1)
  }

  const handleFiltersChange = (newFilters: SearchFiltersType) => {
    setFilters(newFilters)
    setPage(1)
  }

  const handlePageChange = (newPage: number) => {
    setPage(newPage)
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header Section */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-6">Find Your Next Opportunity</h1>
          <SearchBar onSearch={handleSearch} initialQuery={filters.query} />
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Filters Sidebar - Hidden on mobile, shown on desktop */}
          <aside className="hidden lg:block lg:col-span-1">
            <div className="sticky top-6">
              <SearchFilters filters={filters} onFiltersChange={handleFiltersChange} />
            </div>
          </aside>

          {/* Mobile Filters - Shown on mobile only */}
          <div className="lg:hidden mb-4">
            <details className="bg-white border border-gray-200 rounded-lg">
              <summary className="px-4 py-3 cursor-pointer font-medium text-gray-900 flex items-center justify-between">
                <span>Filters</span>
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </summary>
              <div className="px-4 pb-4">
                <SearchFilters filters={filters} onFiltersChange={handleFiltersChange} />
              </div>
            </details>
          </div>

          {/* Job Results */}
          <main className="lg:col-span-3">
            {/* Results Header */}
            {data && (
              <div className="mb-6 flex items-center justify-between">
                <p className="text-sm text-gray-600">
                  Showing {((page - 1) * pageSize) + 1} - {Math.min(page * pageSize, data.total)} of {data.total} jobs
                </p>
              </div>
            )}

            {/* Loading State */}
            {isLoading && <JobListingSkeleton />}

            {/* Error State */}
            {isError && (
              <AnimationWrapper variant="fade">
                <div className="bg-red-50 border border-red-200 rounded-[2rem] p-8 text-center">
                  <h3 className="text-red-800 font-black text-xl mb-2">Error loading jobs</h3>
                  <p className="text-red-600 font-medium whitespace-pre-wrap">
                    {error instanceof Error ? error.message : 'An unexpected error occurred'}
                  </p>
                </div>
              </AnimationWrapper>
            )}

            {/* Job Results */}
            {data && data.jobs.length > 0 && (
              <motion.div 
                variants={staggerContainer}
                initial="hidden"
                animate="visible"
                className="grid grid-cols-1 md:grid-cols-2 gap-6"
              >
                {data.jobs.map((job) => (
                  <motion.div variants={staggerItem} key={job.id}>
                    <JobCard job={job} />
                  </motion.div>
                ))}
              </motion.div>
            )}

            {/* No Results */}
            {data && data.jobs.length === 0 && (
              <div className="bg-white border border-gray-200 rounded-lg p-12 text-center">
                <svg
                  className="mx-auto h-12 w-12 text-gray-400 mb-4"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                  />
                </svg>
                <h3 className="text-lg font-medium text-gray-900 mb-2">No jobs found</h3>
                <p className="text-gray-600">Try adjusting your search filters to find more results.</p>
              </div>
            )}

            {/* Pagination */}
            {data && data.total_pages > 1 && (
              <div className="mt-8 flex items-center justify-center gap-2">
                <button
                  onClick={() => handlePageChange(page - 1)}
                  disabled={page === 1}
                  className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Previous
                </button>
                
                <div className="flex items-center gap-1">
                  {[...Array(Math.min(5, data.total_pages))].map((_, i) => {
                    let pageNum: number
                    if (data.total_pages <= 5) {
                      pageNum = i + 1
                    } else if (page <= 3) {
                      pageNum = i + 1
                    } else if (page >= data.total_pages - 2) {
                      pageNum = data.total_pages - 4 + i
                    } else {
                      pageNum = page - 2 + i
                    }

                    return (
                      <button
                        key={pageNum}
                        onClick={() => handlePageChange(pageNum)}
                        className={`px-4 py-2 border rounded-md text-sm font-medium ${
                          page === pageNum
                            ? 'bg-blue-600 text-white border-blue-600'
                            : 'border-gray-300 text-gray-700 bg-white hover:bg-gray-50'
                        }`}
                      >
                        {pageNum}
                      </button>
                    )
                  })}
                </div>

                <button
                  onClick={() => handlePageChange(page + 1)}
                  disabled={page === data.total_pages}
                  className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Next
                </button>
              </div>
            )}
          </main>
        </div>
      </div>
    </div>
  )
}
