/**
 * Central API client exports
 * 
 * This module provides typed API client functions for all backend endpoints.
 * All clients use the configured axios instance with JWT token handling.
 */

export { authApi } from './auth'
export type {
  LoginResponse,
  RegistrationResponse,
  EmployerRegistrationRequest,
  JobSeekerRegistrationRequest,
} from './auth'

export { jobsApi } from './jobs'
export type {
  JobCreateRequest,
  JobUpdateRequest,
  JobCreateResponse,
  JobListResponse,
  JobReactivateRequest,
} from './jobs'

export { searchApi } from './search'
export type { SearchParams, SearchResponse } from './search'

export { applicationsApi } from './applications'
export type {
  ApplicationSubmitRequest,
  ApplicationSubmitResponse,
  ApplicationStatusUpdateRequest,
  ApplicationWithJobSeekerInfo,
  ApplicationWithJobInfo,
  ApplicationListResponse,
  MyApplicationsListResponse,
} from './applications'

export { subscriptionsApi } from './subscriptions'
export type {
  SubscriptionUpdateRequest,
  SubscriptionUpdateResponse,
  SubscriptionInfoResponse,
} from './subscriptions'

export { urlImportApi } from './url-import'
export type {
  URLImportRequest,
  URLImportResponse,
  ImportStatusResponse,
} from './url-import'

export { analyticsApi } from './analytics'
export type {
  ScrapingMetric,
  PopularSearch,
  JobAnalytics,
  EmployerAnalyticsSummary,
  SystemHealthMetric,
  SlowAPIRequest,
} from './analytics'

export { adminApi } from './admin'
export type {
  RateLimitViolation,
  RateLimitViolationsResponse,
  Violator,
  ViolatorsResponse,
  RateLimitStats,
} from './admin'
