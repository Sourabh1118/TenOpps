import Link from 'next/link'
import { MainLayout } from '@/components/layout'

export default function Home() {
  return (
    <MainLayout>
      {/* Hero Section */}
      <section className="bg-gradient-to-r from-blue-600 to-blue-800 text-white py-20">
        <div className="container mx-auto px-4 text-center">
          <h1 className="text-5xl font-bold mb-6">
            Find Your Next Opportunity
          </h1>
          <p className="text-xl mb-8 max-w-2xl mx-auto">
            Discover jobs, internships, freelance projects, and more from multiple sources in one place
          </p>
          <div className="flex gap-4 justify-center">
            <Link
              href="/jobs"
              className="px-8 py-3 bg-white text-blue-600 rounded-lg font-semibold hover:bg-gray-100"
            >
              Browse Jobs
            </Link>
            <Link
              href="/register"
              className="px-8 py-3 bg-blue-700 text-white rounded-lg font-semibold hover:bg-blue-800 border border-white"
            >
              Get Started
            </Link>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-16">
        <div className="container mx-auto px-4">
          <h2 className="text-3xl font-bold text-center mb-12">Why Choose JobHub?</h2>
          <div className="grid md:grid-cols-3 gap-8">
            <div className="text-center">
              <div className="text-4xl mb-4">🔍</div>
              <h3 className="text-xl font-semibold mb-2">Aggregated Listings</h3>
              <p className="text-gray-600">
                Jobs from LinkedIn, Indeed, Naukri, Monster, and more in one place
              </p>
            </div>
            <div className="text-center">
              <div className="text-4xl mb-4">⚡</div>
              <h3 className="text-xl font-semibold mb-2">Real-time Updates</h3>
              <p className="text-gray-600">
                Get the latest job postings as soon as they&apos;re available
              </p>
            </div>
            <div className="text-center">
              <div className="text-4xl mb-4">🎯</div>
              <h3 className="text-xl font-semibold mb-2">Smart Filtering</h3>
              <p className="text-gray-600">
                Advanced search and filters to find exactly what you&apos;re looking for
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="bg-gray-50 py-16">
        <div className="container mx-auto px-4 text-center">
          <h2 className="text-3xl font-bold mb-4">Ready to hire?</h2>
          <p className="text-xl text-gray-600 mb-8">
            Post your jobs and reach thousands of qualified candidates
          </p>
          <Link
            href="/employer/register"
            className="px-8 py-3 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700 inline-block"
          >
            Post a Job
          </Link>
        </div>
      </section>
    </MainLayout>
  )
}
