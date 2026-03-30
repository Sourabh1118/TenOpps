'use client'

import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { ExternalLink, Building2 } from 'lucide-react'
import { Job } from '@/types'
import { useRouter } from 'next/navigation'

interface StickyApplyBarProps {
  job: Job
}

export function StickyApplyBar({ job }: StickyApplyBarProps) {
  const [isVisible, setIsVisible] = useState(false)
  const router = useRouter()

  useEffect(() => {
    const handleScroll = () => {
      // Show bar when user scrolls past 400px
      if (window.scrollY > 400) {
        setIsVisible(true)
      } else {
        setIsVisible(false)
      }
    }

    window.addEventListener('scroll', handleScroll)
    return () => window.removeEventListener('scroll', handleScroll)
  }, [])

  const isDirectPost = job.sourceType === 'direct'

  return (
    <AnimatePresence>
      {isVisible && (
        <motion.div
          initial={{ y: -100, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          exit={{ y: -100, opacity: 0 }}
          transition={{ duration: 0.4, ease: [0.22, 1, 0.36, 1] }}
          className="fixed top-0 left-0 right-0 z-50 bg-white/80 backdrop-blur-xl border-b border-slate-100 shadow-lg shadow-blue-500/5 px-4 h-20 flex items-center"
        >
          <div className="max-w-5xl mx-auto w-full flex items-center justify-between gap-4">
            <div className="flex items-center min-w-0">
              <div className="hidden sm:flex w-10 h-10 bg-slate-50 border border-slate-100 rounded-lg items-center justify-center mr-3 flex-shrink-0">
                <Building2 className="w-5 h-5 text-slate-400" />
              </div>
              <div className="min-w-0">
                <h2 className="text-sm font-black text-slate-900 truncate leading-tight">{job.title}</h2>
                <p className="text-xs font-bold text-slate-500 truncate">{job.company}</p>
              </div>
            </div>

            <div className="flex-shrink-0">
              {isDirectPost ? (
                <button
                  onClick={() => router.push(`/jobs/${job.id}/apply`)}
                  className="py-2.5 px-6 bg-blue-600 text-white text-sm font-black rounded-xl hover:bg-blue-700 hover:shadow-lg hover:shadow-blue-600/20 transition-all active:scale-95"
                >
                  Apply Now
                </button>
              ) : (
                <a
                  href={job.sourceUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="py-2.5 px-6 bg-blue-600 text-white text-sm font-black rounded-xl hover:bg-blue-700 hover:shadow-lg hover:shadow-blue-600/20 transition-all active:scale-95 flex items-center whitespace-nowrap"
                >
                  Apply External
                  <ExternalLink className="w-3.5 h-3.5 ml-2" />
                </a>
              )}
            </div>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}
