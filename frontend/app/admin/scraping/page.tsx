'use client'

import { useEffect, useState, useCallback, Fragment } from 'react'
import { getScrapingStatus, triggerScrape, resetCircuitBreaker, type ScrapingStatus, type ScraperConfig } from '@/lib/api/admin'

const SCRAPER_PROVIDERS = [
  { id: 'scrape_do', name: 'Scrape.do (Default)', type: 'Proxy' },
  { id: 'scraper_api', name: 'ScraperAPI', type: 'Proxy' },
  { id: 'scraping_bee', name: 'ScrapingBee', type: 'Proxy' },
  { id: 'bright_data', name: 'Bright Data', type: 'Proxy' },
  { id: 'diffbot', name: 'Diffbot', type: 'AI' },
  { id: 'parsehub', name: 'ParseHub', type: 'Cloud' },
  { id: 'browse_ai', name: 'Browse AI', type: 'Cloud' },
  { id: 'decodo', name: 'Decodo', type: 'Proxy' },
  { id: 'databar', name: 'Databar', type: 'API' },
]

const SOURCE_ICONS: Record<string, string> = { linkedin: '🔵', indeed: '🟣', naukri: '🟠', monster: '🔴' }

export default function AdminScrapingPage() {
  const [data, setData] = useState<ScrapingStatus | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [triggering, setTriggering] = useState<string | null>(null)
  const [resetting, setResetting] = useState<string | null>(null)
  const [triggerMsg, setTriggerMsg] = useState<string | null>(null)
  const [showConfig, setShowConfig] = useState<string | null>(null)
  const [config, setConfig] = useState<ScraperConfig>({ provider: 'scrape_do' })

  const load = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      const res = await getScrapingStatus()
      setData(res)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load scraping status')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { load() }, [load])

  const handleTrigger = async () => {
    if (!showConfig) return
    const source = showConfig
    setTriggering(source)
    setTriggerMsg(null)
    setShowConfig(null)
    try {
      const res = await triggerScrape(source, config)
      setTriggerMsg(`✅ ${res.message} via ${res.provider || 'default'} (task: ${res.task_id})`)
    } catch (err: any) {
      setTriggerMsg(`❌ ${err.response?.data?.detail || 'Failed to trigger scrape'}`)
    } finally {
      setTriggering(null)
    }
  }

  const handleReset = async (source: string) => {
    setResetting(source)
    setTriggerMsg(null)
    try {
      const res = await resetCircuitBreaker(source)
      setTriggerMsg(`✅ ${res.message}`)
      await load()
    } catch (err: any) {
      setTriggerMsg(`❌ ${err.response?.data?.detail || 'Failed to reset circuit breaker'}`)
    } finally {
      setResetting(null)
    }
  }

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Scraping Monitor</h1>
          <p className="text-gray-500 mt-1">Real-time status of all job scraping sources</p>
        </div>
        <button onClick={load} className="px-4 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700">Refresh</button>
      </div>

      {triggerMsg && (
        <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded-lg text-sm text-blue-800">{triggerMsg}</div>
      )}

      {error && (
        <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">{error}</div>
      )}

      {loading ? (
        <div className="flex justify-center py-16 text-gray-400">Loading...</div>
      ) : (
        <>
          {/* Source Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-6 mb-8">
            {data?.sources.map(src => (
              <div key={src.source} className={`bg-white rounded-xl border-2 shadow-sm p-5 ${src.circuit_open ? 'border-red-300' : 'border-green-200'}`}>
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <span className="text-2xl">{SOURCE_ICONS[src.source] ?? '⚙️'}</span>
                    <h3 className="font-semibold text-gray-900 capitalize">{src.source}</h3>
                  </div>
                  <span className={`px-2 py-1 rounded-full text-xs font-bold ${src.circuit_open ? 'bg-red-100 text-red-700' : 'bg-green-100 text-green-700'}`}>
                    {src.circuit_open ? '⚡ OPEN' : '✅ OK'}
                  </span>
                </div>

                <div className="space-y-1 text-sm text-gray-600 mb-4">
                  <div className="flex justify-between">
                    <span>Failures</span>
                    <span className={`font-semibold ${src.failure_count > 0 ? 'text-red-600' : 'text-gray-900'}`}>{src.failure_count} / 3</span>
                  </div>
                  {src.circuit_open && src.cooldown_seconds != null && (
                    <div className="flex justify-between">
                      <span>Cooldown</span>
                      <span className="font-semibold text-orange-600">{Math.ceil(src.cooldown_seconds / 60)} min</span>
                    </div>
                  )}
                </div>

                <div className="flex gap-2">
                  <button
                    onClick={() => {
                      setShowConfig(src.source)
                      setConfig({ provider: 'scrape_do' })
                    }}
                    disabled={triggering === src.source}
                    className="flex-1 py-2 text-sm bg-gray-900 text-white rounded-lg hover:bg-gray-700 disabled:opacity-50 font-medium"
                  >
                    {triggering === src.source ? 'Queuing...' : '▶ Trigger Scrape'}
                  </button>
                  {src.circuit_open && (
                    <button
                      onClick={() => handleReset(src.source)}
                      disabled={resetting === src.source}
                      className="px-3 py-2 text-sm bg-white border border-red-300 text-red-600 rounded-lg hover:bg-red-50 disabled:opacity-50 font-medium"
                      title="Reset Circuit Breaker"
                    >
                      {resetting === src.source ? '...' : '↺ Reset'}
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>

          {/* Recent Tasks Table */}
          <div className="bg-white rounded-xl border border-gray-100 shadow-sm overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-100">
              <h2 className="text-lg font-semibold text-gray-900">Recent Tasks</h2>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-gray-50 border-b border-gray-100">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Source</th>
                    <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Type</th>
                    <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Status</th>
                    <th className="px-6 py-3 text-center text-xs font-semibold text-gray-500 uppercase">Found</th>
                    <th className="px-6 py-3 text-center text-xs font-semibold text-gray-500 uppercase">Created</th>
                    <th className="px-6 py-3 text-center text-xs font-semibold text-gray-500 uppercase">Updated</th>
                    <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Started</th>
                    <th className="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Error</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-50">
                  {!data?.recent_tasks?.length ? (
                    <tr><td colSpan={8} className="py-12 text-center text-gray-400">No recent tasks</td></tr>
                  ) : data.recent_tasks.map((t: any) => (
                    <tr key={t.id} className="hover:bg-gray-50">
                      <td className="px-6 py-3 font-medium capitalize">{t.source_platform ?? '—'}</td>
                      <td className="px-6 py-3 text-gray-500">{t.task_type}</td>
                      <td className="px-6 py-3">
                        <StatusPill status={t.status} />
                      </td>
                      <td className="px-6 py-3 text-center">{t.jobs_found}</td>
                      <td className="px-6 py-3 text-center text-green-700">{t.jobs_created}</td>
                      <td className="px-6 py-3 text-center text-blue-700">{t.jobs_updated}</td>
                      <td className="px-6 py-3 text-gray-500 text-xs">{t.created_at ? new Date(t.created_at).toLocaleString() : '—'}</td>
                      <td className="px-6 py-3 text-red-600 text-xs max-w-[180px] truncate" title={t.error_message ?? ''}>{t.error_message ?? '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
      {/* Scraper Config Modal */}
      {showConfig && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          {/* Backdrop */}
          <div 
            className="absolute inset-0 bg-black/50 backdrop-blur-sm transition-opacity" 
            onClick={() => setShowConfig(null)}
          />
          
          {/* Modal Content */}
          <div className="relative w-full max-w-md bg-white rounded-2xl p-6 shadow-2xl transform transition-all border border-gray-100">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-bold text-gray-900 capitalize">Trigger {showConfig} Scrape</h2>
              <button onClick={() => setShowConfig(null)} className="text-gray-400 hover:text-gray-600">
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" /></svg>
              </button>
            </div>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Select Provider</label>
                <select 
                  value={config.provider}
                  onChange={(e) => setConfig({ ...config, provider: e.target.value })}
                  className="w-full p-2.5 border border-gray-300 rounded-lg text-sm bg-gray-50 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all"
                >
                  {SCRAPER_PROVIDERS.map(p => (
                    <option key={p.id} value={p.id}>{p.name} ({p.type})</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">API Key Override (Optional)</label>
                <input 
                  type="password"
                  placeholder="Leave blank for system default"
                  value={config.api_key || ''}
                  onChange={(e) => setConfig({ ...config, api_key: e.target.value })}
                  className="w-full p-2.5 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all"
                />
              </div>

              <div className="relative py-2">
                <div className="absolute inset-0 flex items-center"><div className="w-full border-t border-gray-100"></div></div>
                <div className="relative flex justify-center text-xs uppercase"><span className="bg-white px-2 text-gray-400">Advanced</span></div>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Custom Search URL (Optional)</label>
                <input 
                  type="text"
                  placeholder="Platform specific search URL"
                  value={config.search_url || ''}
                  onChange={(e) => setConfig({ ...config, search_url: e.target.value })}
                  className="w-full p-2.5 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all"
                />
              </div>
            </div>

            <div className="flex gap-3 mt-8">
              <button
                onClick={() => setShowConfig(null)}
                className="flex-1 py-2.5 text-sm font-semibold text-gray-600 bg-gray-50 border border-gray-200 rounded-lg hover:bg-gray-100 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleTrigger}
                className="flex-1 py-2.5 text-sm font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 shadow-md shadow-blue-200 transition-all"
              >
                Confirm & Start
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

function StatusPill({ status }: { status: string }) {
  const map: Record<string, string> = {
    completed: 'bg-green-100 text-green-800',
    running: 'bg-blue-100 text-blue-800',
    failed: 'bg-red-100 text-red-800',
    pending: 'bg-yellow-100 text-yellow-800',
    skipped: 'bg-gray-100 text-gray-600',
  }
  return (
    <span className={`px-2 py-1 rounded-full text-xs font-semibold ${map[status] ?? 'bg-gray-100 text-gray-600'}`}>
      {status}
    </span>
  )
}
