'use client'

import { useEffect } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { useQuery } from '@tanstack/react-query'
import { jobsApi } from '@/lib/api/jobs'
import { formatDistanceToNow } from 'date-fns'
import Link from 'next/link'
import { 
  MapPin, 
  Briefcase, 
  Clock, 
  Coins, 
  Building2, 
  ExternalLink, 
  ChevronLeft, 
  Star,
  Eye,
  Users,
  Target,
  CheckCircle2,
  ListChecks,
  ChevronRight
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { motion, AnimatePresence } from 'framer-motion'
import { AnimationWrapper, staggerContainer, staggerItem } from '@/components/ui/AnimationWrapper'
import { StickyApplyBar } from '@/components/jobs/StickyApplyBar'
import { JobCard } from '@/components/jobs/JobCard'

export default function JobDetailPage() {
  const params = useParams()
  const router = useRouter()
  const jobId = params.id as string

  // Fetch job details
  const { data: job, isLoading, isError, error } = useQuery({
    queryKey: ['job', jobId],
    queryFn: () => jobsApi.getJobById(jobId),
  })

  // Increment view count
  useEffect(() => {
    if (jobId) {
      jobsApi.incrementViewCount(jobId).catch(() => {})
    }
  }, [jobId])

  const formatSalary = () => {
    if (!job || (!job.salaryMin && !job.salaryMax)) return null
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

  if (isLoading) {
    return (
      <div className="min-h-screen bg-[#F8FAFC] py-12 px-4 sm:px-6 lg:px-8 animate-in fade-in duration-500">
        <div className="max-w-4xl mx-auto">
          <div className="bg-white shadow-xl shadow-blue-500/5 rounded-3xl p-8 animate-pulse">
            <div className="h-10 bg-slate-200 rounded-full w-3/4 mb-4"></div>
            <div className="h-6 bg-slate-100 rounded-full w-1/2 mb-8"></div>
            <div className="space-y-4">
              <div className="h-4 bg-slate-100 rounded-full w-full"></div>
              <div className="h-4 bg-slate-100 rounded-full w-full"></div>
              <div className="h-4 bg-slate-100 rounded-full w-3/4"></div>
            </div>
          </div>
        </div>
      </div>
    )
  }

  if (isError || !job) {
    return (
      <div className="min-h-screen bg-[#F8FAFC] flex items-center justify-center p-4">
        <div className="max-w-md w-full bg-white shadow-2xl rounded-3xl p-10 text-center">
          <div className="w-20 h-20 bg-red-50 rounded-full flex items-center justify-center mx-auto mb-6">
            <Target className="w-10 h-10 text-red-500" />
          </div>
          <h2 className="text-2xl font-bold text-slate-900 mb-2">Job Not Found</h2>
          <p className="text-slate-500 mb-8">{error instanceof Error ? error.message : "We couldn't find the position you're looking for."}</p>
          <button
            onClick={() => router.push('/jobs')}
            className="w-full py-4 bg-blue-600 text-white font-semibold rounded-2xl hover:bg-blue-700 transition-all active:scale-95"
          >
            Browse All Jobs
          </button>
        </div>
      </div>
    )
  }

  const salary = formatSalary()
  const postedAgo = formatDistanceToNow(new Date(job.postedAt), { addSuffix: true })
  const isDirectPost = job.sourceType === 'direct'

  return (
    <div className="min-h-screen bg-[#F8FAFC] selection:bg-blue-100 selection:text-blue-900 overflow-x-hidden">
      <StickyApplyBar job={job} />
      
      <div className="max-w-5xl mx-auto px-4 py-12">
        {/* Navigation */}
        <AnimationWrapper variant="fade" delay={0.1}>
          <Link
            href="/jobs"
            className="group inline-flex items-center text-sm font-medium text-slate-500 hover:text-blue-600 mb-10 transition-colors"
          >
            <div className="mr-3 p-1.5 rounded-lg bg-white border border-slate-200 group-hover:border-blue-200 group-hover:bg-blue-50 transition-all">
              <ChevronLeft className="w-4 h-4" />
            </div>
            Back to listings
          </Link>
        </AnimationWrapper>

        {/* Hero Header */}
        <AnimationWrapper variant="slide-up" delay={0.2}>
          <div className="relative overflow-hidden bg-white rounded-[2.5rem] shadow-2xl shadow-blue-500/10 border border-white/50 p-8 md:p-12 mb-8 mt-2">
            {/* Decorative Gradient */}
            <div className="absolute top-0 right-0 -mr-20 -mt-20 w-80 h-80 bg-blue-600/5 rounded-full blur-3xl pointer-events-none"></div>
            
            <div className="relative z-10">
              <div className="flex flex-col md:flex-row md:items-start justify-between gap-6 mb-10">
                <div className="flex-1">
                  <div className="flex flex-wrap items-center gap-3 mb-4">
                    {job.featured && (
                      <span className="inline-flex items-center px-4 py-1.5 bg-amber-50 text-amber-700 text-xs font-bold uppercase tracking-wider rounded-full border border-amber-100">
                        <Star className="w-3.5 h-3.5 mr-1.5 fill-amber-500 text-amber-500" />
                        Featured
                      </span>
                    )}
                    <span className="inline-flex items-center px-4 py-1.5 bg-blue-50 text-blue-700 text-xs font-bold uppercase tracking-wider rounded-full border border-blue-100">
                      {job.sourceType}
                    </span>
                  </div>
                  <h1 className="text-3xl md:text-5xl font-black text-slate-900 tracking-tight leading-tight mb-4">
                    {job.title}
                  </h1>
                  <div className="flex items-center text-xl text-slate-600 font-semibold group cursor-default">
                    <div className="w-12 h-12 bg-slate-50 border border-slate-100 rounded-xl flex items-center justify-center mr-4 group-hover:bg-white group-hover:border-blue-100 transition-all shadow-sm">
                      <Building2 className="w-6 h-6 text-slate-400 group-hover:text-blue-500 transition-colors" />
                    </div>
                    {job.company}
                  </div>
                </div>

                <div className="flex flex-col gap-4 min-w-[200px]">
                  {isDirectPost ? (
                    <button
                      onClick={() => router.push(`/jobs/${job.id}/apply`)}
                      className="w-full py-4 px-8 bg-blue-600 text-white font-bold rounded-2xl hover:bg-blue-700 hover:shadow-xl hover:shadow-blue-600/20 active:scale-95 transition-all shadow-lg shadow-blue-600/10"
                    >
                      Apply Now
                    </button>
                  ) : (
                    <a
                      href={job.sourceUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="w-full py-4 px-8 bg-blue-600 text-white font-bold rounded-2xl hover:bg-blue-700 hover:shadow-xl hover:shadow-blue-600/20 active:scale-95 transition-all text-center inline-flex items-center justify-center shadow-lg shadow-blue-600/10"
                    >
                      Apply on {job.sourcePlatform || 'External Site'}
                      <ExternalLink className="w-5 h-5 ml-2.5" />
                    </a>
                  )}
                  <div className="flex items-center justify-center gap-6 text-sm font-medium text-slate-400">
                    <span className="flex items-center italic"><Eye className="w-4 h-4 mr-1.5" />{job.viewCount} views</span>
                    <span className="flex items-center italic"><Users className="w-4 h-4 mr-1.5" />{job.applicationCount || 0} applicants</span>
                  </div>
                </div>
              </div>

              {/* Quick Info Grid */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 md:gap-8 p-6 md:p-8 bg-slate-50/50 rounded-[2rem] border border-slate-100/50">
                <div className="space-y-1">
                  <span className="text-xs font-bold uppercase tracking-widest text-slate-400">Location</span>
                  <div className="flex items-center font-bold text-slate-700">
                    <MapPin className="w-4 h-4 mr-2 text-blue-500" />
                    {job.location}
                    {job.remote && (
                      <span className="ml-2.5 px-2 py-0.5 bg-emerald-50 text-emerald-700 text-[10px] rounded border border-emerald-100">REMOTE</span>
                    )}
                  </div>
                </div>
                <div className="space-y-1">
                  <span className="text-xs font-bold uppercase tracking-widest text-slate-400">Job Type</span>
                  <div className="flex items-center font-bold text-slate-700 capitalize">
                    <Briefcase className="w-4 h-4 mr-2 text-indigo-500" />
                    {job.jobType?.replace('_', ' ') || 'N/A'}
                  </div>
                </div>
                <div className="space-y-1">
                  <span className="text-xs font-bold uppercase tracking-widest text-slate-400">Experience</span>
                  <div className="flex items-center font-bold text-slate-700 capitalize">
                    <ListChecks className="w-4 h-4 mr-2 text-purple-500" />
                    {job.experienceLevel}
                  </div>
                </div>
                <div className="space-y-1">
                  <span className="text-xs font-bold uppercase tracking-widest text-slate-400">Salary Range</span>
                  <div className="flex items-center font-bold text-slate-700">
                    <Coins className="w-4 h-4 mr-2 text-amber-500" />
                    {salary || 'Market Rate'}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </AnimationWrapper>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Main Description */}
          <div className="lg:col-span-2 space-y-8">
            <AnimationWrapper variant="slide-up" delay={0.3}>
              <div className="bg-white rounded-[2rem] shadow-xl shadow-slate-200 border border-slate-100 p-8 md:p-12 h-full">
                <h2 className="text-2xl font-black text-slate-900 mb-8 flex items-center">
                  <div className="w-1.5 h-8 bg-blue-600 rounded-full mr-4"></div>
                  Detailed Description
                </h2>
                <div 
                  className="prose prose-slate prose-lg max-w-none 
                    prose-headings:font-black prose-headings:text-slate-900 
                    prose-p:text-slate-600 prose-p:leading-relaxed
                    prose-strong:text-slate-900 prose-strong:font-bold
                    prose-ul:list-disc prose-li:marker:text-blue-500
                    prose-li:text-slate-600 prose-a:text-blue-600"
                  dangerouslySetInnerHTML={{ __html: job.description }}
                />
              </div>
            </AnimationWrapper>

            {/* Tags section in main column if present */}
            {job.tags && job.tags.length > 0 && (
              <AnimationWrapper variant="slide-up" delay={0.4}>
                <div className="bg-white rounded-[2rem] shadow-xl shadow-slate-200 border border-slate-100 p-8 md:p-12">
                  <h2 className="text-2xl font-black text-slate-900 mb-6 flex items-center">
                    <div className="w-1.5 h-8 bg-indigo-600 rounded-full mr-4"></div>
                    Key Competencies
                  </h2>
                  <div className="flex flex-wrap gap-2.5">
                    {job.tags.map((tag, index) => (
                      <span
                        key={index}
                        className="px-5 py-2.5 bg-slate-50 text-slate-700 font-bold text-sm rounded-2xl border border-slate-100 hover:bg-white hover:border-blue-200 hover:text-blue-600 transition-all cursor-default"
                      >
                        #{tag}
                      </span>
                    ))}
                  </div>
                </div>
              </AnimationWrapper>
            )}
          </div>

          {/* Sidebar */}
          <div className="space-y-8">
            {/* Metadata Card */}
            <AnimationWrapper variant="slide-up" delay={0.5}>
              <div className="bg-white rounded-[2rem] shadow-xl shadow-slate-200 border border-slate-100 p-8">
                <h3 className="text-lg font-black text-slate-900 mb-6 uppercase tracking-wider">Position Meta</h3>
                <div className="space-y-5">
                  <div className="flex items-center justify-between py-3 border-b border-slate-50 italic">
                    <span className="text-slate-400 flex items-center text-sm font-bold uppercase tracking-tight"><Clock className="w-4 h-4 mr-2" />Posted</span>
                    <span className="text-slate-700 font-black">{postedAgo}</span>
                  </div>
                  <div className="flex items-center justify-between py-3 border-b border-slate-50 italic">
                    <span className="text-slate-400 flex items-center text-sm font-bold uppercase tracking-tight"><Target className="w-4 h-4 mr-2" />Match Score</span>
                    <div className="flex items-center">
                      <div className="w-16 h-2 bg-slate-100 rounded-full overflow-hidden mr-3 shadow-inner">
                        <motion.div 
                          initial={{ width: 0 }}
                          animate={{ width: `${job.qualityScore}%` }}
                          transition={{ duration: 1.5, delay: 0.8, ease: "easeOut" }}
                          className="h-full bg-gradient-to-r from-blue-500 to-indigo-600 rounded-full"
                        ></motion.div>
                      </div>
                      <span className="text-slate-700 font-black">{Math.round(job.qualityScore)}%</span>
                    </div>
                  </div>
                  <div className="flex items-center justify-between py-3 italic">
                    <span className="text-slate-400 flex items-center text-sm font-bold uppercase tracking-tight"><ListChecks className="w-4 h-4 mr-2" />Status</span>
                    <span className="px-3 py-1 bg-emerald-50 text-emerald-700 text-[10px] font-black uppercase rounded-lg border border-emerald-100 shadow-sm">Active Now</span>
                  </div>
                </div>
              </div>
            </AnimationWrapper>

            {/* List sections if they exist as arrays */}
            {job.requirements && job.requirements.length > 0 && (
              <AnimationWrapper variant="slide-up" delay={0.6}>
                <div className="bg-slate-900 rounded-[3rem] shadow-2xl p-10 text-white relative overflow-hidden group">
                  <div className="absolute top-0 right-0 -mr-16 -mt-16 w-48 h-48 bg-blue-500/10 rounded-full blur-3xl group-hover:bg-blue-500/20 transition-all duration-700"></div>
                  <h3 className="text-xl font-black text-white mb-8 uppercase tracking-widest flex items-center relative z-10">
                    <CheckCircle2 className="w-6 h-6 mr-3 text-blue-400" />
                    Requirements
                  </h3>
                  <ul className="space-y-6 relative z-10">
                    {job.requirements.map((req, index) => (
                      <li key={index} className="flex items-start text-sm text-slate-300 leading-relaxed font-bold italic">
                        <div className="w-2 h-2 bg-blue-500 rounded-full mt-1.5 mr-4 flex-shrink-0 shadow-[0_0_10px_rgba(59,130,246,0.5)]"></div>
                        {req}
                      </li>
                    ))}
                  </ul>
                </div>
              </AnimationWrapper>
            )}
          </div>
        </div>

        {/* Related Jobs Section placeholder */}
        <AnimationWrapper variant="fade" delay={0.7}>
          <div className="mt-20">
            <h2 className="text-3xl font-black text-slate-900 mb-10 flex items-center px-4">
              <span className="bg-blue-600 w-2 h-10 rounded-full mr-5 shadow-lg shadow-blue-500/20"></span>
              Similar Opportunities
              <Link href="/jobs" className="ml-auto text-sm font-black text-blue-600 hover:text-blue-700 flex items-center tracking-widest uppercase">
                View All <ChevronRight className="w-4 h-4 ml-1" />
              </Link>
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 opacity-40 blur-[2px] pointer-events-none select-none">
                {/* Visual placeholder for related jobs */}
                {[1, 2, 3].map(i => (
                  <div key={i} className="bg-white border border-slate-100 rounded-[2rem] p-6 h-48"></div>
                ))}
            </div>
            <div className="text-center -mt-32 relative z-20">
              <span className="bg-slate-900 text-white px-8 py-3 rounded-full text-sm font-black uppercase tracking-widest border-4 border-white shadow-2xl">
                Coming Soon: Smart Recommendations
              </span>
            </div>
          </div>
        </AnimationWrapper>
      </div>
    </div>
  )
}
