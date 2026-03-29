import apiClient from '@/lib/api-client'
import type { SearchFilters, Job } from '@/types'

export interface SearchParams extends SearchFilters {
  page?: number
  page_size?: number
}

export interface SearchResponse {
  jobs: Job[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export const searchApi = {
  // Search jobs with filters
  searchJobs: async (params: SearchParams): Promise<SearchResponse> => {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const response = await apiClient.get<any>('/jobs/search', {
      params: {
        query: params.query,
        location: params.location,
        jobType: params.jobType, // Axios will repeat key for array
        experienceLevel: params.experienceLevel,
        salaryMin: params.salaryMin,
        salaryMax: params.salaryMax,
        remote: params.remote,
        postedWithin: params.postedWithin,
        sourceType: params.sourceType,
        page: params.page || 1,
        page_size: params.page_size || 20,
      },
    })
    
    // Transform snake_case to camelCase for frontend
    return {
      total: response.data.total,
      page: response.data.page,
      page_size: response.data.page_size,
      total_pages: response.data.total_pages,
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      jobs: response.data.jobs.map((job: any) => ({
        id: job.id,
        title: job.title,
        company: job.company,
        location: job.location,
        remote: job.remote,
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        jobType: job.job_type as any,
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        experienceLevel: job.experience_level as any,
        description: job.description,
        requirements: job.requirements,
        responsibilities: job.responsibilities,
        salaryMin: job.salary_min,
        salaryMax: job.salary_max,
        salaryCurrency: job.salary_currency,
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        sourceType: job.source_type as any,
        sourceUrl: job.source_url,
        sourcePlatform: job.source_platform,
        employerId: job.employer_id,
        qualityScore: job.quality_score,
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        status: job.status as any,
        postedAt: job.posted_at,
        expiresAt: job.expires_at,
        createdAt: job.created_at,
        updatedAt: job.updated_at,
        applicationCount: job.application_count,
        viewCount: job.view_count,
        featured: job.featured,
        tags: job.tags || [],
      })),
    }
  },
}
