import Link from 'next/link'
import { MainLayout } from '@/components/layout'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { ArrowRight, Briefcase, Globe, Zap, Search, ShieldCheck } from 'lucide-react'

export default function Home() {
  return (
    <MainLayout>
      <div className="flex flex-col min-h-screen bg-background">
        
        {/* Hero Section */}
        <section className="relative pt-24 pb-32 overflow-hidden flex flex-col items-center justify-center text-center px-4">
          <div className="absolute inset-0 bg-blue-50/50 dark:bg-blue-950/20 -z-10" />
          <div className="absolute top-0 right-1/4 w-96 h-96 bg-blue-400/20 rounded-full blur-3xl -z-10" />
          <div className="absolute bottom-10 left-1/4 w-72 h-72 bg-indigo-400/20 rounded-full blur-3xl -z-10" />
          
          <Badge variant="outline" className="mb-6 py-1 px-4 text-sm bg-blue-50 text-blue-700 border-blue-200 dark:bg-blue-900/30 dark:text-blue-300 dark:border-blue-800 rounded-full">
            ✨ The New TruSanity Experience
          </Badge>
          
          <h1 className="text-5xl md:text-7xl font-extrabold tracking-tight mb-8 max-w-4xl text-foreground">
            Find Your Next Opportunity with <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-indigo-600 dark:from-blue-400 dark:to-indigo-400">Precision</span>
          </h1>
          
          <p className="text-xl text-muted-foreground mb-10 max-w-2xl mx-auto leading-relaxed">
            Discover jobs, internships, freelance projects, and more from multiple sources in one unified, intelligent platform.
          </p>
          
          <div className="flex flex-col sm:flex-row gap-4 justify-center w-full max-w-md">
            <Button asChild size="lg" className="h-14 px-8 text-lg rounded-full shadow-lg shadow-blue-500/20 transition-all hover:scale-105">
              <Link href="/jobs">
                Browse Jobs
                <ArrowRight className="ml-2 h-5 w-5" />
              </Link>
            </Button>
            <Button asChild variant="outline" size="lg" className="h-14 px-8 text-lg rounded-full border-blue-200 hover:bg-blue-50 dark:border-blue-800 dark:hover:bg-blue-900/50 transition-all">
              <Link href="/register">
                Join TruSanity
              </Link>
            </Button>
          </div>
          
          {/* Trust Indicators */}
          <div className="mt-20 pt-10 border-t border-border/50 flex flex-wrap justify-center gap-8 md:gap-16 opacity-70 grayscale">
            <div className="flex items-center gap-2 text-lg font-bold"><Briefcase /> LinkedIn</div>
            <div className="flex items-center gap-2 text-lg font-bold"><Globe /> Indeed</div>
            <div className="flex items-center gap-2 text-lg font-bold"><Search /> Naukri</div>
            <div className="flex items-center gap-2 text-lg font-bold"><Zap /> Glassdoor</div>
          </div>
        </section>

        {/* Features Section */}
        <section className="py-24 bg-card px-4">
          <div className="container mx-auto">
            <div className="text-center mb-16">
              <h2 className="text-3xl md:text-4xl font-bold mb-4">Why Choose TruSanity?</h2>
              <p className="text-muted-foreground max-w-2xl mx-auto text-lg">
                We've rebuilt the job search experience from the ground up to be faster, smarter, and incredibly intuitive.
              </p>
            </div>
            
            <div className="grid md:grid-cols-3 gap-8 max-w-6xl mx-auto">
              {/* Feature 1 */}
              <Card className="border-none shadow-lg bg-background hover:shadow-xl transition-all hover:-translate-y-1 duration-300">
                <CardHeader>
                  <div className="h-12 w-12 rounded-lg bg-blue-100 dark:bg-blue-900 flex items-center justify-center mb-4">
                    <Globe className="h-6 w-6 text-blue-600 dark:text-blue-400" />
                  </div>
                  <CardTitle className="text-xl">Aggregated Listings</CardTitle>
                </CardHeader>
                <CardContent>
                  <CardDescription className="text-base text-muted-foreground">
                    Stop checking a dozen different websites. We pull jobs from LinkedIn, Indeed, Naukri, Monster, and more into one unified dashboard.
                  </CardDescription>
                </CardContent>
              </Card>

              {/* Feature 2 */}
              <Card className="border-none shadow-lg bg-background hover:shadow-xl transition-all hover:-translate-y-1 duration-300">
                <CardHeader>
                  <div className="h-12 w-12 rounded-lg bg-indigo-100 dark:bg-indigo-900 flex items-center justify-center mb-4">
                    <Zap className="h-6 w-6 text-indigo-600 dark:text-indigo-400" />
                  </div>
                  <CardTitle className="text-xl">Real-time Pulse</CardTitle>
                </CardHeader>
                <CardContent>
                  <CardDescription className="text-base text-muted-foreground">
                    Get the latest job postings as soon as they're available. Our lightning-fast sync ensures you're always the first to apply.
                  </CardDescription>
                </CardContent>
              </Card>

              {/* Feature 3 */}
              <Card className="border-none shadow-lg bg-background hover:shadow-xl transition-all hover:-translate-y-1 duration-300">
                <CardHeader>
                  <div className="h-12 w-12 rounded-lg bg-purple-100 dark:bg-purple-900 flex items-center justify-center mb-4">
                    <ShieldCheck className="h-6 w-6 text-purple-600 dark:text-purple-400" />
                  </div>
                  <CardTitle className="text-xl">Smart Filtering</CardTitle>
                </CardHeader>
                <CardContent>
                  <CardDescription className="text-base text-muted-foreground">
                    Advanced search and dynamic filters help you cut through the noise to find exactly the role you're looking for, instantly.
                  </CardDescription>
                </CardContent>
              </Card>
            </div>
          </div>
        </section>

        {/* CTA Section */}
        <section className="py-24 relative overflow-hidden">
          <div className="absolute inset-0 bg-gradient-to-br from-blue-600 to-indigo-700 -z-10" />
          <div className="absolute top-0 left-0 w-full h-full bg-[url('/noise.png')] opacity-10 mix-blend-overlay -z-10" />
          
          <div className="container mx-auto px-4 text-center text-white">
            <h2 className="text-4xl md:text-5xl font-bold mb-6">Ready to hire?</h2>
            <p className="text-xl text-blue-100 mb-10 max-w-2xl mx-auto">
              Post your jobs and reach thousands of highly qualified candidates through the TruSanity network.
            </p>
            <Button asChild size="lg" className="bg-white text-blue-700 hover:bg-gray-100 h-14 px-10 text-lg rounded-full shadow-2xl transition-all hover:scale-105">
              <Link href="/employer/register">
                Post a Job Today
              </Link>
            </Button>
          </div>
        </section>
        
      </div>
    </MainLayout>
  )
}
