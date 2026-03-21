// Core type definitions for the Job Aggregation Platform

export enum JobType {
  FULL_TIME = 'FULL_TIME',
  PART_TIME = 'PART_TIME',
  CONTRACT = 'CONTRACT',
  FREELANCE = 'FREELANCE',
  INTERNSHIP = 'INTERNSHIP',
  FELLOWSHIP = 'FELLOWSHIP',
  ACADEMIC = 'ACADEMIC',
}

export enum ExperienceLevel {
  ENTRY = 'ENTRY',
  MID = 'MID',
  SENIOR = 'SENIOR',
  LEAD = 'LEAD',
  EXECUTIVE = 'EXECUTIVE',
}

export enum SourceType {
  DIRECT = 'direct',
  URL_IMPORT = 'url_import',
  AGGREGATED = 'aggregated',
}

export enum JobStatus {
  ACTIVE = 'ACTIVE',
  EXPIRED = 'EXPIRED',
  FILLED = 'FILLED',
  DELETED = 'DELETED',
}

export enum ApplicationStatus {
  SUBMITTED = 'SUBMITTED',
  REVIEWED = 'REVIEWED',
  SHORTLISTED = 'SHORTLISTED',
  REJECTED = 'REJECTED',
  ACCEPTED = 'ACCEPTED',
}

export enum SubscriptionTier {
  FREE = 'free',
  BASIC = 'basic',
  PREMIUM = 'premium',
}

export interface Job {
  id: string
  title: string
  company: string
  location: string
  remote: boolean
  jobType: JobType
  experienceLevel: ExperienceLevel
  description: string
  requirements?: string[]
  responsibilities?: string[]
  salaryMin?: number
  salaryMax?: number
  salaryCurrency?: string
  sourceType: SourceType
  sourceUrl?: string
  sourcePlatform?: string
  employerId?: string
  qualityScore: number
  status: JobStatus
  postedAt: string
  expiresAt: string
  createdAt: string
  updatedAt: string
  applicationCount?: number
  viewCount: number
  featured: boolean
  tags: string[]
}

export interface Employer {
  id: string
  email: string
  companyName: string
  companyWebsite?: string
  companyLogo?: string
  companyDescription?: string
  subscriptionTier: SubscriptionTier
  subscriptionStartDate: string
  subscriptionEndDate: string
  monthlyPostsUsed: number
  featuredPostsUsed: number
  stripeCustomerId?: string
  verified: boolean
  createdAt: string
  updatedAt: string
}

export interface Application {
  id: string
  jobId: string
  jobSeekerId: string
  resume: string
  coverLetter?: string
  status: ApplicationStatus
  appliedAt: string
  updatedAt: string
  employerNotes?: string
}

export interface SearchFilters {
  query?: string
  location?: string
  jobType?: JobType[]
  experienceLevel?: ExperienceLevel[]
  salaryMin?: number
  salaryMax?: number
  postedWithin?: number
  remote?: boolean
  sourceType?: SourceType[]
}

export interface PaginatedJobs {
  jobs: Job[]
  total: number
  page: number
  pageSize: number
  totalPages: number
}

export interface JobCreateDTO {
  title: string
  company: string
  location: string
  remote: boolean
  jobType: JobType
  experienceLevel: ExperienceLevel
  description: string
  requirements?: string[]
  responsibilities?: string[]
  salaryMin?: number
  salaryMax?: number
  salaryCurrency?: string
  tags?: string[]
  expiresAt?: string
}

export interface JobUpdateDTO {
  title?: string
  location?: string
  remote?: boolean
  jobType?: JobType
  experienceLevel?: ExperienceLevel
  description?: string
  requirements?: string[]
  responsibilities?: string[]
  salaryMin?: number
  salaryMax?: number
  salaryCurrency?: string
  tags?: string[]
  status?: JobStatus
}

export interface URLImportRequest {
  url: string
}

export interface URLImportResponse {
  taskId: string
  status: string
}

export interface ImportTaskStatus {
  taskId: string
  status: 'PENDING' | 'RUNNING' | 'COMPLETED' | 'FAILED'
  jobId?: string
  error?: string
}

export interface AuthTokens {
  accessToken: string
  refreshToken: string
  tokenType: string
}

export interface LoginRequest {
  email: string
  password: string
}

export interface RegisterRequest {
  email: string
  password: string
  companyName?: string
  role: 'employer' | 'job_seeker'
}

export interface User {
  id: string
  email: string
  role: 'employer' | 'job_seeker' | 'admin'
  createdAt: string
}

export interface SubscriptionLimits {
  monthlyPosts: number
  featuredPosts: number
  applicationTracking: boolean
  analyticsAccess: boolean
}

export interface ApiError {
  message: string
  detail?: string
  statusCode: number
}
