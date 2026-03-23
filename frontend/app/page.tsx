import Link from 'next/link'
import { MainLayout } from '@/components/layout'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { ArrowRight, Briefcase, Globe, Zap, Search, ShieldCheck, Sparkles, TrendingUp, Users, CheckCircle2, Star } from 'lucide-react'

export default function Home() {
  return (
    <MainLayout>
      <div className="flex flex-col min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50 dark:from-slate-950 dark:via-blue-950 dark:to-indigo-950">
        
        {/* Hero Section */}
        <section className="relative pt-32 pb-40 overflow-hidden">
          {/* Animated Background Elements */}
          <div className="absolute inset-0 overflow-hidden">
            <div className="absolute top-1/4 -left-48 w-96 h-96 bg-blue-500/30 dark:bg-blue-500/20 rounded-full blur-3xl animate-pulse" />
            <div className="absolute top-1/3 -right-48 w-96 h-96 bg-indigo-500/30 dark:bg-indigo-500/20 rounded-full blur-3xl animate-pulse delay-1000" />
            <div className="absolute bottom-1/4 left-1/3 w-72 h-72 bg-purple-500/20 dark:bg-purple-500/10 rounded-full blur-3xl animate-pulse delay-2000" />
          </div>

          <div className="container mx-auto px-4 relative z-10">
            <div className="max-w-5xl mx-auto text-center">
              {/* Badge */}
              <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-white/80 dark:bg-slate-800/80 backdrop-blur-sm border border-blue-200 dark:border-blue-800 shadow-lg mb-8 animate-fade-in">
                <Sparkles className="w-4 h-4 text-blue-600 dark:text-blue-400" />
                <span className="text-sm font-medium text-slate-700 dark:text-slate-300">
                  Trusted by 10,000+ Job Seekers
                </span>
              </div>

              {/* Main Heading */}
              <h1 className="text-6xl md:text-7xl lg:text-8xl font-black tracking-tight mb-8 animate-fade-in-up">
                <span className="bg-clip-text text-transparent bg-gradient-to-r from-slate-900 via-blue-800 to-indigo-900 dark:from-white dark:via-blue-200 dark:to-indigo-200">
                  Find Your Dream Job
                </span>
                <br />
                <span className="bg-clip-text text-transparent bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 dark:from-blue-400 dark:via-indigo-400 dark:to-purple-400">
                  In One Place
                </span>
              </h1>

              {/* Subheading */}
              <p className="text-xl md:text-2xl text-slate-600 dark:text-slate-300 mb-12 max-w-3xl mx-auto leading-relaxed animate-fade-in-up delay-200">
                Aggregate jobs from LinkedIn, Indeed, Naukri, and more. 
                <span className="font-semibold text-blue-600 dark:text-blue-400"> Smart filters</span>, 
                <span className="font-semibold text-indigo-600 dark:text-indigo-400"> real-time updates</span>, 
                and <span className="font-semibold text-purple-600 dark:text-purple-400">zero hassle</span>.
              </p>

              {/* CTA Buttons */}
              <div className="flex flex-col sm:flex-row gap-4 justify-center mb-16 animate-fade-in-up delay-300">
                <Button asChild size="lg" className="h-14 px-10 text-lg rounded-full bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 shadow-2xl shadow-blue-500/50 dark:shadow-blue-500/30 transition-all hover:scale-105 hover:shadow-3xl">
                  <Link href="/jobs" className="flex items-center gap-2">
                    <Search className="w-5 h-5" />
                    Explore Jobs
                    <ArrowRight className="w-5 h-5" />
                  </Link>
                </Button>
                <Button asChild variant="outline" size="lg" className="h-14 px-10 text-lg rounded-full border-2 border-slate-300 dark:border-slate-600 bg-white/50 dark:bg-slate-800/50 backdrop-blur-sm hover:bg-white dark:hover:bg-slate-800 transition-all hover:scale-105">
                  <Link href="/register">
                    Get Started Free
                  </Link>
                </Button>
              </div>

              {/* Stats */}
              <div className="grid grid-cols-3 gap-8 max-w-2xl mx-auto animate-fade-in-up delay-400">
                <div className="text-center">
                  <div className="text-3xl md:text-4xl font-bold text-blue-600 dark:text-blue-400 mb-1">50K+</div>
                  <div className="text-sm text-slate-600 dark:text-slate-400">Active Jobs</div>
                </div>
                <div className="text-center">
                  <div className="text-3xl md:text-4xl font-bold text-indigo-600 dark:text-indigo-400 mb-1">500+</div>
                  <div className="text-sm text-slate-600 dark:text-slate-400">Companies</div>
                </div>
                <div className="text-center">
                  <div className="text-3xl md:text-4xl font-bold text-purple-600 dark:text-purple-400 mb-1">98%</div>
                  <div className="text-sm text-slate-600 dark:text-slate-400">Success Rate</div>
                </div>
              </div>
            </div>
          </div>

          {/* Scroll Indicator */}
          <div className="absolute bottom-8 left-1/2 -translate-x-1/2 animate-bounce">
            <div className="w-6 h-10 rounded-full border-2 border-slate-400 dark:border-slate-600 flex items-start justify-center p-2">
              <div className="w-1 h-3 bg-slate-400 dark:bg-slate-600 rounded-full" />
            </div>
          </div>
        </section>

        {/* Features Section */}
        <section className="py-32 relative">
          <div className="container mx-auto px-4">
            <div className="text-center mb-20">
              <Badge className="mb-4 bg-gradient-to-r from-blue-600 to-indigo-600 text-white border-0">
                Why Choose Us
              </Badge>
              <h2 className="text-4xl md:text-5xl font-bold mb-6 bg-clip-text text-transparent bg-gradient-to-r from-slate-900 to-slate-700 dark:from-white dark:to-slate-300">
                Everything You Need to Land Your Dream Job
              </h2>
              <p className="text-xl text-slate-600 dark:text-slate-400 max-w-3xl mx-auto">
                Powerful features designed to make your job search faster, smarter, and more successful
              </p>
            </div>
            
            <div className="grid md:grid-cols-3 gap-8 max-w-7xl mx-auto">
              {/* Feature 1 */}
              <Card className="group relative overflow-hidden border-0 bg-white/80 dark:bg-slate-800/80 backdrop-blur-sm shadow-xl hover:shadow-2xl transition-all duration-300 hover:-translate-y-2">
                <div className="absolute inset-0 bg-gradient-to-br from-blue-500/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
                <CardHeader className="relative">
                  <div className="h-14 w-14 rounded-2xl bg-gradient-to-br from-blue-500 to-blue-600 dark:from-blue-400 dark:to-blue-500 flex items-center justify-center mb-6 shadow-lg group-hover:scale-110 transition-transform">
                    <Globe className="h-7 w-7 text-white" />
                  </div>
                  <CardTitle className="text-2xl mb-3">Multi-Source Aggregation</CardTitle>
                </CardHeader>
                <CardContent className="relative">
                  <CardDescription className="text-base text-slate-600 dark:text-slate-400 leading-relaxed">
                    Access jobs from LinkedIn, Indeed, Naukri, Monster, and 20+ platforms in one unified dashboard. No more tab switching.
                  </CardDescription>
                  <div className="mt-6 flex items-center gap-2 text-sm font-medium text-blue-600 dark:text-blue-400">
                    <CheckCircle2 className="w-4 h-4" />
                    20+ Job Boards
                  </div>
                </CardContent>
              </Card>

              {/* Feature 2 */}
              <Card className="group relative overflow-hidden border-0 bg-white/80 dark:bg-slate-800/80 backdrop-blur-sm shadow-xl hover:shadow-2xl transition-all duration-300 hover:-translate-y-2">
                <div className="absolute inset-0 bg-gradient-to-br from-indigo-500/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
                <CardHeader className="relative">
                  <div className="h-14 w-14 rounded-2xl bg-gradient-to-br from-indigo-500 to-indigo-600 dark:from-indigo-400 dark:to-indigo-500 flex items-center justify-center mb-6 shadow-lg group-hover:scale-110 transition-transform">
                    <Zap className="h-7 w-7 text-white" />
                  </div>
                  <CardTitle className="text-2xl mb-3">Real-Time Updates</CardTitle>
                </CardHeader>
                <CardContent className="relative">
                  <CardDescription className="text-base text-slate-600 dark:text-slate-400 leading-relaxed">
                    Get instant notifications for new job postings. Our AI-powered system syncs every 5 minutes to keep you ahead.
                  </CardDescription>
                  <div className="mt-6 flex items-center gap-2 text-sm font-medium text-indigo-600 dark:text-indigo-400">
                    <TrendingUp className="w-4 h-4" />
                    5-Min Sync
                  </div>
                </CardContent>
              </Card>

              {/* Feature 3 */}
              <Card className="group relative overflow-hidden border-0 bg-white/80 dark:bg-slate-800/80 backdrop-blur-sm shadow-xl hover:shadow-2xl transition-all duration-300 hover:-translate-y-2">
                <div className="absolute inset-0 bg-gradient-to-br from-purple-500/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
                <CardHeader className="relative">
                  <div className="h-14 w-14 rounded-2xl bg-gradient-to-br from-purple-500 to-purple-600 dark:from-purple-400 dark:to-purple-500 flex items-center justify-center mb-6 shadow-lg group-hover:scale-110 transition-transform">
                    <ShieldCheck className="h-7 w-7 text-white" />
                  </div>
                  <CardTitle className="text-2xl mb-3">Smart AI Filtering</CardTitle>
                </CardHeader>
                <CardContent className="relative">
                  <CardDescription className="text-base text-slate-600 dark:text-slate-400 leading-relaxed">
                    Advanced filters and AI-powered recommendations help you find the perfect match based on your skills and preferences.
                  </CardDescription>
                  <div className="mt-6 flex items-center gap-2 text-sm font-medium text-purple-600 dark:text-purple-400">
                    <Star className="w-4 h-4" />
                    AI-Powered
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>
        </section>

        {/* CTA Section */}
        <section className="py-32 relative overflow-hidden">
          <div className="absolute inset-0 bg-gradient-to-br from-blue-600 via-indigo-600 to-purple-700 dark:from-blue-700 dark:via-indigo-700 dark:to-purple-800" />
          <div className="absolute inset-0 bg-[url('/grid.svg')] opacity-10" />
          <div className="absolute top-0 left-0 w-full h-full">
            <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-white/10 rounded-full blur-3xl animate-pulse" />
            <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-white/10 rounded-full blur-3xl animate-pulse delay-1000" />
          </div>
          
          <div className="container mx-auto px-4 relative z-10">
            <div className="max-w-4xl mx-auto text-center text-white">
              <Badge className="mb-6 bg-white/20 text-white border-white/30 backdrop-blur-sm">
                For Employers
              </Badge>
              <h2 className="text-5xl md:text-6xl font-bold mb-8 leading-tight">
                Ready to Find Your
                <br />
                <span className="bg-clip-text text-transparent bg-gradient-to-r from-yellow-200 to-orange-200">
                  Perfect Candidate?
                </span>
              </h2>
              <p className="text-xl md:text-2xl text-blue-100 mb-12 max-w-2xl mx-auto leading-relaxed">
                Post your jobs and connect with thousands of qualified candidates actively looking for opportunities
              </p>
              
              <div className="flex flex-col sm:flex-row gap-4 justify-center mb-12">
                <Button asChild size="lg" className="h-16 px-12 text-lg rounded-full bg-white text-blue-700 hover:bg-blue-50 shadow-2xl transition-all hover:scale-105">
                  <Link href="/employer/register" className="flex items-center gap-2">
                    <Users className="w-5 h-5" />
                    Post a Job
                    <ArrowRight className="w-5 h-5" />
                  </Link>
                </Button>
                <Button asChild variant="outline" size="lg" className="h-16 px-12 text-lg rounded-full border-2 border-white/30 bg-white/10 backdrop-blur-sm text-white hover:bg-white/20 transition-all hover:scale-105">
                  <Link href="/employer/pricing">
                    View Pricing
                  </Link>
                </Button>
              </div>

              {/* Trust Badges */}
              <div className="flex flex-wrap justify-center gap-8 items-center opacity-80">
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="w-5 h-5" />
                  <span>No Credit Card Required</span>
                </div>
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="w-5 h-5" />
                  <span>Free Trial Available</span>
                </div>
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="w-5 h-5" />
                  <span>Cancel Anytime</span>
                </div>
              </div>
            </div>
          </div>
        </section>
        
      </div>
    </MainLayout>
  )
}
