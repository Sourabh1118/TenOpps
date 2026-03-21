import apiClient from '@/lib/api-client'
import { LoginRequest } from '@/types'

export interface LoginResponse {
  user_id: string
  role: 'employer' | 'job_seeker' | 'admin'
  access_token: string
  refresh_token: string
  token_type: string
}

export interface RegistrationResponse {
  user_id: string
  role: 'employer' | 'job_seeker'
  access_token: string
  refresh_token: string
  token_type: string
}

export interface EmployerRegistrationRequest {
  email: string
  password: string
  company_name: string
  company_website?: string
  company_description?: string
}

export interface JobSeekerRegistrationRequest {
  email: string
  password: string
  full_name: string
  phone?: string
}

export const authApi = {
  login: async (data: LoginRequest): Promise<LoginResponse> => {
    const response = await apiClient.post<LoginResponse>('/auth/login', data)
    return response.data
  },

  registerEmployer: async (data: EmployerRegistrationRequest): Promise<RegistrationResponse> => {
    const response = await apiClient.post<RegistrationResponse>('/auth/register/employer', data)
    return response.data
  },

  registerJobSeeker: async (data: JobSeekerRegistrationRequest): Promise<RegistrationResponse> => {
    const response = await apiClient.post<RegistrationResponse>('/auth/register/job-seeker', data)
    return response.data
  },

  logout: async (refreshToken: string): Promise<void> => {
    await apiClient.post('/auth/logout', { refresh_token: refreshToken })
  },

  refreshToken: async (refreshToken: string): Promise<{ access_token: string; token_type: string }> => {
    const response = await apiClient.post('/auth/refresh', { refresh_token: refreshToken })
    return response.data
  },
}
