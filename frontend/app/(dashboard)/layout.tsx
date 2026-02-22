'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'

const MAIN_DOMAIN = 'factory.supportbox.cloud'
const COOKIE_NAME = 'sf_token'

const EXTENSION_ICONS: Record<string, string> = {
  todo_list:        '✓',
  task_management:  '✅',
  kanban:           '⬡',
  kanban_board:     '⬡',
  invoicing:        '💳',
  contacts:         '👥',
  helpdesk:         '🎧',
  appointments:     '📅',
  appointment_booking: '📅',
  roles:            '🔑',
  notes:            '📝',
  analytics:        '📊',
  form_builder:     '📋',
  live_chat:        '💬',
  blog_cms:         '✍',
  customer_portal:  '🏠',
}

const STATIC_NAV = [
  { href: '/dashboard',   label: 'Dashboard',   icon: '⊞' },
  { href: '/ai',          label: 'AI Builder',   icon: '✦' },
  { href: '/extensions',  label: 'Extensions',   icon: '⬡' },
  { href: '/marketplace', label: 'Marketplace',  icon: '◈' },
  { href: '/settings',    label: 'Settings',     icon: '⚙' },
]

interface ActiveExtension {
  name: string
  description: string
  active: boolean
}

interface WorkspaceInfo {
  tenant_name: string
  tenant_slug: string
  subdomain: string
}

function getToken(): string | null {
  if (typeof window === 'undefined') return null
  // Prefer localStorage; fall back to cookie (set on subdomain logins)
  const ls = localStorage.getItem('token')
  if (ls) return ls
  const match = document.cookie.match(new RegExp(`(?:^|; )${COOKIE_NAME}=([^;]*)`))
  return match ? decodeURIComponent(match[1]) : null
}

function isOnSubdomain(): boolean {
  if (typeof window === 'undefined') return false
  const host = window.location.hostname
  return host.endsWith(`.${MAIN_DOMAIN}`) && host !== MAIN_DOMAIN
}

function currentSlug(): string {
  if (typeof window === 'undefined') return ''
  return window.location.hostname.replace(`.${MAIN_DOMAIN}`, '')
}

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname()
  const [sidebarOpen, setSidebarOpen]           = useState(true)
  const [activeExtensions, setActiveExtensions] = useState<ActiveExtension[]>([])
  const [workspace, setWorkspace]               = useState<WorkspaceInfo | null>(null)
  const [onSubdomain, setOnSubdomain]           = useState(false)

  // Fetch workspace info + extensions on load and navigation
  useEffect(() => {
    const token = getToken()
    if (!token) {
      window.location.href = '/login'
      return
    }
    // Sync token to localStorage if it came from cookie
    if (!localStorage.getItem('token')) {
      localStorage.setItem('token', token)
    }

    setOnSubdomain(isOnSubdomain())

    // Fetch user info (includes tenant_slug and tenant_name)
    fetch('/api/v1/auth/me', { headers: { Authorization: `Bearer ${token}` } })
      .then(r => r.ok ? r.json() : null)
      .then(d => {
        if (d) setWorkspace({ tenant_name: d.tenant_name, tenant_slug: d.tenant_slug, subdomain: d.subdomain })
      })
      .catch(() => {})

    // Fetch active extensions
    fetch('/api/v1/extensions/', { headers: { Authorization: `Bearer ${token}` } })
      .then(r => r.json())
      .then(d => {
        const exts: ActiveExtension[] = (d.extensions || [])
          .filter((e: ActiveExtension) => e.active && e.name !== 'ai_generator')
        setActiveExtensions(exts)
      })
      .catch(() => {})
  }, [pathname])

  return (
    <div className="flex h-screen bg-slate-950 text-white overflow-hidden">
      {/* Sidebar */}
      <aside className={`${sidebarOpen ? 'w-60' : 'w-16'} flex-shrink-0 bg-slate-900 border-r border-slate-800 flex flex-col transition-all duration-200`}>

        {/* Logo / workspace name */}
        <div className="h-16 flex items-center px-4 border-b border-slate-800 gap-3 min-w-0">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-500 to-cyan-500 flex items-center justify-center text-white text-sm font-bold flex-shrink-0">
            {workspace?.tenant_name?.charAt(0).toUpperCase() ?? 'SF'}
          </div>
          {sidebarOpen && (
            <span className="font-bold text-white truncate text-sm">
              {workspace?.tenant_name ?? 'SaaS Factory'}
            </span>
          )}
        </div>

        {/* Nav */}
        <nav className="flex-1 p-3 space-y-0.5 overflow-y-auto">
          {STATIC_NAV.map((item) => {
            const active = pathname === item.href
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors
                  ${active
                    ? 'bg-indigo-600 text-white'
                    : 'text-slate-400 hover:text-white hover:bg-slate-800'
                  }`}
              >
                <span className="text-base flex-shrink-0">{item.icon}</span>
                {sidebarOpen && item.label}
              </Link>
            )
          })}

          {/* Active extensions */}
          {activeExtensions.length > 0 && (
            <>
              {sidebarOpen && (
                <p className="text-xs text-slate-600 uppercase tracking-widest px-3 pt-4 pb-1 font-medium">
                  Extensions
                </p>
              )}
              {!sidebarOpen && <div className="border-t border-slate-800 my-2 mx-1" />}
              {activeExtensions.map(ext => {
                const href   = `/extensions/${ext.name}`
                const active = pathname === href || pathname.startsWith(href + '/')
                const icon   = EXTENSION_ICONS[ext.name] || '⬡'
                const label  = ext.name.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
                return (
                  <Link
                    key={ext.name}
                    href={href}
                    title={!sidebarOpen ? label : undefined}
                    className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors
                      ${active
                        ? 'bg-indigo-600/80 text-white'
                        : 'text-slate-400 hover:text-white hover:bg-slate-800'
                      }`}
                  >
                    <span className="text-base flex-shrink-0">{icon}</span>
                    {sidebarOpen && <span className="truncate">{label}</span>}
                  </Link>
                )
              })}
            </>
          )}
        </nav>

        {/* Subdomain badge — only shown when on user's own subdomain */}
        {sidebarOpen && onSubdomain && workspace?.tenant_slug && (
          <div className="px-3 pb-2">
            <div className="bg-slate-800 rounded-lg px-3 py-2 border border-slate-700">
              <p className="text-xs text-slate-500 mb-0.5">Your workspace URL</p>
              <p className="text-xs text-indigo-400 font-mono truncate">
                {workspace.tenant_slug}.{MAIN_DOMAIN}
              </p>
            </div>
          </div>
        )}

        {/* If on main domain and workspace has a subdomain, show a link to it */}
        {sidebarOpen && !onSubdomain && workspace?.subdomain && (
          <div className="px-3 pb-2">
            <a
              href={workspace.subdomain}
              className="flex items-center gap-2 bg-slate-800/60 hover:bg-slate-800 rounded-lg px-3 py-2 border border-slate-700 transition group"
            >
              <span className="text-xs text-slate-400 group-hover:text-white transition truncate">
                Open workspace URL ↗
              </span>
            </a>
          </div>
        )}

        {/* Collapse toggle */}
        <button
          onClick={() => setSidebarOpen(!sidebarOpen)}
          className="p-4 text-slate-500 hover:text-white transition text-xs border-t border-slate-800"
        >
          {sidebarOpen ? '← Collapse' : '→'}
        </button>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-hidden flex flex-col">
        {children}
      </main>
    </div>
  )
}
