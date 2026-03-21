import apiClient from '@/lib/api-client'

export interface ScrapingMetric {
  source_platform: string
  total_tasks: number
  successful_tasks: number
  failed_tasks: number
  jobs_found: number
  jobs_created: number
  jobs_updated: number
  success_rate: number
  avg_duration_seconds: number
}

export interface PopularSearch {
  query: string
  count: number
}

export interface JobAnalytics {
  job_id: string
  view_count: number
  application_count: number
  views_by_day: Array<{ date: string; count: number }>
  applications_by_day: Array<{ date: string; count: number }>
}

export interface EmployerAnalyticsSummary {
  total_jobs: number
  active_jobs: number
  expired_jobs: number
  filled_jobs: number
  total_views: number
  total_applications: number
  avg_applications_per_job: number
  top_performing_jobs: Array<{
    job_id: string
    title: string
    view_count: number
    application_count: number
  }>
}

export interface SystemHealthMetric {
  metric_name: string
  value: number
  timestamp: string
  status: 'healthy' | 'warning' | 'critical'
}

export interface SlowAPIRequest {
  endpoint: string
  method: string
  duration_ms: number
  timestamp: string
  status_code: number
}

export const analyticsApi = {
  // Get scraping metrics
  getScrapingMetrics: async (sourcePlatform?: string): Promise<ScrapingMetric[]> => {
    const response = await apiClient.get<ScrapingMetric[]>('/analytics/scraping', {
      params: { source_platform: sourcePlatform },
    })
    return response.data
  },

  // Get popular searches
  getPopularSearches: async (limit: number = 10): Promise<PopularSearch[]> => {
    const response = await apiClient.get<PopularSearch[]>('/analytics/searches/popular', {
      params: { limit },
    })
    return response.data
  },

  // Get job analytics
  getJobAnalytics: async (jobId: string): Promise<JobAnalytics> => {
    const response = await apiClient.get<JobAnalytics>(`/analytics/jobs/${jobId}`)
    return response.data
  },

  // Get employer analytics summary
  getEmployerAnalyticsSummary: async (days: number = 30): Promise<EmployerAnalyticsSummary> => {
    const response = await apiClient.get<EmployerAnalyticsSummary>('/analytics/employer/summary', {
      params: { days },
    })
    return response.data
  },

  // Get system health metrics (admin only)
  getSystemHealthMetrics: async (metricName?: string): Promise<SystemHealthMetric[]> => {
    const response = await apiClient.get<SystemHealthMetric[]>('/analytics/system/health', {
      params: { metric_name: metricName },
    })
    return response.data
  },

  // Get slow API requests (admin only)
  getSlowAPIRequests: async (thresholdMs: number = 1000, limit: number = 50): Promise<SlowAPIRequest[]> => {
    const response = await apiClient.get<SlowAPIRequest[]>('/analytics/api/slow-requests', {
      params: { threshold_ms: thresholdMs, limit },
    })
    return response.data
  },
}
