import apiClient from '@/lib/api-client'

export interface URLImportRequest {
  url: string
}

export interface URLImportResponse {
  task_id: string
  message: string
}

export interface ImportStatusResponse {
  task_id: string
  status: 'PENDING' | 'RUNNING' | 'COMPLETED' | 'FAILED'
  job_id?: string
  error_message?: string
  created_at: string
  completed_at?: string
}

export const urlImportApi = {
  // Import job from URL
  importJobFromURL: async (data: URLImportRequest): Promise<URLImportResponse> => {
    const response = await apiClient.post<URLImportResponse>('/url-import/import-url', data)
    return response.data
  },

  // Get import task status
  getImportStatus: async (taskId: string): Promise<ImportStatusResponse> => {
    const response = await apiClient.get<ImportStatusResponse>(`/url-import/import-status/${taskId}`)
    return response.data
  },
}
