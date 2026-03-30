'use client'

export function JobCardSkeleton() {
  return (
    <div className="bg-white border border-slate-100 rounded-[2rem] p-6 relative overflow-hidden">
      <div className="animate-pulse space-y-6">
        {/* Header Shimmer */}
        <div className="flex items-start justify-between">
          <div className="flex-1 space-y-3">
            <div className="h-6 bg-slate-100 rounded-full w-3/4"></div>
            <div className="h-4 bg-slate-50 rounded-full w-1/2"></div>
          </div>
          <div className="w-20 h-6 bg-slate-50 rounded-lg"></div>
        </div>

        {/* Info Grid Shimmer */}
        <div className="grid grid-cols-2 gap-4">
          <div className="h-4 bg-slate-50 rounded-full"></div>
          <div className="h-4 bg-slate-50 rounded-full"></div>
        </div>

        {/* Badges Shimmer */}
        <div className="flex gap-2">
          <div className="w-24 h-8 bg-slate-50 rounded-xl"></div>
          <div className="w-24 h-8 bg-slate-50 rounded-xl"></div>
        </div>

        {/* Description Shimmer */}
        <div className="space-y-2">
          <div className="h-3 bg-slate-50 rounded-full w-full"></div>
          <div className="h-3 bg-slate-50 rounded-full w-5/6"></div>
        </div>

        {/* Footer Shimmer */}
        <div className="pt-5 border-t border-slate-50 flex justify-between">
          <div className="w-32 h-3 bg-slate-50 rounded-full"></div>
          <div className="w-20 h-3 bg-slate-50 rounded-full"></div>
        </div>
      </div>
      
      {/* Shimmer gradient overlay */}
      <div className="absolute inset-0 -translate-x-full animate-[shimmer_2s_infinite] bg-gradient-to-r from-transparent via-white/40 to-transparent"></div>
    </div>
  )
}

export function JobListingSkeleton() {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pb-12">
      {[...Array(6)].map((_, i) => (
        <JobCardSkeleton key={i} />
      ))}
    </div>
  )
}
