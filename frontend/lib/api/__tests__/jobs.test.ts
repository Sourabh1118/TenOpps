/**
 * Jobs API Client Tests
 */

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { jobsApi } from '../jobs'
import apiClient from '@/lib/api-client'

vi.mock('@/lib/api-client')

describe('Jobs API', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('createDirectJob', () => {
    it('should create a direct job post', async () => {
      const mockRequest = {
        title: 'Senior Software Engineer',
        company: 'Tech Corp',
        location: 'San Francisco, CA',
        remote: true,
        job_type: 'FULL_TIME',
        experience_level: 'SENIOR',
        description: 'We are looking for a senior software engineer...',
        expires_at: '2024-12-31T23:59:59Z',
      }

      const mockResponse = {
        job_id: '123e4567-e89b-12d3-a456-426614174000',
        message: 'Job created successfully',
      }

      vi.mocked(apiClient.post).mockResolvedValue({ data: mockResponse })

      const result = await jobsApi.createDirectJob(mockRequest)

      expect(apiClient.post).toHaveBeenCalledWith('/jobs/direct', mockRequest)
      expect(result).toEqual(mockResponse)
    })
  })

  describe('getJobById', () => {
    it('should fetch a job by ID', async () => {
      const jobId = '123e4567-e89b-12d3-a456-426614174000'
      const mockJob = {
        id: jobId,
        title: 'Senior Software Engineer',
        company: 'Tech Corp',
      }

      vi.mocked(apiClient.get).mockResolvedValue({ data: mockJob })

      const result = await jobsApi.getJobById(jobId)

      expect(apiClient.get).toHaveBeenCalledWith(`/jobs/${jobId}`)
      expect(result).toEqual(mockJob)
    })
  })

  describe('updateJob', () => {
    it('should update a job', async () => {
      const jobId = '123e4567-e89b-12d3-a456-426614174000'
      const updateData = {
        title: 'Updated Title',
        description: 'Updated description with more details about the role',
      }

      const mockResponse = {
        id: jobId,
        ...updateData,
      }

      vi.mocked(apiClient.patch).mockResolvedValue({ data: mockResponse })

      const result = await jobsApi.updateJob(jobId, updateData)

      expect(apiClient.patch).toHaveBeenCalledWith(`/jobs/${jobId}`, updateData)
      expect(result).toEqual(mockResponse)
    })
  })

  describe('deleteJob', () => {
    it('should delete a job', async () => {
      const jobId = '123e4567-e89b-12d3-a456-426614174000'
      const mockResponse = { message: 'Job deleted successfully' }

      vi.mocked(apiClient.delete).mockResolvedValue({ data: mockResponse })

      const result = await jobsApi.deleteJob(jobId)

      expect(apiClient.delete).toHaveBeenCalledWith(`/jobs/${jobId}`)
      expect(result).toEqual(mockResponse)
    })
  })

  describe('featureJob', () => {
    it('should feature a job', async () => {
      const jobId = '123e4567-e89b-12d3-a456-426614174000'
      const mockResponse = { message: 'Job featured successfully' }

      vi.mocked(apiClient.post).mockResolvedValue({ data: mockResponse })

      const result = await jobsApi.featureJob(jobId)

      expect(apiClient.post).toHaveBeenCalledWith(`/jobs/${jobId}/feature`)
      expect(result).toEqual(mockResponse)
    })
  })
})
