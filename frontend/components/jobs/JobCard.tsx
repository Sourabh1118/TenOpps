'use client'

import Link from 'next/link'
import { Job } from '@/types'
import { formatDistanceToNow } from 'date-fns'

interface JobCardProps {
  job: Job
}

export function JobCard({ job }: JobCardProps) {
  const formatSalary = () => {
    if (!job.salaryMin && !job.salaryMax) return null
    
    const currency = job.salaryCurrency || 'USD'
    const formatter = new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency,
      maximumFractionDigits: 0,
    })
    
    if (job.salaryMin && job.salaryMax) {
      return `${formatter.format(job.salaryMin)} - ${formatter.format(job.salaryMax)}`
    } else if (job.salaryMin) {
      return `From ${formatter.format(job.salaryMin)}`
    } else if (job.salaryMax) {
      return `Up to ${formatter.format(job.salaryMax)}`
    }
  }

  const formatJobType = (type: string) => {
    return type.replace('_', ' ').toLowerCase().replace(/\b\w/g, l => l.toUpperCase())
  }

  const formatExperienceLevel = (level: string) => {
    return level.charAt(0) + level.slice(1).toLowerCase()
  }

  const getQualityBadge = () => {
    if (job.qualityScore >= 80) return { text: 'High Quality', color: 'bg-green-100 text-green-800' }
    if (job.qualityScore >= 60) return { text: 'Good', color: 'bg-blue-100 text-blue-800' }
    return { text: 'Standard', color: 'bg-gray-100 text-gray-800' }
  }

  const qualityBadge = getQualityBadge()
  const salary = formatSalary()
  const postedAgo = formatDistanceToNow(new Date(job.postedAt), { addSuffix: true })

  return (
    <Link href={`/jobs/${job.id}`}>
      <div className="bg-white border border-gray-200 rounded-lg p-6 hover:shadow-lg transition-shadow duration-200 cursor-pointer">
        {/* Header with Featured Badge */}
        <div className="flex items-start justify-between mb-3">
          <div className="flex-1">
            <h3 className="text-xl font-semibold text-gray-900 mb-1 hover:text-blue-600 transition-colors">
              {job.title}
            </h3>
            <p className="text-lg text-gray-700 font-medium">{job.company}</p>
          </div>
          {job.featured && (
            <span className="ml-4 px-3 py-1 bg-yellow-100 text-yellow-800 text-sm font-medium rounded-full flex-shrink-0">
              ⭐ Featured
            </span>
          )}
        </div>

        {/* Location and Remote Badge */}
        <div className="flex items-center gap-2 mb-3 flex-wrap">
          <span className="text-gray-600 flex items-center">
            <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
            {job.location}
          </span>
          {job.remote && (
            <span className="px-2 py-1 bg-green-100 text-green-800 text-xs font-medium rounded">
              🏠 Remote
            </span>
          )}
        </div>

        {/* Job Details */}
        <div className="flex items-center gap-3 mb-3 flex-wrap text-sm text-gray-600">
          <span className="px-2 py-1 bg-gray-100 rounded">
            {formatJobType(job.jobType)}
          </span>
          <span className="px-2 py-1 bg-gray-100 rounded">
            {formatExperienceLevel(job.experienceLevel)}
          </span>
          {salary && (
            <span className="font-medium text-gray-900">
              💰 {salary}
            </span>
          )}
        </div>

        {/* Description Preview */}
        <p className="text-gray-600 text-sm mb-4 line-clamp-2">
          {job.description}
        </p>

        {/* Footer */}
        <div className="flex items-center justify-between pt-4 border-t border-gray-100">
          <div className="flex items-center gap-3 text-sm text-gray-500">
            <span>{postedAgo}</span>
            {job.applicationCount !== undefined && job.applicationCount > 0 && (
              <span>• {job.applicationCount} applicants</span>
            )}
            <span className={`px-2 py-1 text-xs font-medium rounded ${qualityBadge.color}`}>
              {qualityBadge.text}
            </span>
          </div>
          {job.sourceType !== 'direct' && job.sourcePlatform && (
            <span className="text-xs text-gray-400">
              via {job.sourcePlatform}
            </span>
          )}
        </div>
      </div>
    </Link>
  )
}
