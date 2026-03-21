import apiClient from '@/lib/api-client'
import type { Job } from '@/types'

export interface JobCreateRequest {
  title: string
  company: string
  location: string
  remote: boolean
  job_type: string
  experience_level: string
  description: string
  requirements?: string[]
  responsibilities?: string[]
  salary_min?: number
  salary_max?: number
  salary_currency?: string
  expires_at: string
  featured?: boolean
  tags?: string[]
}

export interface JobUpdateRequest {
  title?: string
  location?: string
  remote?: boolean
  job_type?: string
  experience_level?: string
  description?: string
  requirements?: string[]
  responsibilities?: string[]
  salary_min?: number
  salary_max?: number
  salary_currency?: string
  expires_at?: string
  tags?: string[]
}

export interface JobCreateResponse {
  job_id: string
  message: string
}

export interface JobListResponse {
  jobs: Job[]
  total: number
  page: number
  page_size: number
}

export interface JobReactivateRequest {
  expires_at: string
}

export const jobsApi = {
  // Create a direct job post
  createDirectJob: async (data: JobCreateRequest): Promise<JobCreateResponse> => {
    const response = await apiClient.post<JobCreateResponse>('/jobs/direct', data)
    return response.data
  },

  // Get job by ID
  getJobById: async (jobId: string): Promise<Job> => {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const response = await apiClient.get<any>(`/jobs/${jobId}`)
    const job = response.data
    
    // Transform snake_case to camelCase
    return {
      id: job.id,
      title: job.title,
      company: job.company,
      location: job.location,
      remote: job.remote,
      jobType: job.job_type,
      experienceLevel: job.experience_level,
      description: job.description,
      requirements: job.requirements,
      responsibilities: job.responsibilities,
      salaryMin: job.salary_min,
      salaryMax: job.salary_max,
      salaryCurrency: job.salary_currency,
      sourceType: job.source_type,
      sourceUrl: job.source_url,
      sourcePlatform: job.source_platform,
      employerId: job.employer_id,
      qualityScore: job.quality_score,
      status: job.status,
      postedAt: job.posted_at,
      expiresAt: job.expires_at,
      createdAt: job.created_at,
      updatedAt: job.updated_at,
      applicationCount: job.application_count,
      viewCount: job.view_count,
      featured: job.featured,
      tags: job.tags || [],
    }
  },

  // Get jobs by employer
  getJobsByEmployer: async (employerId: string, page: number = 1, pageSize: number = 20): Promise<JobListResponse> => {
    const response = await apiClient.get<JobListResponse>(`/jobs/employer/${employerId}`, {
      params: { page, page_size: pageSize },
    })
    return response.data
  },

  // Update job
  updateJob: async (jobId: string, data: JobUpdateRequest): Promise<Job> => {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const response = await apiClient.patch<any>(`/jobs/${jobId}`, data)
    const job = response.data
    
    // Transform snake_case to camelCase
    return {
      id: job.id,
      title: job.title,
      company: job.company,
      location: job.location,
      remote: job.remote,
      jobType: job.job_type,
      experienceLevel: job.experience_level,
      description: job.description,
      requirements: job.requirements,
      responsibilities: job.responsibilities,
      salaryMin: job.salary_min,
      salaryMax: job.salary_max,
      salaryCurrency: job.salary_currency,
      sourceType: job.source_type,
      sourceUrl: job.source_url,
      sourcePlatform: job.source_platform,
      employerId: job.employer_id,
      qualityScore: job.quality_score,
      status: job.status,
      postedAt: job.posted_at,
      expiresAt: job.expires_at,
      createdAt: job.created_at,
      updatedAt: job.updated_at,
      applicationCount: job.application_count,
      viewCount: job.view_count,
      featured: job.featured,
      tags: job.tags || [],
    }
  },

  // Delete job
  deleteJob: async (jobId: string): Promise<{ message: string }> => {
    const response = await apiClient.delete<{ message: string }>(`/jobs/${jobId}`)
    return response.data
  },

  // Mark job as filled
  markJobAsFilled: async (jobId: string): Promise<{ message: string }> => {
    const response = await apiClient.post<{ message: string }>(`/jobs/${jobId}/mark-filled`)
    return response.data
  },

  // Increment job view count
  incrementViewCount: async (jobId: string): Promise<{ message: string }> => {
    const response = await apiClient.post<{ message: string }>(`/jobs/${jobId}/increment-view`)
    return response.data
  },

  // Feature a job
  featureJob: async (jobId: string): Promise<{ message: string }> => {
    const response = await apiClient.post<{ message: string }>(`/jobs/${jobId}/feature`)
    return response.data
  },

  // Reactivate expired job
  reactivateJob: async (jobId: string, data: JobReactivateRequest): Promise<Job> => {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const response = await apiClient.post<any>(`/jobs/${jobId}/reactivate`, data)
    const job = response.data
    
    // Transform snake_case to camelCase
    return {
      id: job.id,
      title: job.title,
      company: job.company,
      location: job.location,
      remote: job.remote,
      jobType: job.job_type,
      experienceLevel: job.experience_level,
      description: job.description,
      requirements: job.requirements,
      responsibilities: job.responsibilities,
      salaryMin: job.salary_min,
      salaryMax: job.salary_max,
      salaryCurrency: job.salary_currency,
      sourceType: job.source_type,
      sourceUrl: job.source_url,
      sourcePlatform: job.source_platform,
      employerId: job.employer_id,
      qualityScore: job.quality_score,
      status: job.status,
      postedAt: job.posted_at,
      expiresAt: job.expires_at,
      createdAt: job.created_at,
      updatedAt: job.updated_at,
      applicationCount: job.application_count,
      viewCount: job.view_count,
      featured: job.featured,
      tags: job.tags || [],
    }
  },
}
