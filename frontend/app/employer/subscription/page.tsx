'use client'

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { subscriptionsApi } from '@/lib/api/subscriptions'
import { ProtectedRoute } from '@/components/auth/ProtectedRoute'
import { SubscriptionTier } from '@/types'
import Link from 'next/link'

const tierDetails = {
  [SubscriptionTier.FREE]: {
    name: 'Free',
    price: '$0',
    period: 'forever',
    features: [
      '3 job posts per month',
      '0 featured listings',
      'Basic job posting',
      'URL import (limited)',
      'No application tracking',
      'No analytics',
    ],
    color: 'gray' as const,
    recommended: false,
  },
  [SubscriptionTier.BASIC]: {
    name: 'Basic',
    price: '$49',
    period: 'per month',
    features: [
      '20 job posts per month',
      '2 featured listings',
      'Priority job posting',
      'URL import',
      'Application tracking',
      'Email notifications',
    ],
    color: 'blue' as const,
    recommended: false,
  },
  [SubscriptionTier.PREMIUM]: {
    name: 'Premium',
    price: '$149',
    period: 'per month',
    features: [
      'Unlimited job posts',
      '10 featured listings',
      'Priority support',
      'Unlimited URL imports',
      'Advanced application tracking',
      'Analytics & insights',
      'Custom branding',
    ],
    color: 'purple' as const,
    recommended: true,
  },
}

export default function SubscriptionPage() {
  return (
    <ProtectedRoute requiredRole="employer">
      <SubscriptionContent />
    </ProtectedRoute>
  )
}

