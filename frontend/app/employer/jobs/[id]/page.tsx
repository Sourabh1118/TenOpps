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
  Layers
} from 'lucide-react'
import { cn } from '@/lib/utils'

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
    <div className="min-h-screen bg-[#FBFDFF] pb-24">
      <div className="max-w-6xl mx-auto px-4 pt-12">
        {/* Navigation & Alerts */}
        <div className="mb-10 flex flex-col gap-6">
          <Link
            href="/employer/jobs"
            className="group inline-flex items-center text-sm font-bold text-slate-500 hover:text-blue-600 transition-colors"
          >
            <div className="mr-3 p-1.5 rounded-lg bg-white border border-slate-200 group-hover:border-blue-200 group-hover:bg-blue-50 transition-all">
              <ChevronLeft className="w-4 h-4" />
            </div>
            Management Dashboard
          </Link>

          {(posted || updated) && (
            <div className="bg-emerald-50 border border-emerald-100 rounded-2xl p-4 flex items-center animate-in slide-in-from-top-2 duration-500">
              <div className="w-10 h-10 bg-white rounded-full flex items-center justify-center mr-4 shadow-sm border border-emerald-100">
                <CheckCircle2 className="w-5 h-5 text-emerald-500" />
              </div>
              <p className="text-emerald-900 font-bold">
                {posted ? 'Great! Your job is now live.' : 'Success! Your changes have been saved.'}
              </p>
            </div>
          )}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <div className="lg:col-span-2 space-y-8">
            {/* Main Header Card */}
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
                          <Trophy className="w-3.5 h-3.5 mr-2" />
                          Featured
                        </span>
                      )}
                    </div>
                    <h1 className="text-4xl md:text-5xl font-black text-slate-900 leading-tight mb-4">{job.title}</h1>
                    <div className="flex items-center text-xl text-slate-500 font-semibold italic">
                      <Building2 className="w-6 h-6 mr-3 text-slate-300" />
                      {job.company}
                    </div>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-6 pt-8 border-t border-slate-50">
                  <div className="flex items-center gap-4">
                    <div className="w-12 h-12 bg-blue-50 rounded-2xl flex items-center justify-center text-blue-600">
                      <MapPin className="w-6 h-6" />
                    </div>
                    <div>
                      <div className="text-xs font-black text-slate-400 uppercase tracking-widest">Location</div>
                      <div className="font-bold text-slate-700">{job.location} {job.remote && '(Remote)'}</div>
                    </div>
                  </div>
                  <div className="flex items-center gap-4">
                    <div className="w-12 h-12 bg-indigo-50 rounded-2xl flex items-center justify-center text-indigo-600">
                      <Briefcase className="w-6 h-6" />
                    </div>
                    <div>
                      <div className="text-xs font-black text-slate-400 uppercase tracking-widest">Type</div>
                      <div className="font-bold text-slate-700 capitalize">{job.jobType?.replace('_', ' ') || 'N/A'}</div>
                    </div>
                  </div>
                  <div className="flex items-center gap-4">
                    <div className="w-12 h-12 bg-purple-50 rounded-2xl flex items-center justify-center text-purple-600">
                      <Layers className="w-6 h-6" />
                    </div>
                    <div>
                      <div className="text-xs font-black text-slate-400 uppercase tracking-widest">Experience</div>
                      <div className="font-bold text-slate-700 capitalize">{job.experienceLevel}</div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Performance Stats Cards */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 md:gap-6">
              {[
                { label: 'Total Views', value: job.viewCount, icon: Eye, color: 'text-blue-600', bg: 'bg-blue-50' },
                { label: 'Applications', value: job.applicationCount || 0, icon: Users, color: 'text-emerald-600', bg: 'bg-emerald-50' },
                { label: 'Quality Score', value: `${Math.round(job.qualityScore)}%`, icon: BarChart3, color: 'text-indigo-600', bg: 'bg-indigo-50' },
                { label: 'Days Active', value: formatDistanceToNow(new Date(job.postedAt)).split(' ')[0], icon: Calendar, color: 'text-amber-600', bg: 'bg-amber-50' }
              ].map((stat, i) => (
                <div key={i} className="bg-white p-6 rounded-[2rem] border border-slate-50 shadow-lg shadow-slate-200/50">
                  <div className={cn("w-10 h-10 rounded-xl flex items-center justify-center mb-4 transition-transform hover:scale-110", stat.bg, stat.color)}>
                    <stat.icon className="w-5 h-5" />
                  </div>
                  <div className="text-2xl font-black text-slate-900 leading-tight">{stat.value}</div>
                  <div className="text-[10px] font-black text-slate-400 uppercase tracking-widest mt-1">{stat.label}</div>
                </div>
              ))}
            </div>

            {/* Description Card */}
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
                <div className="mt-12 pt-12 border-t border-slate-100 flex flex-col gap-10">
                  {job.requirements && job.requirements.length > 0 && (
                    <div className="animate-in fade-in duration-700">
                      <h3 className="text-xl font-black text-slate-900 mb-6 uppercase tracking-wider flex items-center gap-3">
                        <CheckCircle2 className="w-5 h-5 text-emerald-500" />
                        Candidate Requirements
                      </h3>
                      <ul className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {job.requirements.map((req, index) => (
                          <li key={index} className="bg-slate-50 p-4 rounded-2xl text-sm font-bold text-slate-600 border border-slate-100 flex items-start gap-3">
                            <div className="w-1.5 h-1.5 bg-emerald-500 rounded-full mt-1.5 flex-shrink-0"></div>
                            {req}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {job.responsibilities && job.responsibilities.length > 0 && (
                    <div className="animate-in fade-in duration-700">
                      <h3 className="text-xl font-black text-slate-900 mb-6 uppercase tracking-wider flex items-center gap-3">
                        <BarChart3 className="w-5 h-5 text-indigo-500" />
                        Job Responsibilities
                      </h3>
                      <ul className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {job.responsibilities.map((resp, index) => (
                          <li key={index} className="bg-slate-50 p-4 rounded-2xl text-sm font-bold text-slate-600 border border-slate-100 flex items-start gap-3">
                            <div className="w-1.5 h-1.5 bg-indigo-500 rounded-full mt-1.5 flex-shrink-0"></div>
                            {resp}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>

          {/* Sidebar */}
          <div className="space-y-8">
            {/* Quick Actions Card */}
            <div className="bg-slate-900 p-8 rounded-[2.5rem] text-white shadow-2xl shadow-blue-900/20">
              <h3 className="text-lg font-black text-white/50 mb-8 uppercase tracking-widest">Admin Actions</h3>
              <div className="flex flex-col gap-4">
                <Link
                  href={`/employer/jobs/${job.id}/edit`}
                  className="w-full py-4 bg-blue-600 text-white font-black rounded-2xl text-center hover:bg-blue-500 transition-all flex items-center justify-center gap-3 active:scale-95 shadow-xl shadow-blue-600/20"
                >
                  <Edit3 className="w-5 h-5" />
                  Edit Position
                </Link>
                <Link
                  href={`/jobs/${job.id}`}
                  target="_blank"
                  className="w-full py-4 bg-white/10 text-white font-black rounded-2xl text-center hover:bg-white/20 transition-all flex items-center justify-center gap-3 active:scale-95 border border-white/10"
                >
                  <Globe className="w-5 h-5" />
                  View Public Page
                </Link>
              </div>
            </div>

            {/* Applications Preview */}
            {job.sourceType === 'direct' && (
              <div className="bg-white shadow-lg shadow-slate-200 border border-slate-50 rounded-[2.5rem] p-8 overflow-hidden relative">
                <div className="flex items-center justify-between mb-8">
                  <h3 className="text-lg font-black text-slate-900 uppercase tracking-widest">Applicants</h3>
                  <span className="px-3 py-1 bg-blue-50 text-blue-600 text-xs font-black rounded-lg border border-blue-100">{applications.length}</span>
                </div>

                {applications.length === 0 ? (
                  <div className="text-center py-12 px-4 italic text-slate-400 font-semibold border-2 border-dashed border-slate-100 rounded-[2rem]">
                    Waiting for candidates...
                  </div>
                ) : (
                  <div className="space-y-4">
                    {applications.slice(0, 5).map((app) => (
                      <div key={app.id} className="p-5 bg-slate-50 rounded-2xl border border-slate-100 group hover:border-blue-200 transition-all">
                        <div className="flex items-center justify-between mb-2">
                          <p className="font-black text-slate-900 group-hover:text-blue-600 transition-colors uppercase tracking-tight truncate pr-2">{app.applicant_name}</p>
                          <div className="text-[10px] font-black text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-100">{app.status}</div>
                        </div>
                        <p className="text-[10px] font-bold text-slate-400 italic mb-3">
                          {formatDistanceToNow(new Date(app.applied_at), { addSuffix: true })}
                        </p>
                        <a
                          href={app.resume}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-xs font-black text-blue-600 hover:text-blue-700 underline underline-offset-4 decoration-2"
                        >
                          Review Resume →
                        </a>
                      </div>
                    ))}
                    {applications.length > 5 && (
                      <Link
                        href={`/employer/applications?job=${job.id}`}
                        className="block text-center py-3 text-slate-400 hover:text-blue-600 font-black text-xs uppercase tracking-widest transition-colors"
                      >
                        All Applications ({applications.length})
                      </Link>
                    )}
                  </div>
                )}
              </div>
            )}

            {/* Posting Info */}
            <div className="bg-white shadow-lg shadow-slate-200 border border-slate-50 rounded-[2.5rem] p-8 font-bold text-sm">
              <div className="space-y-4">
                <div className="flex justify-between items-center text-slate-500 border-b border-slate-50 pb-4">
                  <span className="flex items-center gap-2"><Calendar className="w-4 h-4" /> Posted</span>
                  <span className="text-slate-900 font-black tracking-tight">{format(new Date(job.postedAt), 'MMM d, yyyy')}</span>
                </div>
                <div className="flex justify-between items-center text-slate-500 border-b border-slate-50 pb-4">
                  <span className="flex items-center gap-2"><AlertCircle className="w-4 h-4" /> Expires</span>
                  <span className="text-slate-900 font-black tracking-tight">{format(new Date(job.expiresAt), 'MMM d, yyyy')}</span>
                </div>
                <div className="flex justify-between items-center text-slate-500">
                  <span className="flex items-center gap-2"><Globe className="w-4 h-4" /> Strategy</span>
                  <span className="px-2 py-0.5 bg-slate-900 text-white text-[10px] font-black rounded uppercase tracking-tighter">{job.sourceType}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
