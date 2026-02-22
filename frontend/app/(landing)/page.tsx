'use client'

import Link from 'next/link'
import { useState } from 'react'

const TEMPLATES = [
  { id: 'lms',       emoji: '📚', name: 'LMS',         desc: 'Courses, quizzes, certificates, student progress tracking' },
  { id: 'crm',       emoji: '📊', name: 'CRM',         desc: 'Contacts, deal pipeline, email templates, reports' },
  { id: 'helpdesk',  emoji: '🎧', name: 'Helpdesk',    desc: 'Tickets, agents, knowledge base, live chat' },
  { id: 'ecommerce', emoji: '🛒', name: 'E-commerce',  desc: 'Products, orders, payments, inventory, shipping' },
  { id: 'hr',        emoji: '👥', name: 'HR System',   desc: 'Employees, leave, payroll, recruitment, onboarding' },
  { id: 'saas',      emoji: '🚀', name: 'SaaS Starter',desc: 'Billing, tenants, onboarding flow, analytics' },
  { id: 'blank',     emoji: '✨', name: 'Blank',       desc: 'Start from scratch — AI builds anything you describe' },
]

const HOW_IT_WORKS = [
  { step: '01', title: 'Pick a Template', desc: 'Choose from LMS, CRM, Helpdesk, E-commerce, HR, or start blank. Each template comes with the right extensions pre-activated.' },
  { step: '02', title: 'AI Builds Features', desc: 'Describe what you want in plain English. Claude AI generates complete, production-ready extension code — routes, models, UI, tests.' },
  { step: '03', title: 'Launch & Scale', desc: 'Activate extensions like plugins. Publish to the marketplace. Export your code. Deploy anywhere with Docker.' },
]

