import apiClient from '@/lib/api-client'
import { SubscriptionTier } from '@/types'

export interface SubscriptionUpdateRequest {
  new_tier: SubscriptionTier
}

export interface SubscriptionUpdateResponse {
  employer_id: string
  tier: string
  start_date: string
  end_date: string
  monthly_posts_used: number
  featured_posts_used: number
  message: string
}

export interface SubscriptionInfoResponse {
  employer_id: string
  tier: string
  start_date: string
  end_date: string
  is_active: boolean
  monthly_posts_used: number
  monthly_posts_limit: number
  featured_posts_used: number
  featured_posts_limit: number
  has_application_tracking: boolean
  has_analytics: boolean
}

export const subscriptionsApi = {
  // Get subscription info
  getSubscriptionInfo: async (): Promise<SubscriptionInfoResponse> => {
    const response = await apiClient.get<SubscriptionInfoResponse>('/subscription/info')
    return response.data
  },

  // Update subscription tier
  updateSubscription: async (data: SubscriptionUpdateRequest): Promise<SubscriptionUpdateResponse> => {
    const response = await apiClient.post<SubscriptionUpdateResponse>('/subscription/update', data)
    return response.data
  },

  // Cancel subscription (downgrade to free at period end)
  cancelSubscription: async (): Promise<SubscriptionUpdateResponse> => {
    const response = await apiClient.post<SubscriptionUpdateResponse>('/subscription/cancel')
    return response.data
  },
}
