import { Metadata } from 'next'
import Link from 'next/link'

export const metadata: Metadata = {
  title: 'Pricing | Job Aggregation Platform',
  description: 'Choose the right plan for your hiring needs',
}

export default function PricingPage() {
  const plans = [
    {
      name: 'Free',
      price: '₹0',
      period: 'forever',
      description: 'Perfect for trying out the platform',
      features: [
        '1 job posting per month',
        'Basic job listing',
        '30-day job duration',
        'Email support',
      ],
      cta: 'Get Started',
      href: '/register/employer',
      highlighted: false,
    },
    {
      name: 'Basic',
      price: '₹999',
      period: 'per month',
      description: 'Great for small businesses',
      features: [
        '5 job postings per month',
        'Standard job listings',
        '60-day job duration',
        'Priority email support',
        'Basic analytics',
      ],
      cta: 'Subscribe',
      href: '/employer/subscription',
      highlighted: false,
    },
    {
      name: 'Premium',
      price: '₹2,999',
      period: 'per month',
      description: 'Best for growing companies',
      features: [
        'Unlimited job postings',
        'Featured listings (10 slots)',
        '90-day job duration',
        'Priority support',
        'Advanced analytics',
        'URL import feature',
        'Application tracking',
      ],
      cta: 'Subscribe',
      href: '/employer/subscription',
      highlighted: true,
    },
  ]

  return (
    <div className="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto">
        <div className="text-center">
          <h1 className="text-4xl font-extrabold text-gray-900 sm:text-5xl">
            Simple, transparent pricing
          </h1>
          <p className="mt-4 text-xl text-gray-600">
            Choose the plan that fits your hiring needs
          </p>
        </div>

        <div className="mt-16 grid gap-8 lg:grid-cols-3 lg:gap-x-8">
          {plans.map((plan) => (
            <div
              key={plan.name}
              className={`relative flex flex-col rounded-2xl border ${
                plan.highlighted
                  ? 'border-blue-500 shadow-xl'
                  : 'border-gray-200 shadow-sm'
              } bg-white p-8`}
            >
              {plan.highlighted && (
                <div className="absolute -top-4 left-1/2 -translate-x-1/2">
                  <span className="inline-flex rounded-full bg-blue-500 px-4 py-1 text-sm font-semibold text-white">
                    Most Popular
                  </span>
                </div>
              )}

              <div className="flex-1">
                <h3 className="text-2xl font-bold text-gray-900">{plan.name}</h3>
                <p className="mt-4 flex items-baseline text-gray-900">
                  <span className="text-5xl font-extrabold tracking-tight">
                    {plan.price}
                  </span>
                  <span className="ml-2 text-xl text-gray-500">/{plan.period}</span>
                </p>
                <p className="mt-6 text-gray-600">{plan.description}</p>

                <ul className="mt-8 space-y-4">
                  {plan.features.map((feature) => (
                    <li key={feature} className="flex items-start">
                      <svg
                        className="h-6 w-6 flex-shrink-0 text-green-500"
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
                      <span className="ml-3 text-gray-700">{feature}</span>
                    </li>
                  ))}
                </ul>
              </div>

              <Link
                href={plan.href}
                className={`mt-8 block w-full rounded-lg px-6 py-3 text-center text-sm font-semibold ${
                  plan.highlighted
                    ? 'bg-blue-600 text-white hover:bg-blue-700'
                    : 'bg-gray-100 text-gray-900 hover:bg-gray-200'
                } transition-colors`}
              >
                {plan.cta}
              </Link>
            </div>
          ))}
        </div>

        <div className="mt-16 text-center">
          <p className="text-gray-600">
            Need a custom plan?{' '}
            <a href="mailto:support@trusanity.com" className="text-blue-600 hover:text-blue-500">
              Contact us
            </a>
          </p>
        </div>
      </div>
    </div>
  )
}