export default function LandingPage() {
  const [selectedTemplate, setSelectedTemplate] = useState<string | null>(null)

  return (
    <div className="min-h-screen bg-white dark:bg-slate-950">
      {/* Navbar */}
      <nav className="fixed top-0 w-full z-50 bg-white/80 dark:bg-slate-950/80 backdrop-blur-md border-b border-slate-200 dark:border-slate-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-500 to-cyan-500 flex items-center justify-center text-white text-sm font-bold">SF</div>
            <span className="text-lg font-bold gradient-text">SaaS Factory</span>
          </div>
          <div className="hidden md:flex items-center gap-8 text-sm text-slate-600 dark:text-slate-400">
            <a href="#templates" className="hover:text-indigo-600 transition">Templates</a>
            <a href="#how-it-works" className="hover:text-indigo-600 transition">How it works</a>
            <a href="#marketplace" className="hover:text-indigo-600 transition">Marketplace</a>
          </div>
          <div className="flex items-center gap-3">
            <Link href="/login" className="text-sm font-medium text-slate-700 dark:text-slate-300 hover:text-indigo-600 transition">Sign in</Link>
            <Link href="/register" className="text-sm font-semibold bg-indigo-600 text-white px-4 py-2 rounded-lg hover:bg-indigo-700 transition shadow-lg shadow-indigo-500/25">
              Start Building Free
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="pt-32 pb-24 px-4 text-center">
        <div className="max-w-5xl mx-auto">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-50 dark:bg-indigo-950 text-indigo-600 dark:text-indigo-400 text-sm font-medium mb-8">
            <span className="w-2 h-2 rounded-full bg-indigo-500 animate-pulse-slow" />
            Powered by Claude AI
          </div>
          <h1 className="text-6xl sm:text-7xl lg:text-8xl font-extrabold tracking-tight leading-none mb-6 text-slate-900 dark:text-white">
            Build any SaaS
            <span className="gradient-text block mt-2">with AI in minutes</span>
          </h1>
          <p className="text-xl text-slate-600 dark:text-slate-400 max-w-2xl mx-auto mb-10 leading-relaxed">
            Pick a template. Describe features in plain English. AI generates production-ready extensions — models, routes, UI, tests. Deploy anywhere.
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link href="/register" className="w-full sm:w-auto px-8 py-4 bg-indigo-600 text-white font-semibold rounded-xl hover:bg-indigo-700 transition shadow-xl shadow-indigo-500/30 text-lg">
              Start Building — Free
            </Link>
            <a href="#how-it-works" className="w-full sm:w-auto px-8 py-4 bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 font-semibold rounded-xl hover:bg-slate-200 dark:hover:bg-slate-700 transition text-lg">
              See How It Works ↓
            </a>
          </div>
        </div>
      </section>

      {/* Template selector */}
      <section id="templates" className="py-24 px-4 bg-slate-50 dark:bg-slate-900">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold text-slate-900 dark:text-white mb-4">Start with a template</h2>
            <p className="text-slate-600 dark:text-slate-400 text-lg">Each template comes with the right extensions pre-installed. Customize everything.</p>
          </div>
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {TEMPLATES.map((t) => (
              <div
                key={t.id}
                onClick={() => setSelectedTemplate(t.id)}
                className={`relative bg-white dark:bg-slate-800 rounded-2xl border-2 p-6 cursor-pointer transition-all duration-200 hover:shadow-xl group
                  ${selectedTemplate === t.id
                    ? 'border-indigo-500 shadow-xl shadow-indigo-500/20'
                    : 'border-slate-200 dark:border-slate-700 hover:border-indigo-300 dark:hover:border-indigo-700'
                  }`}
              >
                {selectedTemplate === t.id && (
                  <div className="absolute top-3 right-3 w-6 h-6 bg-indigo-600 rounded-full flex items-center justify-center text-white text-xs">✓</div>
                )}
                <div className="text-4xl mb-3">{t.emoji}</div>
                <h3 className="text-lg font-bold text-slate-900 dark:text-white mb-2">{t.name}</h3>
                <p className="text-sm text-slate-600 dark:text-slate-400 leading-relaxed">{t.desc}</p>
                <div className="mt-4 text-xs font-semibold text-indigo-600 dark:text-indigo-400 opacity-0 group-hover:opacity-100 transition">
                  Select template →
                </div>
              </div>
            ))}
          </div>
          {selectedTemplate && (
            <div className="mt-10 text-center animate-slide-up">
              <Link
                href={`/register?template=${selectedTemplate}`}
                className="inline-flex items-center gap-2 px-10 py-4 bg-indigo-600 text-white font-bold rounded-xl hover:bg-indigo-700 transition shadow-xl shadow-indigo-500/30 text-lg"
              >
                Build with {TEMPLATES.find(t => t.id === selectedTemplate)?.name} →
              </Link>
            </div>
          )}
        </div>
      </section>

      {/* How it works */}
      <section id="how-it-works" className="py-24 px-4">
        <div className="max-w-5xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold text-slate-900 dark:text-white mb-4">How it works</h2>
          </div>
          <div className="grid md:grid-cols-3 gap-8">
            {HOW_IT_WORKS.map((step) => (
              <div key={step.step} className="text-center">
                <div className="w-14 h-14 rounded-2xl bg-indigo-50 dark:bg-indigo-950 flex items-center justify-center mx-auto mb-4">
                  <span className="text-2xl font-black text-indigo-600 dark:text-indigo-400">{step.step}</span>
                </div>
                <h3 className="text-xl font-bold text-slate-900 dark:text-white mb-3">{step.title}</h3>
                <p className="text-slate-600 dark:text-slate-400 leading-relaxed">{step.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-24 px-4 bg-gradient-to-br from-indigo-600 to-cyan-600">
        <div className="max-w-3xl mx-auto text-center text-white">
          <h2 className="text-4xl font-bold mb-4">Ready to build your SaaS?</h2>
          <p className="text-indigo-100 text-xl mb-8">Free to start. No credit card required.</p>
          <Link href="/register" className="inline-block px-10 py-4 bg-white text-indigo-700 font-bold rounded-xl hover:bg-indigo-50 transition shadow-xl text-lg">
            Start Building for Free
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-12 px-4 border-t border-slate-200 dark:border-slate-800 text-center text-sm text-slate-500">
        <p>© 2026 SaaS Factory. All rights reserved.</p>
      </footer>
    </div>
  )
}
