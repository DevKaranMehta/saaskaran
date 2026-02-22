'use client'

import { useEffect, useState, Suspense } from 'react'
import Link from 'next/link'
import { useSearchParams, useRouter } from 'next/navigation'

const TEMPLATE_INFO: Record<string, { name: string; emoji: string; tip: string }> = {
  blank:     { name: 'Blank',        emoji: '✨', tip: 'Use the AI builder to add any feature you need.' },
  lms:       { name: 'LMS',          emoji: '📚', tip: 'Build courses, quizzes and certificates with the AI builder.' },
  crm:       { name: 'CRM',          emoji: '📊', tip: 'Your CRM extensions are active. Add more with the AI builder.' },
  helpdesk:  { name: 'Helpdesk',     emoji: '🎧', tip: 'Live chat and forms are ready. Build ticket workflows with AI.' },
  ecommerce: { name: 'E-commerce',   emoji: '🛒', tip: 'Billing and invoicing are active. Add products catalog with AI.' },
  hr:        { name: 'HR System',    emoji: '👥', tip: 'Forms and notifications are active. Add employee modules with AI.' },
  saas:      { name: 'SaaS Starter', emoji: '🚀', tip: 'Billing and marketplace are active. Keep building with AI.' },
}

function WelcomeBanner({ templateId, onDismiss }: { templateId: string; onDismiss: () => void }) {
  const info = TEMPLATE_INFO[templateId] ?? TEMPLATE_INFO.blank
  return (
    <div className="mb-8 bg-gradient-to-r from-indigo-600/20 to-cyan-600/20 border border-indigo-500/40 rounded-xl p-6 relative">
      <button
        onClick={onDismiss}
        className="absolute top-4 right-4 text-slate-500 hover:text-slate-300 transition text-lg leading-none"
        aria-label="Dismiss"
      >
        ×
      </button>
      <div className="flex items-start gap-4">
        <div className="text-4xl">{info.emoji}</div>
        <div className="flex-1">
          <h2 className="text-lg font-bold text-white mb-1">
            Your {info.name} workspace is ready!
          </h2>
          <p className="text-slate-300 text-sm mb-4">{info.tip}</p>
          <div className="flex flex-wrap gap-3">
            <Link
              href="/ai"
              className="inline-flex items-center gap-2 bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-medium px-4 py-2 rounded-lg transition"
            >
              ✦ Open AI Builder
            </Link>
            <Link
              href="/extensions"
              className="inline-flex items-center gap-2 bg-slate-700 hover:bg-slate-600 text-white text-sm font-medium px-4 py-2 rounded-lg transition"
            >
              ⬡ View Active Extensions
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}

function DashboardContent() {
  const searchParams = useSearchParams()
  const router = useRouter()
  const [showWelcome, setShowWelcome] = useState(false)
  const [templateId, setTemplateId] = useState('')
  const [activeCount, setActiveCount] = useState(0)

  useEffect(() => {
    const welcome = searchParams.get('welcome')
    const tmpl = searchParams.get('template') || 'blank'
    if (welcome === '1') {
      setShowWelcome(true)
      setTemplateId(tmpl)
      // Clean URL without losing navigation
      const url = new URL(window.location.href)
      url.searchParams.delete('welcome')
      url.searchParams.delete('template')
      window.history.replaceState({}, '', url.toString())
    }
  }, [searchParams])

  useEffect(() => {
    const token = localStorage.getItem('token') || getCookieToken()
    if (!token) return
    fetch('/api/v1/extensions/', { headers: { Authorization: `Bearer ${token}` } })
      .then((r) => r.json())
      .then((d) => {
        const active = (d.extensions || []).filter((e: any) => e.active).length
        setActiveCount(active)
      })
      .catch(() => {})
  }, [])

  function getCookieToken() {
    const match = document.cookie.match(/(?:^|;\s*)sf_token=([^;]*)/)
    return match ? match[1] : null
  }

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white">Dashboard</h1>
        <p className="text-slate-400 mt-1">Welcome to your SaaS Factory workspace.</p>
      </div>

      {showWelcome && (
        <WelcomeBanner templateId={templateId} onDismiss={() => setShowWelcome(false)} />
      )}

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
        {[
          { label: 'Active Extensions', value: activeCount, icon: '⬡' },
          { label: 'Projects', value: 1, icon: '⊞' },
          { label: 'AI Builds', value: 0, icon: '✦' },
        ].map((s) => (
          <div key={s.label} className="bg-slate-800 rounded-xl p-5 border border-slate-700">
            <div className="text-2xl mb-2">{s.icon}</div>
            <div className="text-3xl font-bold text-white">{s.value}</div>
            <div className="text-sm text-slate-400 mt-1">{s.label}</div>
          </div>
        ))}
      </div>

      {/* Quick actions */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Link
          href="/ai"
          className="group bg-gradient-to-br from-indigo-600/20 to-cyan-600/20 border border-indigo-500/30 rounded-xl p-6 hover:border-indigo-500/60 transition"
        >
          <div className="text-3xl mb-3">✦</div>
          <h3 className="text-lg font-semibold text-white mb-1">AI Extension Builder</h3>
          <p className="text-sm text-slate-400">Describe what you want — AI builds it as a pluggable extension.</p>
          <div className="mt-4 text-indigo-400 text-sm group-hover:text-indigo-300 transition">
            Open AI Builder →
          </div>
        </Link>

        <Link
          href="/extensions"
          className="group bg-slate-800 border border-slate-700 rounded-xl p-6 hover:border-slate-600 transition"
        >
          <div className="text-3xl mb-3">⬡</div>
          <h3 className="text-lg font-semibold text-white mb-1">Manage Extensions</h3>
          <p className="text-sm text-slate-400">Browse, install, activate, and deactivate extensions for your SaaS.</p>
          <div className="mt-4 text-slate-400 text-sm group-hover:text-white transition">
            Browse Extensions →
          </div>
        </Link>
      </div>
    </div>
  )
}

export default function DashboardHome() {
  return (
    <Suspense fallback={<div className="p-8 text-slate-400">Loading...</div>}>
      <DashboardContent />
    </Suspense>
  )
}
