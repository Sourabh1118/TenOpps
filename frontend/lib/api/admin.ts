/**
 * Admin API Client
 * 
 * API functions for admin operations including:
 * - Platform statistics
 * - User management
 * - Rate limit monitoring
 * - System health
 */

import apiClient from '../api-client'

// Types
export interface PlatformStats {
  total_users: number
  total_employers: number
  total_job_seekers: number
  total_jobs: number
  total_applications: number
  active_jobs: number
  jobs_posted_today: number
  applications_today: number
}

export interface UserListItem {
  id: string
  email: string
  role: 'admin' | 'employer' | 'job_seeker'
  created_at: string
  full_name?: string
  company_name?: string
}

export interface RateLimitViolation {
  timestamp: string
  user_id: string
  path: string
  count: number
  limit: number
}

export interface RateLimitStats {
  total_violators: number
  time_window_hours: number
  top_violators: Array<{
    user_id: string
    violation_count: number
  }>
}

/**
 * Get platform statistics
 */
export async function getPlatformStats(): Promise<PlatformStats> {
  const response = await apiClient.get('/admin/stats')
  return response.data
}

/**
 * Get all users (paginated)
 */
export async function getUsers(params?: {
  role?: 'admin' | 'employer' | 'job_seeker'
  page?: number
  limit?: number
}): Promise<{ users: UserListItem[]; total: number }> {
  const response = await apiClient.get('/admin/users', { params })
  return response.data
}

/**
 * Get rate limit violations for a user
 */
export async function getUserViolations(
  userId: string,
  limit: number = 100
): Promise<{ user_id: string; violations: RateLimitViolation[]; total_count: number }> {
  const response = await apiClient.get(`/admin/rate-limit/violations/${userId}`, {
    params: { limit }
  })
  return response.data
}

/**
 * Get list of users with rate limit violations
 */
export async function getViolators(
  hours: number = 24
): Promise<{ violators: string[]; total_count: number; time_window_hours: number }> {
  const response = await apiClient.get('/admin/rate-limit/violators', {
    params: { hours }
  })
  return response.data
}

/**
 * Get rate limit statistics
 */
export async function getRateLimitStats(
  hours: number = 24,
  topN: number = 10
): Promise<RateLimitStats> {
  const response = await apiClient.get('/admin/rate-limit/stats', {
    params: { hours, top_n: topN }
  })
  return response.data
}

/**
 * Clear rate limit violations for a user
 */
export async function clearUserViolations(userId: string): Promise<{ message: string }> {
  const response = await apiClient.delete(`/admin/rate-limit/violations/${userId}`)
  return response.data
}

/**
 * Delete a user (admin only)
 */
export async function deleteUser(userId: string): Promise<{ message: string }> {
  const response = await apiClient.delete(`/admin/users/${userId}`)
  return response.data
}

/**
 * Update user status (ban/unban)
 */
export async function updateUserStatus(
  userId: string,
  status: 'active' | 'banned'
): Promise<{ message: string }> {
  const response = await apiClient.patch(`/admin/users/${userId}/status`, { status })
  return response.data
}

// ─────────────────────────────────────
// Jobs Management
// ─────────────────────────────────────

export interface AdminJobItem {
  id: string
  title: string
  company: string
  location: string
  status: string
  source_platform: string | null
  source_type: string
  posted_at: string | null
  created_at: string
  application_count: number
  view_count: number
}

/**
 * Get all jobs (admin view) with optional filters
 */
export async function getAdminJobs(params?: {
  search?: string
  status?: string
  source?: string
  page?: number
  limit?: number
}): Promise<{ jobs: AdminJobItem[]; total: number; page: number; limit: number }> {
  const response = await apiClient.get('/admin/jobs', { params })
  return response.data
}

/**
 * Activate or deactivate a job
 */
export async function updateJobStatus(
  jobId: string,
  status: 'active' | 'expired'
): Promise<{ message: string }> {
  const response = await apiClient.patch(`/admin/jobs/${jobId}/status`, { status })
  return response.data
}

// ─────────────────────────────────────
// Scraping Monitor
// ─────────────────────────────────────

export interface ScrapingSourceStatus {
  source: string
  circuit_open: boolean
  failure_count: number
  cooldown_seconds: number | null
}

export interface ScrapingStatus {
  sources: ScrapingSourceStatus[]
  recent_tasks: Array<{
    id: string
    task_type: string
    source_platform: string | null
    status: string
    jobs_found: number
    jobs_created: number
    jobs_updated: number
    error_message: string | null
    created_at: string | null
    completed_at: string | null
  }>
}

/**
 * Get scraping system status (circuit breakers + recent tasks)
 */
export async function getScrapingStatus(): Promise<ScrapingStatus> {
  const response = await apiClient.get('/admin/scraping/status')
  return response.data
}

/**
 * Manually trigger a scraping job for a source
 */
export async function triggerScrape(source: string): Promise<{ message: string; task_id: string }> {
  const response = await apiClient.post(`/admin/scraping/trigger/${source}`)
  return response.data
}

