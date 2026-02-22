'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'

interface Stats {
  extensions_active: number
  projects: number
  ai_builds: number
}

export default function DashboardHome() {
  const [stats] = useState<Stats>({ extensions_active: 0, projects: 1, ai_builds: 0 })

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white">Dashboard</h1>
        <p className="text-slate-400 mt-1">Welcome to your SaaS Factory workspace.</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
        {[
          { label: 'Active Extensions', value: stats.extensions_active, icon: '⬡' },
          { label: 'Projects', value: stats.projects, icon: '⊞' },
          { label: 'AI Builds', value: stats.ai_builds, icon: '✦' },
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
