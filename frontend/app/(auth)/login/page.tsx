'use client'

import { Suspense, useEffect, useState } from 'react'
import Link from 'next/link'
import { useRouter, useSearchParams } from 'next/navigation'

const MAIN_DOMAIN = 'factory.supportbox.cloud'
const COOKIE_NAME = 'sf_token'

function setAuthCookie(token: string) {
  // Set for all subdomains so middleware can read it
  const expires = new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toUTCString()
  document.cookie = `${COOKIE_NAME}=${token}; domain=.${MAIN_DOMAIN}; path=/; expires=${expires}; SameSite=Lax`
}

function LoginForm() {
  const router       = useRouter()
  const searchParams = useSearchParams()
  const workspace    = searchParams.get('workspace') // set by middleware on subdomain
  const [form, setForm]             = useState({ email: '', password: '' })
  const [error, setError]           = useState('')
  const [loading, setLoading]       = useState(false)
  const [workspaceName, setWorkspaceName] = useState<string | null>(null)

  // Fetch workspace branding if on a subdomain login
  useEffect(() => {
    if (!workspace) return
    fetch(`/api/v1/auth/workspace/${workspace}`)
      .then(r => r.ok ? r.json() : null)
      .then(d => d && setWorkspaceName(d.name))
      .catch(() => {})
  }, [workspace])

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError('')

    try {
      const res = await fetch('/api/v1/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form),
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || 'Login failed')

      // Store in localStorage (main domain) AND cookie (all subdomains)
      localStorage.setItem('token', data.access_token)
      setAuthCookie(data.access_token)

      // After login: redirect to /dashboard on current origin (works on both main + subdomain)
      router.push('/dashboard')
    } catch (err: any) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-slate-950 flex items-center justify-center p-4">
      <div className="w-full max-w-sm">
        {/* Logo / workspace branding */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center gap-2 mb-4">
            <div className="w-8 h-8 bg-gradient-to-br from-indigo-500 to-cyan-500 rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-sm">SF</span>
            </div>
            <span className="text-white font-bold text-lg">
              {workspaceName ?? 'SaaS Factory'}
            </span>
          </div>
          <h1 className="text-2xl font-bold text-white">
            {workspaceName ? `Sign in to ${workspaceName}` : 'Welcome back'}
          </h1>
          <p className="text-slate-400 text-sm mt-1">
            {workspaceName
              ? `${workspace}.${MAIN_DOMAIN}`
              : 'Sign in to your workspace'}
          </p>
        </div>

        <form onSubmit={submit} className="space-y-4">
          {error && (
            <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-3 text-red-400 text-sm">
              {error}
            </div>
          )}

          <div>
            <label className="block text-sm text-slate-400 mb-1.5">Email</label>
            <input
              type="email"
              required
              value={form.email}
              onChange={(e) => setForm({ ...form, email: e.target.value })}
              className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-2.5 text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition text-sm"
              placeholder="you@example.com"
            />
          </div>

          <div>
            <label className="block text-sm text-slate-400 mb-1.5">Password</label>
            <input
              type="password"
              required
              value={form.password}
              onChange={(e) => setForm({ ...form, password: e.target.value })}
              className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-2.5 text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition text-sm"
              placeholder="••••••••"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-indigo-600 hover:bg-indigo-700 text-white font-medium py-2.5 rounded-lg transition disabled:opacity-50"
          >
            {loading ? 'Signing in...' : 'Sign in'}
          </button>
        </form>

        <p className="text-center text-slate-500 text-sm mt-6">
          No account?{' '}
          <Link href="/register" className="text-indigo-400 hover:text-indigo-300 transition">
            Create one free
          </Link>
        </p>

        {/* On subdomain: link back to main factory */}
        {workspace && (
          <p className="text-center text-slate-600 text-xs mt-4">
            <a href={`https://${MAIN_DOMAIN}`} className="hover:text-slate-400 transition">
              ← Back to SaaS Factory
            </a>
          </p>
        )}
      </div>
    </div>
  )
}

export default function LoginPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-slate-950 flex items-center justify-center">
        <div className="text-slate-400 text-sm">Loading...</div>
      </div>
    }>
      <LoginForm />
    </Suspense>
  )
}
