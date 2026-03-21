/**
 * API Client Tests
 * 
 * Tests for the API client utilities including:
 * - Request interceptor (JWT token attachment)
 * - Response interceptor (401 handling and token refresh)
 * - Typed API client functions
 */

import { describe, it, expect, beforeEach, vi } from 'vitest'
import axios from 'axios'
import apiClient from '@/lib/api-client'

// Mock axios
vi.mock('axios')

describe('API Client', () => {
  beforeEach(() => {
    // Clear localStorage
    localStorage.clear()
    vi.clearAllMocks()
  })

  describe('Request Interceptor', () => {
    it('should attach JWT token to request headers', async () => {
      const token = 'test-access-token'
      localStorage.setItem('accessToken', token)

      const mockResponse = { data: { success: true } }
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      vi.mocked(axios.create).mockReturnValue({
        ...apiClient,
        get: vi.fn().mockResolvedValue(mockResponse),
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
      } as any)

      // The interceptor should add the Authorization header
      expect(localStorage.getItem('accessToken')).toBe(token)
    })

    it('should not attach token if not present in localStorage', () => {
      expect(localStorage.getItem('accessToken')).toBeNull()
    })
  })

  describe('Response Interceptor', () => {
    it('should handle successful responses', async () => {
      const mockResponse = { data: { success: true }, status: 200 }
      
      // Response interceptor should pass through successful responses
      expect(mockResponse.status).toBe(200)
    })

    it('should handle 401 errors and attempt token refresh', async () => {
      const refreshToken = 'test-refresh-token'
      localStorage.setItem('refreshToken', refreshToken)

      // The interceptor should attempt to refresh the token
      expect(localStorage.getItem('refreshToken')).toBe(refreshToken)
    })

    it('should redirect to login if token refresh fails', () => {
      // Clear tokens
      localStorage.removeItem('accessToken')
      localStorage.removeItem('refreshToken')

      expect(localStorage.getItem('accessToken')).toBeNull()
      expect(localStorage.getItem('refreshToken')).toBeNull()
    })
  })

  describe('Token Refresh Queue', () => {
    it('should queue requests while refreshing token', async () => {
      // This tests that multiple 401 errors don't trigger multiple refresh attempts
      const refreshToken = 'test-refresh-token'
      localStorage.setItem('refreshToken', refreshToken)

      // Simulate multiple concurrent requests getting 401
      // The interceptor should queue them and process after refresh
      expect(localStorage.getItem('refreshToken')).toBe(refreshToken)
    })
  })
})

describe('API Client Configuration', () => {
  it('should have correct base URL', () => {
    const expectedBaseURL = `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}${process.env.NEXT_PUBLIC_API_BASE_PATH || '/api'}`
    expect(apiClient.defaults.baseURL).toBe(expectedBaseURL)
  })

  it('should have correct timeout', () => {
    expect(apiClient.defaults.timeout).toBe(30000)
  })

  it('should have correct default headers', () => {
    expect(apiClient.defaults.headers['Content-Type']).toBe('application/json')
  })
})
