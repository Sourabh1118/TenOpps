'use client'

import Link from 'next/link'
import { Job } from '@/types'
import { formatDistanceToNow } from 'date-fns'
import { 
  MapPin, 
  Briefcase, 
  Coins, 
  Star, 
  Building2, 
  Eye, 
  Users,
  Target
} from 'lucide-react'
import { motion } from 'framer-motion'

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

  const stripHtml = (html?: string) => {
    if (!html) return ''
    return html.replace(/<[^>]*>?/gm, '')
  }

  const getQualityBadge = () => {
    if (job.qualityScore >= 80) return { text: 'High Quality', color: 'bg-emerald-50 text-emerald-700 border-emerald-100' }
    if (job.qualityScore >= 60) return { text: 'Good Match', color: 'bg-blue-50 text-blue-700 border-blue-100' }
    return { text: 'Standard', color: 'bg-slate-50 text-slate-700 border-slate-100' }
  }

  const qualityBadge = getQualityBadge()
  const salary = formatSalary()
  
  let posted_ago = 'Recently'
  try {
    const date = new Date(job.postedAt)
    if (!isNaN(date.getTime())) {
      posted_ago = formatDistanceToNow(date, { addSuffix: true })
    }
  } catch (e) {
    console.error('Error parsing date:', e)
  }

  return (
    <Link href={`/jobs/${job.id}`}>
      <motion.div 
        whileHover={{ y: -8, scale: 1.01 }}
        whileTap={{ scale: 0.98 }}
        className="group bg-white border border-slate-100 rounded-[2rem] p-6 hover:shadow-2xl hover:shadow-blue-500/10 hover:border-blue-100 transition-all duration-300 cursor-pointer relative overflow-hidden h-full flex flex-col"
      >
        {/* Subtle hover effect background */}
        <div className="absolute top-0 right-0 -mr-8 -mt-8 w-32 h-32 bg-blue-500/5 rounded-full blur-3xl group-hover:bg-blue-500/10 transition-colors"></div>

        <div className="relative z-10 flex flex-col h-full">
          {/* Header with Featured Badge */}
          <div className="flex items-start justify-between mb-4">
            <div className="flex-1">
              <h3 className="text-xl font-black text-slate-900 mb-1 group-hover:text-blue-600 transition-colors leading-tight line-clamp-1">
                {job.title}
              </h3>
              <div className="flex items-center text-slate-500 font-bold text-sm">
                <Building2 className="w-3.5 h-3.5 mr-2 text-slate-400 group-hover:text-blue-500 transition-colors" />
                {job.company}
              </div>
            </div>
            {job.featured && (
              <motion.span 
                animate={{ 
                  backgroundColor: ["rgba(254, 252, 232, 1)", "rgba(254, 252, 232, 0.5)", "rgba(254, 252, 232, 1)"],
                }}
                transition={{ duration: 2, repeat: Infinity }}
                className="ml-4 px-3 py-1 bg-amber-50 text-amber-600 text-[10px] font-black uppercase tracking-widest border border-amber-100 rounded-lg flex items-center shadow-sm whitespace-nowrap"
              >
                <Star className="w-3 h-3 mr-1 fill-amber-500 text-amber-500" />
                Featured
              </motion.span>
            )}
          </div>

          {/* Location and Metadata Grid */}
          <div className="grid grid-cols-2 gap-3 mb-5">
            <div className="flex items-center text-slate-500 text-sm font-bold truncate">
              <MapPin className="w-3.5 h-3.5 mr-2 text-blue-500 flex-shrink-0" />
              <span className="truncate">{job.location}</span>
              {job.remote && (
                <span className="ml-2 px-1.5 py-0.5 bg-emerald-50 text-emerald-600 text-[9px] rounded font-black border border-emerald-100">REMOTE</span>
              )}
            </div>
            <div className="flex items-center text-slate-500 text-sm font-bold truncate">
              <Briefcase className="w-3.5 h-3.5 mr-2 text-indigo-500 flex-shrink-0" />
              <span className="capitalize truncate">{job.jobType?.replace('_', ' ') || 'N/A'}</span>
            </div>
          </div>

          {/* Salary and Quality */}
          <div className="flex items-center gap-3 mb-5 flex-wrap">
            {salary && (
              <span className="inline-flex items-center px-3 py-1.5 bg-slate-50 text-slate-700 text-xs font-black rounded-xl border border-slate-100 group-hover:bg-white group-hover:border-amber-100 transition-all">
                <motion.div
                  animate={{ rotate: [0, 10, -10, 0] }}
                  transition={{ duration: 2, repeat: Infinity }}
                >
                  <Coins className="w-3.5 h-3.5 mr-2 text-amber-500" />
                </motion.div>
                {salary}
              </span>
            )}
            <span className={`inline-flex items-center px-3 py-1.5 text-xs font-black rounded-xl border ${qualityBadge.color} transition-all`}>
              <Target className="w-3.5 h-3.5 mr-2" />
              {qualityBadge.text}
            </span>
          </div>

          {/* Description Preview */}
          <p className="text-slate-500 text-sm mb-6 line-clamp-2 leading-relaxed italic flex-grow">
            {stripHtml(job.description) || "No description provided."}
          </p>

          {/* Footer */}
          <div className="flex items-center justify-between pt-5 border-t border-slate-50 italic mt-auto">
            <div className="flex items-center gap-4 text-[11px] font-bold text-slate-400">
              <span className="flex items-center"><Eye className="w-3 h-3 mr-1" /> {job.viewCount} views</span>
              <span className="flex items-center"><Users className="w-3 h-3 mr-1" /> {job.applicationCount || 0} applicants</span>
              <span>•</span>
              <span className="text-blue-500/70">{posted_ago}</span>
            </div>
            {job.sourceType !== 'direct' && job.sourcePlatform && (
              <span className="text-[10px] font-black text-slate-300 uppercase tracking-tighter">
                via {job.sourcePlatform}
              </span>
            )}
          </div>
        </div>
      </motion.div>
    </Link>
  )
}
