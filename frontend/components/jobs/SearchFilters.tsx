'use client'

import { SearchFilters as SearchFiltersType, JobType, ExperienceLevel, SourceType } from '@/types'

interface SearchFiltersProps {
  filters: SearchFiltersType
  onFiltersChange: (filters: SearchFiltersType) => void
}

export function SearchFilters({ filters, onFiltersChange }: SearchFiltersProps) {
  const updateFilter = (key: keyof SearchFiltersType, value: unknown) => {
    onFiltersChange({ ...filters, [key]: value })
  }

  const toggleArrayFilter = (key: 'jobType' | 'experienceLevel' | 'sourceType', value: string) => {
    const currentArray = (filters[key] || []) as string[]
    const newArray = currentArray.includes(value)
      ? currentArray.filter(item => item !== value)
      : [...currentArray, value]
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    updateFilter(key, newArray.length > 0 ? newArray as any : undefined)
  }

  const clearFilters = () => {
    onFiltersChange({})
  }

  const hasActiveFilters = Object.keys(filters).length > 0

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-gray-900">Filters</h2>
        {hasActiveFilters && (
          <button
            onClick={clearFilters}
            className="text-sm text-blue-600 hover:text-blue-700 font-medium"
          >
            Clear all
          </button>
        )}
      </div>

      {/* Location */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Location
        </label>
        <input
          type="text"
          value={filters.location || ''}
          onChange={(e) => updateFilter('location', e.target.value || undefined)}
          placeholder="e.g. San Francisco"
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>

      {/* Remote */}
      <div>
        <label className="flex items-center space-x-2 cursor-pointer">
          <input
            type="checkbox"
            checked={filters.remote || false}
            onChange={(e) => updateFilter('remote', e.target.checked || undefined)}
            className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
          />
          <span className="text-sm font-medium text-gray-700">Remote only</span>
        </label>
      </div>

      {/* Job Type */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Job Type
        </label>
        <div className="space-y-2">
          {Object.values(JobType).map((type) => (
            <label key={type} className="flex items-center space-x-2 cursor-pointer">
              <input
                type="checkbox"
                checked={filters.jobType?.includes(type) || false}
                onChange={() => toggleArrayFilter('jobType', type)}
                className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
              />
              <span className="text-sm text-gray-700">
                {type.replace('_', ' ').toLowerCase().replace(/\b\w/g, l => l.toUpperCase())}
              </span>
            </label>
          ))}
        </div>
      </div>

      {/* Experience Level */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Experience Level
        </label>
        <div className="space-y-2">
          {Object.values(ExperienceLevel).map((level) => (
            <label key={level} className="flex items-center space-x-2 cursor-pointer">
              <input
                type="checkbox"
                checked={filters.experienceLevel?.includes(level) || false}
                onChange={() => toggleArrayFilter('experienceLevel', level)}
                className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
              />
              <span className="text-sm text-gray-700">
                {level.charAt(0) + level.slice(1).toLowerCase()}
              </span>
            </label>
          ))}
        </div>
      </div>

      {/* Salary Range */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Minimum Salary
        </label>
        <input
          type="number"
          value={filters.salaryMin || ''}
          onChange={(e) => updateFilter('salaryMin', e.target.value ? parseInt(e.target.value) : undefined)}
          placeholder="e.g. 50000"
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Maximum Salary
        </label>
        <input
          type="number"
          value={filters.salaryMax || ''}
          onChange={(e) => updateFilter('salaryMax', e.target.value ? parseInt(e.target.value) : undefined)}
          placeholder="e.g. 150000"
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>

      {/* Posted Within */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Posted Within
        </label>
        <select
          value={filters.postedWithin || ''}
          onChange={(e) => updateFilter('postedWithin', e.target.value ? parseInt(e.target.value) : undefined)}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="">Any time</option>
          <option value="1">Last 24 hours</option>
          <option value="3">Last 3 days</option>
          <option value="7">Last week</option>
          <option value="14">Last 2 weeks</option>
          <option value="30">Last month</option>
        </select>
      </div>

      {/* Source Type */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Source Type
        </label>
        <div className="space-y-2">
          <label className="flex items-center space-x-2 cursor-pointer">
            <input
              type="checkbox"
              checked={filters.sourceType?.includes(SourceType.DIRECT) || false}
              onChange={() => toggleArrayFilter('sourceType', SourceType.DIRECT)}
              className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
            />
            <span className="text-sm text-gray-700">Direct Posts</span>
          </label>
          <label className="flex items-center space-x-2 cursor-pointer">
            <input
              type="checkbox"
              checked={filters.sourceType?.includes(SourceType.URL_IMPORT) || false}
              onChange={() => toggleArrayFilter('sourceType', SourceType.URL_IMPORT)}
              className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
            />
            <span className="text-sm text-gray-700">URL Imports</span>
          </label>
          <label className="flex items-center space-x-2 cursor-pointer">
            <input
              type="checkbox"
              checked={filters.sourceType?.includes(SourceType.AGGREGATED) || false}
              onChange={() => toggleArrayFilter('sourceType', SourceType.AGGREGATED)}
              className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
            />
            <span className="text-sm text-gray-700">Aggregated</span>
          </label>
        </div>
      </div>
    </div>
  )
}
