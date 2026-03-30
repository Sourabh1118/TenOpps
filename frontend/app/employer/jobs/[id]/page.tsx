'use client'

import { useQuery } from '@tanstack/react-query'
import { jobsApi } from '@/lib/api/jobs'
import { applicationsApi } from '@/lib/api/applications'
import { useParams, useSearchParams } from 'next/navigation'
import { ProtectedRoute } from '@/components/auth/ProtectedRoute'
import Link from 'next/link'
import { formatDistanceToNow, format } from 'date-fns'
import { JobStatus } from '@/types'
import { 
  BarChart3, 
  Users, 
  Eye, 
  Trophy, 
  Calendar, 
  Edit3, 
  Globe, 
  ChevronLeft,
  CheckCircle2,
  AlertCircle,
  Building2,
  MapPin,
  Briefcase,
  Layers,
  ChevronRight,
  Clock
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { motion } from 'framer-motion'
import { AnimationWrapper, staggerContainer, staggerItem } from '@/components/ui/AnimationWrapper'

const statusConfig: Record<JobStatus, { label: string; className: string; icon: any }> = {
  ACTIVE: { label: 'Active', className: 'bg-emerald-50 text-emerald-700 border-emerald-100', icon: CheckCircle2 },
  EXPIRED: { label: 'Expired', className: 'bg-amber-50 text-amber-700 border-amber-100', icon: AlertCircle },
  FILLED: { label: 'Filled', className: 'bg-blue-50 text-blue-700 border-blue-100', icon: CheckCircle2 },
  DELETED: { label: 'Deleted', className: 'bg-slate-50 text-slate-700 border-slate-100', icon: AlertCircle },
}

export default function EmployerJobDetailsPage() {
  return (
    <ProtectedRoute requiredRole="employer">
      <JobDetailsContent />
    </ProtectedRoute>
  )
}

function JobDetailsContent() {
  const params = useParams()
  const searchParams = useSearchParams()
  const jobId = params.id as string
  const posted = searchParams.get('posted') === 'true'
  const updated = searchParams.get('updated') === 'true'

  // Fetch job details
  const { data: job, isLoading: jobLoading } = useQuery({
    queryKey: ['job', jobId],
    queryFn: () => jobsApi.getJobById(jobId),
  })

  // Fetch applications
  const { data: applicationsData, isLoading: appsLoading } = useQuery({
    queryKey: ['job-applications', jobId],
    queryFn: () => applicationsApi.getApplicationsForJob(jobId),
    enabled: !!job && job.sourceType === 'direct',
  })

  const isLoading = jobLoading || appsLoading

  if (isLoading) {
    return (
      <div className="min-h-screen bg-[#FBFDFF] py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-5xl mx-auto space-y-8 animate-pulse">
          <div className="h-8 bg-slate-200 rounded-full w-48"></div>
          <div className="bg-white shadow-xl shadow-slate-200 rounded-[2.5rem] p-10 h-64"></div>
        </div>
      </div>
    )
  }

  if (!job) {
    return (
      <div className="min-h-screen bg-[#FBFDFF] flex items-center justify-center p-4">
        <div className="max-w-md w-full bg-white shadow-2xl rounded-[2.5rem] p-12 text-center">
          <h2 className="text-2xl font-black text-slate-900 mb-2">Job Not Found</h2>
          <p className="text-slate-500 mb-8">The position you're looking for doesn't exist or is no longer available.</p>
          <Link
            href="/employer/jobs"
            className="inline-block px-10 py-4 bg-slate-900 text-white font-bold rounded-2xl hover:bg-slate-800 transition-all"
          >
            Back to Dashboard
          </Link>
        </div>
      </div>
    )
  }

  const statusInfo = statusConfig[job.status]
  const applications = applicationsData?.applications || []
  const StatusIcon = statusInfo.icon

  return (
    <div className="min-h-screen bg-[#FBFDFF] pb-24 overflow-x-hidden">
      <div className="max-w-6xl mx-auto px-4 pt-12">
        {/* Navigation & Alerts */}
        <div className="mb-10 flex flex-col gap-6">
          <AnimationWrapper variant="fade" delay={0.1}>
            <Link
              href="/employer/jobs"
              className="group inline-flex items-center text-sm font-bold text-slate-500 hover:text-blue-600 transition-colors"
            >
              <div className="mr-3 p-1.5 rounded-lg bg-white border border-slate-200 group-hover:border-blue-200 group-hover:bg-blue-50 transition-all">
                <ChevronLeft className="w-4 h-4" />
              </div>
              Management Dashboard
            </Link>
          </AnimationWrapper>

          {(posted || updated) && (
            <AnimationWrapper variant="slide-down">
              <div className="bg-emerald-50 border border-emerald-100 rounded-2xl p-4 flex items-center shadow-lg shadow-emerald-500/5">
                <div className="w-10 h-10 bg-white rounded-full flex items-center justify-center mr-4 shadow-sm border border-emerald-100">
                  <CheckCircle2 className="w-5 h-5 text-emerald-500" />
                </div>
                <p className="text-emerald-900 font-bold">
                  {posted ? 'Great! Your job is now live.' : 'Success! Your changes have been saved.'}
                </p>
              </div>
            </AnimationWrapper>
          )}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <div className="lg:col-span-2 space-y-8">
            {/* Main Header Card */}
            <AnimationWrapper variant="slide-up" delay={0.2}>
              <div className="bg-white shadow-2xl shadow-slate-200 border border-slate-50 rounded-[2.5rem] p-8 md:p-12 overflow-hidden relative">
                {/* Subtle background element */}
                <div className="absolute top-0 right-0 -mr-16 -mt-16 w-64 h-64 bg-blue-50 rounded-full blur-3xl pointer-events-none"></div>

                <div className="relative z-10">
                  <div className="flex flex-wrap items-start justify-between gap-6 mb-8">
                    <div className="flex-1">
                      <div className="flex flex-wrap items-center gap-3 mb-6">
                        <span className={cn(
                          "px-4 py-1.5 rounded-full text-xs font-black uppercase tracking-widest border flex items-center gap-2",
                          statusInfo.className
                        )}>
                          <StatusIcon className="w-3.5 h-3.5" />
                          {statusInfo.label}
                        </span>
                        {job.featured && (
                          <span className="px-4 py-1.5 bg-amber-50 text-amber-700 text-xs font-black uppercase tracking-widest border border-amber-100 rounded-full flex items-center">
                            <Trophy className="w-3.5 h-3.5 mr-2 text-amber-500" />
                            Featured
                          </span>
                        )}
                      </div>
                      <h1 className="text-4xl md:text-5xl font-black text-slate-900 leading-tight mb-4 tracking-tighter">{job.title}</h1>
                      <div className="flex items-center text-xl text-slate-500 font-bold italic">
                        <Building2 className="w-6 h-6 mr-3 text-slate-300" />
                        {job.company}
                      </div>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6 pt-8 border-t border-slate-50">
                    <div className="flex items-center gap-4">
                      <div className="w-12 h-12 bg-blue-50 rounded-2xl flex items-center justify-center text-blue-600 shadow-sm border border-blue-100/50">
                        <MapPin className="w-6 h-6" />
                      </div>
                      <div>
                        <div className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Location</div>
                        <div className="font-bold text-slate-700 leading-tight">{job.location} {job.remote && <span className="text-[9px] px-1.5 py-0.5 bg-emerald-50 text-emerald-600 rounded-sm ml-1.5">REMOTE</span>}</div>
                      </div>
                    </div>
                    <div className="flex items-center gap-4">
                      <div className="w-12 h-12 bg-indigo-50 rounded-2xl flex items-center justify-center text-indigo-600 shadow-sm border border-indigo-100/50">
                        <Briefcase className="w-6 h-6" />
                      </div>
                      <div>
                        <div className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Type</div>
                        <div className="font-bold text-slate-700 capitalize leading-tight">{job.jobType?.replace('_', ' ') || 'N/A'}</div>
                      </div>
                    </div>
                    <div className="flex items-center gap-4">
                      <div className="w-12 h-12 bg-purple-50 rounded-2xl flex items-center justify-center text-purple-600 shadow-sm border border-purple-100/50">
                        <Layers className="w-6 h-6" />
                      </div>
                      <div>
                        <div className="text-[10px] font-black text-slate-400 uppercase tracking-widest">Experience</div>
                        <div className="font-bold text-slate-700 capitalize leading-tight">{job.experienceLevel}</div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </AnimationWrapper>

            {/* Performance Stats Cards */}
            <motion.div 
              variants={staggerContainer}
              initial="hidden"
              whileInView="visible"
              viewport={{ once: true }}
              className="grid grid-cols-2 md:grid-cols-4 gap-4 md:gap-6"
            >
              {[
                { label: 'Total Views', value: job.viewCount, icon: Eye, color: 'text-blue-600', bg: 'bg-blue-50' },
                { label: 'Applications', value: job.applicationCount || 0, icon: Users, color: 'text-emerald-600', bg: 'bg-emerald-50' },
                { label: 'Quality Score', value: `${Math.round(job.qualityScore)}%`, icon: BarChart3, color: 'text-indigo-600', bg: 'bg-indigo-50' },
                { label: 'Days Active', value: formatDistanceToNow(new Date(job.postedAt)).split(' ')[0], icon: Calendar, color: 'text-amber-600', bg: 'bg-amber-50' }
              ].map((stat, i) => (
                <motion.div 
                  variants={staggerItem}
                  key={i} 
                  className="bg-white p-6 rounded-[2rem] border border-slate-50 shadow-xl shadow-slate-200/50 group hover:border-blue-100 transition-all duration-300"
                >
                  <div className={cn("w-12 h-12 rounded-2xl flex items-center justify-center mb-5 transition-transform group-hover:scale-110 shadow-sm", stat.bg, stat.color)}>
                    <stat.icon className="w-6 h-6" />
                  </div>
                  <div className="text-3xl font-black text-slate-900 leading-tight mb-1">{stat.value}</div>
                  <div className="text-[10px] font-black text-slate-400 uppercase tracking-widest whitespace-nowrap">{stat.label}</div>
                </motion.div>
              ))}
            </motion.div>

            {/* Description Card */}
            <AnimationWrapper variant="slide-up" delay={0.3}>
              <div className="bg-white shadow-2xl shadow-slate-200 border border-slate-50 rounded-[2.5rem] p-8 md:p-12 transition-all">
                <h2 className="text-2xl font-black text-slate-900 mb-8 flex items-center gap-4">
                  <div className="w-2 h-8 bg-blue-600 rounded-full"></div>
                  Description Content
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

                {(job.requirements?.length || job.responsibilities?.length) && (
                  <div className="mt-12 pt-12 border-t border-slate-100 flex flex-col gap-12">
                    {job.requirements && job.requirements.length > 0 && (
                      <div className="animate-in fade-in duration-700">
                        <h3 className="text-xl font-black text-slate-900 mb-8 uppercase tracking-wider flex items-center gap-4 underline underline-offset-8 decoration-blue-500/20">
                          <CheckCircle2 className="w-6 h-6 text-emerald-500" />
                          Candidate Requirements
                        </h3>
                        <ul className="grid grid-cols-1 md:grid-cols-2 gap-5">
                          {job.requirements.map((req, index) => (
                            <li key={index} className="bg-slate-50 p-5 rounded-2xl text-sm font-bold text-slate-600 border border-slate-100 flex items-start gap-4 hover:bg-white hover:border-blue-100 transition-all group">
                              <div className="w-2 h-2 bg-emerald-500 rounded-full mt-1.5 flex-shrink-0 group-hover:scale-125 transition-transform shadow-[0_0_8px_rgba(16,185,129,0.3)]"></div>
                              {req}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {job.responsibilities && job.responsibilities.length > 0 && (
                      <div className="animate-in fade-in duration-700">
                        <h3 className="text-xl font-black text-slate-900 mb-8 uppercase tracking-wider flex items-center gap-4 underline underline-offset-8 decoration-indigo-500/20">
                          <BarChart3 className="w-6 h-6 text-indigo-500" />
                          Job Responsibilities
                        </h3>
                        <ul className="grid grid-cols-1 md:grid-cols-2 gap-5">
                          {job.responsibilities.map((resp, index) => (
                            <li key={index} className="bg-slate-50 p-5 rounded-2xl text-sm font-bold text-slate-600 border border-slate-100 flex items-start gap-4 hover:bg-white hover:border-blue-100 transition-all group">
                              <div className="w-2 h-2 bg-indigo-500 rounded-full mt-1.5 flex-shrink-0 group-hover:scale-125 transition-transform shadow-[0_0_8px_rgba(99,102,241,0.3)]"></div>
                              {resp}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </AnimationWrapper>
          </div>

          {/* Sidebar */}
          <div className="space-y-8">
            {/* Quick Actions Card */}
            <AnimationWrapper variant="slide-up" delay={0.4}>
              <div className="bg-slate-900 p-10 rounded-[2.5rem] text-white shadow-2xl shadow-blue-900/40 relative overflow-hidden group">
                <div className="absolute top-0 right-0 -mr-16 -mt-16 w-48 h-48 bg-blue-500/10 rounded-full blur-3xl group-hover:bg-blue-500/20 transition-all duration-700"></div>
                <h3 className="text-lg font-black text-white/40 mb-10 uppercase tracking-widest relative z-10">Admin Actions</h3>
                <div className="flex flex-col gap-5 relative z-10">
                  <Link
                    href={`/employer/jobs/${job.id}/edit`}
                    className="w-full py-4 bg-blue-600 text-white font-black rounded-2xl text-center hover:bg-blue-500 transition-all flex items-center justify-center gap-3 active:scale-95 shadow-xl shadow-blue-600/20 border border-blue-400/20"
                  >
                    <Edit3 className="w-5 h-5" />
                    Edit Position
                  </Link>
                  <Link
                    href={`/jobs/${job.id}`}
                    target="_blank"
                    className="w-full py-4 bg-white/5 text-white font-black rounded-2xl text-center hover:bg-white/10 transition-all flex items-center justify-center gap-3 active:scale-95 border border-white/10"
                  >
                    <Globe className="w-5 h-5 text-blue-400" />
                    View Live Page
                  </Link>
                </div>
              </div>
            </AnimationWrapper>

            {/* Applications Preview */}
            {job.sourceType === 'direct' && (
              <AnimationWrapper variant="slide-up" delay={0.5}>
                <div className="bg-white shadow-2xl shadow-slate-200 border border-slate-50 rounded-[2.5rem] p-8 overflow-hidden relative">
                  <div className="flex items-center justify-between mb-10">
                    <h3 className="text-lg font-black text-slate-900 uppercase tracking-widest">Applicants</h3>
                    <span className="px-4 py-1.5 bg-blue-50 text-blue-600 text-xs font-black rounded-xl border border-blue-100 shadow-sm">{applications.length}</span>
                  </div>

                  {applications.length === 0 ? (
                    <div className="text-center py-16 px-6 italic text-slate-400 font-bold border-4 border-dashed border-slate-50 rounded-[2.5rem] bg-slate-50/30">
                      Waiting for candidates...
                    </div>
                  ) : (
                    <div className="space-y-5">
                      {applications.slice(0, 5).map((app) => (
                        <div key={app.id} className="p-6 bg-slate-50 rounded-2xl border border-slate-100 group hover:border-blue-200 hover:bg-white transition-all shadow-sm hover:shadow-md">
                          <div className="flex items-center justify-between mb-3">
                            <p className="font-black text-slate-900 group-hover:text-blue-600 transition-colors uppercase tracking-tight truncate pr-2 text-sm">{app.applicant_name}</p>
                            <div className="text-[9px] font-black text-emerald-600 bg-emerald-50 px-2 py-1 rounded border border-emerald-100 uppercase tracking-tighter">{app.status}</div>
                          </div>
                          <p className="text-[10px] font-bold text-slate-400 italic mb-4 flex items-center gap-2">
                            <Clock className="w-3 h-3" />
                            {formatDistanceToNow(new Date(app.applied_at), { addSuffix: true })}
                          </p>
                          <a
                            href={app.resume}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-xs font-black text-blue-600 hover:text-blue-700 flex items-center gap-2 group-hover:translate-x-1 transition-transform"
                          >
                            Review Details <ChevronRight className="w-3.5 h-3.5" />
                          </a>
                        </div>
                      ))}
                      {applications.length > 5 && (
                        <Link
                          href={`/employer/applications?job=${job.id}`}
                          className="block text-center py-4 text-slate-400 hover:text-blue-600 font-black text-xs uppercase tracking-widest transition-colors border-t border-slate-50 mt-6"
                        >
                          Show all candidates ({applications.length})
                        </Link>
                      )}
                    </div>
                  )}
                </div>
              </AnimationWrapper>
            )}

            {/* Posting Info */}
            <AnimationWrapper variant="slide-up" delay={0.6}>
              <div className="bg-white shadow-xl shadow-slate-200 border border-slate-50 rounded-[2.5rem] p-10 font-bold text-sm">
                <div className="space-y-6">
                  <div className="flex justify-between items-center text-slate-400 border-b border-slate-50 pb-5">
                    <span className="flex items-center gap-3 text-xs uppercase tracking-widest font-black"><Calendar className="w-4 h-4 text-blue-500" /> Published</span>
                    <span className="text-slate-900 font-black tracking-tight text-base">{format(new Date(job.postedAt), 'MMM d, yyyy')}</span>
                  </div>
                  <div className="flex justify-between items-center text-slate-400 border-b border-slate-50 pb-5">
                    <span className="flex items-center gap-3 text-xs uppercase tracking-widest font-black"><AlertCircle className="w-4 h-4 text-amber-500" /> Expiring</span>
                    <span className="text-slate-900 font-black tracking-tight text-base">{format(new Date(job.expiresAt), 'MMM d, yyyy')}</span>
                  </div>
                  <div className="flex justify-between items-center text-slate-400">
                    <span className="flex items-center gap-3 text-xs uppercase tracking-widest font-black"><Globe className="w-4 h-4 text-emerald-500" /> Visibility</span>
                    <span className="px-3 py-1 bg-slate-900 text-white text-[10px] font-black rounded-lg uppercase tracking-widest shadow-lg shadow-slate-900/20">{job.sourceType}</span>
                  </div>
                </div>
              </div>
            </AnimationWrapper>
          </div>
        </div>
      </div>
    </div>
  )
}
