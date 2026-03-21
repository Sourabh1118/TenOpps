import apiClient from '@/lib/api-client'

export interface RateLimitViolation {
  timestamp: string
  endpoint: string
  count: number
}

export interface RateLimitViolationsResponse {
  user_id: string
  violations: RateLimitViolation[]
  total_violations: number
}

export interface Violator {
  user_id: string
  total_violations: number
  last_violation: string
}

export interface ViolatorsResponse {
  violators: Violator[]
  total: number
}

export interface RateLimitStats {
  total_requests: number
  total_violations: number
  violation_rate: number
  top_endpoints: Array<{
    endpoint: string
    violations: number
  }>
}

export const adminApi = {
  // Get rate limit violations for a user
  getRateLimitViolations: async (userId: string): Promise<RateLimitViolationsResponse> => {
    const response = await apiClient.get<RateLimitViolationsResponse>(`/admin/rate-limit/violations/${userId}`)
    return response.data
  },

  // Get top rate limit violators
  getRateLimitViolators: async (limit: number = 10): Promise<ViolatorsResponse> => {
    const response = await apiClient.get<ViolatorsResponse>('/admin/rate-limit/violators', {
      params: { limit },
    })
    return response.data
  },

  // Get rate limit statistics
  getRateLimitStats: async (): Promise<RateLimitStats> => {
    const response = await apiClient.get<RateLimitStats>('/admin/rate-limit/stats')
    return response.data
  },

  // Clear rate limit violations for a user
  clearRateLimitViolations: async (userId: string): Promise<{ message: string }> => {
    const response = await apiClient.delete<{ message: string }>(`/admin/rate-limit/violations/${userId}`)
    return response.data
  },
}
