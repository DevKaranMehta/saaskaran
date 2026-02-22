'use client'

import { Suspense, useEffect, useState } from 'react'
import Link from 'next/link'
import { useSearchParams } from 'next/navigation'

const MAIN_DOMAIN = 'factory.supportbox.cloud'

// Icons for known extension names
const EXT_ICONS: Record<string, string> = {
  contacts:            '👥',
  crm:                 '📊',
  deals:               '🤝',
  invoicing:           '💰',
  invoice_manager:     '💰',
  helpdesk:            '🎧',
  ticket_tracker:      '🎫',
  appointments:        '📅',
  appointment_booking: '📅',
  kanban_board:        '⬡',
  kanban:              '⬡',
  todo_list:           '✓',
  task_tracker:        '📋',
  task_management:     '📋',
  blog_cms:            '✍',
  form_builder:        '📋',
  live_chat:           '💬',
  chatbot:             '🤖',
  customer_portal:     '🏠',
  inventory:           '📦',
  hr:                  '👤',
  expenses:            '💳',
  leads:               '🎯',
  notes:               '📝',
}

interface ExtensionInfo {
  name: string
  label: string
}

interface WorkspacePreviewData {
  name: string
  slug: string
  plan: string
  subdomain: string
  extension_count: number
  extensions: ExtensionInfo[]
  created_at: string
}

function WorkspacePreviewContent() {
  const searchParams = useSearchParams()
  const workspace    = searchParams.get('workspace') || ''

  const [data,    setData]    = useState<WorkspacePreviewData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error,   setError]   = useState(false)

  useEffect(() => {
    if (!workspace) { setError(true); setLoading(false); return }
    fetch(`/api/v1/auth/preview/${workspace}`)
      .then(r => r.ok ? r.json() : null)
      .then(d => { if (d) setData(d); else setError(true) })
      .catch(() => setError(true))
      .finally(() => setLoading(false))
  }, [workspace])

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center">
        <div className="flex gap-1.5">
          {[0, 150, 300].map(d => (
            <div key={d} className="w-2 h-2 rounded-full bg-indigo-500 animate-bounce" style={{ animationDelay: `${d}ms` }} />
          ))}
        </div>
      </div>
    )
  }

  if (error || !data) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center p-8">
        <div className="text-center max-w-sm">
          <div className="text-5xl mb-4">⬡</div>
          <h1 className="text-xl font-bold text-white mb-2">Workspace not found</h1>
          <p className="text-slate-400 text-sm mb-6">
            <span className="font-mono text-slate-300">{workspace}.{MAIN_DOMAIN}</span> doesn't exist yet.
          </p>
          <a href={`https://${MAIN_DOMAIN}`} className="inline-flex items-center gap-2 text-sm text-indigo-400 hover:text-indigo-300 transition">
            ← Build your own at SaaS Factory
          </a>
        </div>
      </div>
    )
  }

  const initials = data.name.split(' ').slice(0, 2).map(w => w[0]).join('').toUpperCase()
  const loginUrl = `/login?workspace=${data.slug}`

  return (
    <div className="min-h-screen bg-slate-950 flex flex-col">

      {/* Header bar */}
      <header className="border-b border-slate-800 px-6 py-3 flex items-center justify-between">
        <div className="flex items-center gap-2 text-slate-500 text-xs font-mono">
          <span className="text-indigo-400">◈</span>
          <span>SaaS Factory</span>
          <span>/</span>
          <span className="text-slate-300">{data.slug}</span>
        </div>
        <a
          href={loginUrl}
          className="text-xs px-3 py-1.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg transition font-medium"
        >
          Sign in →
        </a>
      </header>

      {/* Hero */}
      <main className="flex-1 flex flex-col items-center justify-center px-6 py-16">
        <div className="w-full max-w-lg">

          {/* Workspace avatar + name */}
          <div className="flex flex-col items-center text-center mb-10">
            <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-indigo-500 to-cyan-500 flex items-center justify-center text-white text-3xl font-bold mb-5 shadow-lg shadow-indigo-500/20">
              {initials}
            </div>
            <h1 className="text-3xl font-bold text-white mb-2">{data.name}</h1>
            <p className="text-slate-400 text-sm font-mono">{data.slug}.{MAIN_DOMAIN}</p>

            {data.plan === 'trial' && (
              <span className="mt-3 inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-amber-500/10 text-amber-400 border border-amber-500/20">
                Trial workspace
              </span>
            )}
          </div>

          {/* Extensions showcase */}
          <div className="bg-slate-900 rounded-2xl border border-slate-800 overflow-hidden mb-6">
            <div className="px-5 py-4 border-b border-slate-800 flex items-center justify-between">
              <h2 className="text-sm font-semibold text-white">Active Features</h2>
              <span className="text-xs text-slate-500 font-mono">{data.extension_count} installed</span>
            </div>

            {data.extensions.length === 0 ? (
              <div className="px-5 py-10 text-center">
                <div className="text-3xl mb-3">⬡</div>
                <p className="text-slate-500 text-sm">No features activated yet.</p>
                <p className="text-slate-600 text-xs mt-1">Sign in to activate features via the AI Builder.</p>
              </div>
            ) : (
              <div className="divide-y divide-slate-800/60">
                {data.extensions.map(ext => (
                  <div key={ext.name} className="flex items-center gap-4 px-5 py-3.5">
                    <div className="w-8 h-8 rounded-lg bg-slate-800 border border-slate-700 flex items-center justify-center text-base flex-shrink-0">
                      {EXT_ICONS[ext.name] || '⬡'}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-white">{ext.label}</p>
                      <p className="text-xs text-slate-500 font-mono">{ext.name}</p>
                    </div>
                    <span className="flex-shrink-0 w-2 h-2 rounded-full bg-green-500"></span>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* CTA buttons */}
          <div className="flex flex-col gap-3">
            <a
              href={loginUrl}
              className="flex items-center justify-center gap-2 w-full py-3 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl font-medium transition text-sm"
            >
              Sign in to {data.name}
            </a>
            <a
              href={`https://${MAIN_DOMAIN}/register`}
              className="flex items-center justify-center gap-2 w-full py-3 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl font-medium transition text-sm border border-slate-700"
            >
              Build your own workspace — it's free
            </a>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800 py-4 px-6 text-center">
        <p className="text-xs text-slate-600">
          Built with{' '}
          <a href={`https://${MAIN_DOMAIN}`} className="text-indigo-400 hover:text-indigo-300 transition font-medium">
            SaaS Factory
          </a>
          {' '}— AI-powered SaaS builder
        </p>
      </footer>
    </div>
  )
}

export default function WorkspacePreviewPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-slate-950 flex items-center justify-center">
        <div className="flex gap-1.5">
          {[0, 150, 300].map(d => (
            <div key={d} className="w-2 h-2 rounded-full bg-indigo-500 animate-bounce" style={{ animationDelay: `${d}ms` }} />
          ))}
        </div>
      </div>
    }>
      <WorkspacePreviewContent />
    </Suspense>
  )
}
