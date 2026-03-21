import apiClient from '@/lib/api-client'
import { Application, ApplicationStatus } from '@/types'

export interface ApplicationSubmitRequest {
  job_id: string
  resume: string
  cover_letter?: string
}

export interface ApplicationSubmitResponse {
  application_id: string
  message: string
}

export interface ApplicationStatusUpdateRequest {
  status: ApplicationStatus
  employer_notes?: string
}

export interface ApplicationWithJobSeekerInfo {
  id: string
  job_id: string
  job_seeker_id: string
  applicant_name: string
  resume: string
  cover_letter?: string
  status: ApplicationStatus
  employer_notes?: string
  applied_at: string
  updated_at: string
}

export interface ApplicationWithJobInfo {
  id: string
  job_id: string
  job_title: string
  company: string
  location: string
  resume: string
  cover_letter?: string
  status: ApplicationStatus
  applied_at: string
  updated_at: string
}

export interface ApplicationListResponse {
  applications: ApplicationWithJobSeekerInfo[]
  total: number
}

export interface MyApplicationsListResponse {
  applications: ApplicationWithJobInfo[]
  total: number
}

export const applicationsApi = {
  // Submit a job application
  submitApplication: async (data: ApplicationSubmitRequest): Promise<ApplicationSubmitResponse> => {
    const response = await apiClient.post<ApplicationSubmitResponse>('/applications', data)
    return response.data
  },

  // Get applications for a job (employer only)
  getApplicationsForJob: async (jobId: string): Promise<ApplicationListResponse> => {
    const response = await apiClient.get<ApplicationListResponse>(`/applications/job/${jobId}`)
    return response.data
  },

  // Update application status (employer only)
  updateApplicationStatus: async (
    applicationId: string,
    data: ApplicationStatusUpdateRequest
  ): Promise<Application> => {
    const response = await apiClient.patch<Application>(`/applications/${applicationId}`, data)
    return response.data
  },

  // Get my applications (job seeker only)
  getMyApplications: async (): Promise<MyApplicationsListResponse> => {
    const response = await apiClient.get<MyApplicationsListResponse>('/applications/my-applications')
    return response.data
  },
}