function SubscriptionContent() {
  const queryClient = useQueryClient()
  const [showCancelDialog, setShowCancelDialog] = useState(false)

  // Fetch current subscription
  const { data: subscription, isLoading } = useQuery({
    queryKey: ['subscription-info'],
    queryFn: () => subscriptionsApi.getSubscriptionInfo(),
  })

  // Update subscription mutation
  const updateMutation = useMutation({
    mutationFn: async (newTier: SubscriptionTier) => {
      // For paid tiers, redirect to Stripe checkout
      if (newTier !== SubscriptionTier.FREE) {
        const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/stripe/create-checkout-session?tier=${newTier}`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
          },
        })
        
        if (!response.ok) {
          const error = await response.json()
          throw new Error(error.detail || 'Failed to create checkout session')
        }
        
        const data = await response.json()
        
        // Redirect to Stripe checkout
        window.location.href = data.checkout_url
        
        return data
      } else {
        // For free tier, use the existing API
        return subscriptionsApi.updateSubscription({ new_tier: newTier })
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['subscription-info'] })
    },
  })

  // Cancel subscription mutation
  const cancelMutation = useMutation({
    mutationFn: async () => {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/stripe/cancel-subscription`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        },
      })
      
      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.detail || 'Failed to cancel subscription')
      }
      
      return response.json()
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['subscription-info'] })
      setShowCancelDialog(false)
      alert(data.message)
    },
    onError: (error: any) => {
      alert(error.message || 'Failed to cancel subscription')
    },
  })

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 py-8 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="h-8 bg-gray-200 rounded w-64 mb-8 animate-pulse"></div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {[1, 2, 3].map((i) => (
              <div key={i} className="bg-white shadow rounded-lg p-6 animate-pulse">
                <div className="h-6 bg-gray-200 rounded w-24 mb-4"></div>
                <div className="h-8 bg-gray-200 rounded w-32 mb-6"></div>
                <div className="space-y-3">
                  {[1, 2, 3, 4].map((j) => (
                    <div key={j} className="h-4 bg-gray-200 rounded"></div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    )
  }

  const currentTier = subscription?.tier as SubscriptionTier
  const isFreeTier = currentTier === SubscriptionTier.FREE

  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="text-center mb-12">
          <Link
            href="/employer/dashboard"
            className="inline-flex items-center text-sm text-gray-600 hover:text-gray-900 mb-4"
          >
            <svg
              className="w-4 h-4 mr-1"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M15 19l-7-7 7-7"
              />
            </svg>
            Back to Dashboard
          </Link>
          <h1 className="text-4xl font-bold text-gray-900 mb-4">Subscription Management</h1>
          <p className="text-xl text-gray-600">
            Manage your subscription and view usage statistics
          </p>
        </div>

        {/* Current Subscription Info with Enhanced Usage Stats */}
        {subscription && (
          <div className="bg-white shadow rounded-lg p-6 mb-8">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h3 className="text-2xl font-bold text-gray-900 mb-2">
                  Current Plan: {tierDetails[currentTier].name}
                </h3>
                <p className="text-gray-600">
                  Active until {new Date(subscription.end_date).toLocaleDateString()}
                </p>
              </div>
              {!isFreeTier && (
                <button
                  onClick={() => setShowCancelDialog(true)}
                  className="px-4 py-2 text-sm text-red-600 hover:text-red-800 hover:bg-red-50 rounded-lg transition-colors"
                >
                  Cancel Subscription
                </button>
              )}
            </div>

            {/* Usage Statistics */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Monthly Posts Usage */}
              <div className="bg-blue-50 rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <h4 className="text-sm font-semibold text-blue-900">Monthly Job Posts</h4>
                  <span className="text-sm text-blue-700">
                    {subscription.monthly_posts_used} / {subscription.monthly_posts_limit === -1 ? '∞' : subscription.monthly_posts_limit}
                  </span>
                </div>
                <div className="w-full bg-blue-200 rounded-full h-2">
                  <div
                    className="bg-blue-600 h-2 rounded-full transition-all"
                    style={{
                      width: subscription.monthly_posts_limit === -1
                        ? '0%'
                        : `${Math.min((subscription.monthly_posts_used / subscription.monthly_posts_limit) * 100, 100)}%`
                    }}
                  ></div>
                </div>
                <p className="text-xs text-blue-700 mt-2">
                  {subscription.monthly_posts_limit === -1
                    ? 'Unlimited posts available'
                    : `${subscription.monthly_posts_limit - subscription.monthly_posts_used} posts remaining this month`}
                </p>
              </div>

              {/* Featured Posts Usage */}
              <div className="bg-purple-50 rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <h4 className="text-sm font-semibold text-purple-900">Featured Listings</h4>
                  <span className="text-sm text-purple-700">
                    {subscription.featured_posts_used} / {subscription.featured_posts_limit}
                  </span>
                </div>
                <div className="w-full bg-purple-200 rounded-full h-2">
                  <div
                    className="bg-purple-600 h-2 rounded-full transition-all"
                    style={{
                      width: subscription.featured_posts_limit === 0
                        ? '0%'
                        : `${Math.min((subscription.featured_posts_used / subscription.featured_posts_limit) * 100, 100)}%`
                    }}
                  ></div>
                </div>
                <p className="text-xs text-purple-700 mt-2">
                  {subscription.featured_posts_limit === 0
                    ? 'Upgrade to access featured listings'
                    : `${subscription.featured_posts_limit - subscription.featured_posts_used} featured posts remaining`}
                </p>
              </div>
            </div>

            {/* Feature Access */}
            <div className="mt-6 pt-6 border-t border-gray-200">
              <h4 className="text-sm font-semibold text-gray-900 mb-3">Feature Access</h4>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="flex items-center">
                  <svg
                    className={`w-5 h-5 mr-2 ${subscription.has_application_tracking ? 'text-green-600' : 'text-gray-400'}`}
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d={subscription.has_application_tracking ? 'M5 13l4 4L19 7' : 'M6 18L18 6M6 6l12 12'}
                    />
                  </svg>
                  <span className="text-sm text-gray-700">Application Tracking</span>
                </div>
                <div className="flex items-center">
                  <svg
                    className={`w-5 h-5 mr-2 ${subscription.has_analytics ? 'text-green-600' : 'text-gray-400'}`}
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d={subscription.has_analytics ? 'M5 13l4 4L19 7' : 'M6 18L18 6M6 6l12 12'}
                    />
                  </svg>
                  <span className="text-sm text-gray-700">Analytics</span>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Pricing Cards */}
        <div className="mb-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-6 text-center">Available Plans</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {Object.entries(tierDetails).map(([tier, details]) => {
              const isCurrentTier = currentTier === tier
              const colorClasses = {
                gray: {
                  border: 'border-gray-300',
                  bg: 'bg-gray-50',
                  text: 'text-gray-900',
                  button: 'bg-gray-600 hover:bg-gray-700',
                },
                blue: {
                  border: 'border-blue-300',
                  bg: 'bg-blue-50',
                  text: 'text-blue-900',
                  button: 'bg-blue-600 hover:bg-blue-700',
                },
                purple: {
                  border: 'border-purple-300',
                  bg: 'bg-purple-50',
                  text: 'text-purple-900',
                  button: 'bg-purple-600 hover:bg-purple-700',
                },
              }[details.color] || {
                border: 'border-gray-300',
                bg: 'bg-gray-50',
                text: 'text-gray-900',
                button: 'bg-gray-600 hover:bg-gray-700',
              }

              return (
                <div
                  key={tier}
                  className={`relative bg-white rounded-lg shadow-lg overflow-hidden ${
                    details.recommended ? 'ring-2 ring-purple-600' : ''
                  }`}
                >
                  {details.recommended && (
                    <div className="absolute top-0 right-0 bg-purple-600 text-white px-4 py-1 text-sm font-medium rounded-bl-lg">
                      Recommended
                    </div>
                  )}
                  {isCurrentTier && (
                    <div className="absolute top-0 left-0 bg-green-600 text-white px-4 py-1 text-sm font-medium rounded-br-lg">
                      Current Plan
                    </div>
                  )}

                  <div className={`${colorClasses.bg} p-6 border-b ${colorClasses.border}`}>
                    <h3 className={`text-2xl font-bold ${colorClasses.text} mb-2`}>
                      {details.name}
                    </h3>
                    <div className="flex items-baseline">
                      <span className="text-4xl font-bold text-gray-900">{details.price}</span>
                      <span className="ml-2 text-gray-600">/ {details.period}</span>
                    </div>
                  </div>

                  <div className="p-6">
                    <ul className="space-y-4 mb-8">
                      {details.features.map((feature, index) => (
                        <li key={index} className="flex items-start">
                          <svg
                            className="w-5 h-5 text-green-600 mr-3 mt-0.5 flex-shrink-0"
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                          >
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M5 13l4 4L19 7"
                            />
                          </svg>
                          <span className="text-gray-700">{feature}</span>
                        </li>
                      ))}
                    </ul>

                    {isCurrentTier ? (
                      <button
                        disabled
                        className="w-full px-6 py-3 bg-gray-300 text-gray-600 font-medium rounded-lg cursor-not-allowed"
                      >
                        Current Plan
                      </button>
                    ) : (
                      <button
                        onClick={() => updateMutation.mutate(tier as SubscriptionTier)}
                        disabled={updateMutation.isPending}
                        className={`w-full px-6 py-3 text-white font-medium rounded-lg transition-colors ${colorClasses.button} disabled:bg-gray-400 disabled:cursor-not-allowed`}
                      >
                        {updateMutation.isPending ? 'Processing...' : `Upgrade to ${details.name}`}
                      </button>
                    )}
                  </div>
                </div>
              )
            })}
          </div>
        </div>

        {/* FAQ Section */}
        <div className="bg-white shadow rounded-lg p-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">Frequently Asked Questions</h2>
          <div className="space-y-6">
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                Can I change my plan at any time?
              </h3>
              <p className="text-gray-700">
                Yes, you can upgrade or downgrade your plan at any time. Changes take effect immediately,
                and we'll prorate any charges.
              </p>
            </div>
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                What happens when I reach my posting limit?
              </h3>
              <p className="text-gray-700">
                Once you reach your monthly posting limit, you'll need to wait until the next billing
                cycle or upgrade to a higher tier to post more jobs.
              </p>
            </div>
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                Do featured listings expire?
              </h3>
              <p className="text-gray-700">
                Featured listings remain active for the duration of the job posting. Your monthly
                featured listing quota resets at the start of each billing cycle.
              </p>
            </div>
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                Is there a contract or can I cancel anytime?
              </h3>
              <p className="text-gray-700">
                There are no long-term contracts. You can cancel your subscription at any time, and
                you'll retain access until the end of your current billing period.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Cancel Confirmation Dialog */}
      {showCancelDialog && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg max-w-md w-full p-6">
            <h3 className="text-xl font-bold text-gray-900 mb-4">Cancel Subscription</h3>
            <p className="text-gray-700 mb-6">
              Are you sure you want to cancel your subscription? You'll maintain access to your current
              plan until {subscription && new Date(subscription.end_date).toLocaleDateString()}, after
              which you'll be downgraded to the Free plan.
            </p>
            <div className="flex space-x-4">
              <button
                onClick={() => setShowCancelDialog(false)}
                className="flex-1 px-4 py-2 bg-gray-200 text-gray-800 rounded-lg hover:bg-gray-300 transition-colors"
              >
                Keep Subscription
              </button>
              <button
                onClick={() => cancelMutation.mutate()}
                disabled={cancelMutation.isPending}
                className="flex-1 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors disabled:bg-gray-400"
              >
                {cancelMutation.isPending ? 'Cancelling...' : 'Cancel Subscription'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
