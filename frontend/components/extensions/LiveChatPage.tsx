'use client'

import { useState, useEffect, useRef, useCallback } from 'react'

// ── Types ──────────────────────────────────────────────────────────────────

interface Site {
  id: string
  name: string
  url: string
  site_key: string
  color: string
  greeting: string
  is_active: boolean
  created_at: string
}

interface Conversation {
  id: string
  site_id: string
  visitor_name: string
  visitor_email: string | null
  status: 'open' | 'closed'
  message_count: number
  unread_count: number
  last_message: string | null
  last_message_at: string | null
  assigned_to: string | null
  created_at: string
}

interface Message {
  id: string
  conversation_id: string
  content: string
  sender: 'visitor' | 'agent'
  sender_name: string
  is_read: boolean
  created_at: string
}

interface Stats {
  total_conversations: number
  open_conversations: number
  total_unread: number
  total_sites: number
}

// ── API helper ─────────────────────────────────────────────────────────────

function useApi() {
  const token = typeof window !== 'undefined' ? localStorage.getItem('token') : ''
  const headers = { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` }
  const base = '/api/v1/live-chat'

  const get = (path: string) => fetch(base + path, { headers }).then(r => r.json())
  const post = (path: string, body: object) =>
    fetch(base + path, { method: 'POST', headers, body: JSON.stringify(body) }).then(r => r.json())
  const patch = (path: string, body: object) =>
    fetch(base + path, { method: 'PATCH', headers, body: JSON.stringify(body) }).then(r => r.json())
  const del = (path: string) =>
    fetch(base + path, { method: 'DELETE', headers })

  return { get, post, patch, del }
}

// ── Embed Code Generator ────────────────────────────────────────────────────

function EmbedCodeModal({ site, onClose }: { site: Site; onClose: () => void }) {
  const [copied, setCopied] = useState(false)
  const origin = typeof window !== 'undefined' ? window.location.origin : 'https://yourapp.com'
  const code = `<script src="${origin}/api/v1/live-chat/widget/${site.site_key}/script.js" defer><\/script>`

  const copy = () => {
    navigator.clipboard.writeText(code)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
      <div className="bg-slate-800 rounded-2xl p-6 w-full max-w-lg border border-slate-700">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-white font-semibold text-lg">Embed Code — {site.name}</h3>
          <button onClick={onClose} className="text-slate-400 hover:text-white text-xl">×</button>
        </div>
        <p className="text-slate-400 text-sm mb-3">
          Add this snippet inside the <code className="text-indigo-400">&lt;head&gt;</code> or before the closing <code className="text-indigo-400">&lt;/body&gt;</code> tag of your website:
        </p>
        <div className="bg-slate-900 rounded-xl p-4 font-mono text-xs text-green-300 break-all mb-4 select-all border border-slate-700">
          {code}
        </div>
        <div className="flex gap-3">
          <button
            onClick={copy}
            className="flex-1 py-2.5 rounded-lg font-medium text-sm transition"
            style={{ background: copied ? '#22c55e' : '#6366f1', color: '#fff' }}
          >
            {copied ? '✓ Copied!' : 'Copy Code'}
          </button>
          <button onClick={onClose} className="px-4 py-2.5 bg-slate-700 text-slate-300 rounded-lg text-sm hover:bg-slate-600">
            Close
          </button>
        </div>
        <p className="text-slate-500 text-xs mt-3">
          Site key: <span className="text-slate-300 font-mono">{site.site_key}</span>
        </p>
      </div>
    </div>
  )
}

// ── Add Site Modal ─────────────────────────────────────────────────────────

function AddSiteModal({ onClose, onCreated }: { onClose: () => void; onCreated: (site: Site) => void }) {
  const api = useApi()
  const [form, setForm] = useState({ name: '', url: '', color: '#6366f1', greeting: 'Hi! How can we help you today?' })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const submit = async () => {
    if (!form.name || !form.url) { setError('Name and URL are required'); return }
    setLoading(true)
    try {
      const site = await api.post('/sites', form)
      if (site.id) onCreated(site)
      else setError(site.detail || 'Failed to create site')
    } catch { setError('Network error') }
    setLoading(false)
  }

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
      <div className="bg-slate-800 rounded-2xl p-6 w-full max-w-md border border-slate-700">
        <div className="flex items-center justify-between mb-5">
          <h3 className="text-white font-semibold text-lg">Add Website</h3>
          <button onClick={onClose} className="text-slate-400 hover:text-white text-xl">×</button>
        </div>
        <div className="flex flex-col gap-3">
          <div>
            <label className="text-slate-400 text-xs mb-1 block">Website Name *</label>
            <input
              className="w-full bg-slate-900 border border-slate-600 rounded-lg px-3 py-2 text-white text-sm outline-none focus:border-indigo-500"
              placeholder="My Website"
              value={form.name}
              onChange={e => setForm(f => ({ ...f, name: e.target.value }))}
            />
          </div>
          <div>
            <label className="text-slate-400 text-xs mb-1 block">Website URL *</label>
            <input
              className="w-full bg-slate-900 border border-slate-600 rounded-lg px-3 py-2 text-white text-sm outline-none focus:border-indigo-500"
              placeholder="https://mywebsite.com"
              value={form.url}
              onChange={e => setForm(f => ({ ...f, url: e.target.value }))}
            />
          </div>
          <div>
            <label className="text-slate-400 text-xs mb-1 block">Greeting Message</label>
            <input
              className="w-full bg-slate-900 border border-slate-600 rounded-lg px-3 py-2 text-white text-sm outline-none focus:border-indigo-500"
              value={form.greeting}
              onChange={e => setForm(f => ({ ...f, greeting: e.target.value }))}
            />
          </div>
          <div>
            <label className="text-slate-400 text-xs mb-1 block">Widget Color</label>
            <div className="flex items-center gap-3">
              <input
                type="color"
                className="w-10 h-10 rounded cursor-pointer border-0 bg-transparent"
                value={form.color}
                onChange={e => setForm(f => ({ ...f, color: e.target.value }))}
              />
              <span className="text-slate-300 text-sm font-mono">{form.color}</span>
            </div>
          </div>
          {error && <p className="text-red-400 text-xs">{error}</p>}
          <div className="flex gap-3 pt-1">
            <button
              onClick={submit}
              disabled={loading}
              className="flex-1 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg font-medium text-sm disabled:opacity-50 transition"
            >
              {loading ? 'Creating…' : 'Create Site'}
            </button>
            <button onClick={onClose} className="px-4 py-2.5 bg-slate-700 text-slate-300 rounded-lg text-sm hover:bg-slate-600">
              Cancel
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

// ── Conversation Thread ────────────────────────────────────────────────────

function ConvThread({
  conv,
  onClose,
  onStatusChange,
}: {
  conv: Conversation
  onClose: () => void
  onStatusChange: (id: string, status: 'open' | 'closed') => void
}) {
  const api = useApi()
  const [messages, setMessages] = useState<Message[]>([])
  const [reply, setReply] = useState('')
  const [sending, setSending] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)
  const pollRef = useRef<NodeJS.Timeout | null>(null)

  const loadMessages = useCallback(async () => {
    try {
      const data = await api.get(`/conversations/${conv.id}/messages`)
      if (Array.isArray(data)) setMessages(data)
    } catch {}
  }, [conv.id])

  useEffect(() => {
    loadMessages()
    // Mark as read
    api.post(`/conversations/${conv.id}/mark-read`, {})
    // Poll every 3s for new messages
    pollRef.current = setInterval(loadMessages, 3000)
    return () => { if (pollRef.current) clearInterval(pollRef.current) }
  }, [conv.id])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const sendReply = async () => {
    const text = reply.trim()
    if (!text || sending) return
    setSending(true)
    setReply('')
    try {
      const msg = await api.post(`/conversations/${conv.id}/reply`, { content: text })
      if (msg.id) setMessages(m => [...m, msg])
    } catch {}
    setSending(false)
  }

  const toggleStatus = async () => {
    const newStatus = conv.status === 'open' ? 'closed' : 'open'
    await api.patch(`/conversations/${conv.id}`, { status: newStatus })
    onStatusChange(conv.id, newStatus)
  }

  const fmt = (iso: string) => {
    const d = new Date(iso)
    return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  }

  const fmtDate = (iso: string) => new Date(iso).toLocaleDateString([], { month: 'short', day: 'numeric' })

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center gap-3 px-5 py-4 border-b border-slate-700/50 bg-slate-800/50">
        <button onClick={onClose} className="text-slate-400 hover:text-white transition p-1 rounded">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M19 12H5M12 5l-7 7 7 7"/>
          </svg>
        </button>
        <div className="w-9 h-9 rounded-full bg-indigo-600/30 flex items-center justify-center text-indigo-300 font-bold text-sm flex-shrink-0">
          {conv.visitor_name.charAt(0).toUpperCase()}
        </div>
        <div className="flex-1 min-w-0">
          <div className="text-white font-medium text-sm truncate">{conv.visitor_name}</div>
          <div className="text-slate-500 text-xs truncate">{conv.visitor_email || 'No email'} · {fmtDate(conv.created_at)}</div>
        </div>
        <button
          onClick={toggleStatus}
          className={`text-xs px-3 py-1.5 rounded-full font-medium transition ${
            conv.status === 'open'
              ? 'bg-green-500/15 text-green-400 hover:bg-red-500/15 hover:text-red-400'
              : 'bg-slate-600/40 text-slate-400 hover:bg-green-500/15 hover:text-green-400'
          }`}
        >
          {conv.status === 'open' ? 'Close Chat' : 'Reopen'}
        </button>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-5 space-y-3">
        {messages.length === 0 && (
          <div className="text-center text-slate-500 text-sm py-8">No messages yet</div>
        )}
        {messages.map(msg => (
          <div key={msg.id} className={`flex ${msg.sender === 'agent' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-[75%] ${msg.sender === 'agent' ? 'items-end' : 'items-start'} flex flex-col gap-1`}>
              <div className="text-xs text-slate-500">{msg.sender_name} · {fmt(msg.created_at)}</div>
              <div className={`px-4 py-2.5 rounded-2xl text-sm leading-relaxed ${
                msg.sender === 'agent'
                  ? 'bg-indigo-600 text-white rounded-br-sm'
                  : 'bg-slate-700/80 text-slate-100 rounded-bl-sm'
              }`}>
                {msg.content}
              </div>
            </div>
          </div>
        ))}
        <div ref={bottomRef} />
      </div>

      {/* Reply box */}
      {conv.status === 'open' ? (
        <div className="px-4 py-3 border-t border-slate-700/50 flex gap-3 items-end">
          <textarea
            className="flex-1 bg-slate-700/50 border border-slate-600/50 rounded-xl px-4 py-2.5 text-white text-sm resize-none outline-none focus:border-indigo-500/70 placeholder-slate-500 min-h-[42px] max-h-32"
            placeholder="Type your reply…"
            value={reply}
            rows={1}
            onChange={e => setReply(e.target.value)}
            onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendReply() } }}
          />
          <button
            onClick={sendReply}
            disabled={sending || !reply.trim()}
            className="w-10 h-10 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 text-white rounded-xl flex items-center justify-center transition flex-shrink-0"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
              <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/>
            </svg>
          </button>
        </div>
      ) : (
        <div className="px-4 py-3 border-t border-slate-700/50 text-center text-slate-500 text-xs">
          Conversation closed · <button onClick={toggleStatus} className="text-indigo-400 hover:underline">Reopen to reply</button>
        </div>
      )}
    </div>
  )
}

// ── Main Page ──────────────────────────────────────────────────────────────

export default function LiveChatPage() {
  const api = useApi()
  const [tab, setTab] = useState<'conversations' | 'sites'>('conversations')
  const [conversations, setConversations] = useState<Conversation[]>([])
  const [sites, setSites] = useState<Site[]>([])
  const [stats, setStats] = useState<Stats | null>(null)
  const [selectedConv, setSelectedConv] = useState<Conversation | null>(null)
  const [filterStatus, setFilterStatus] = useState<'all' | 'open' | 'closed'>('open')
  const [showAddSite, setShowAddSite] = useState(false)
  const [embedSite, setEmbedSite] = useState<Site | null>(null)
  const [loading, setLoading] = useState(true)
  const pollRef = useRef<NodeJS.Timeout | null>(null)

  const loadAll = useCallback(async () => {
    try {
      const [convData, siteData, statsData] = await Promise.all([
        api.get('/conversations'),
        api.get('/sites'),
        api.get('/stats'),
      ])
      if (Array.isArray(convData)) setConversations(convData)
      if (Array.isArray(siteData)) setSites(siteData)
      if (statsData.total_conversations !== undefined) setStats(statsData)
    } catch {}
    setLoading(false)
  }, [])

  useEffect(() => {
    loadAll()
    pollRef.current = setInterval(loadAll, 5000)
    return () => { if (pollRef.current) clearInterval(pollRef.current) }
  }, [])

  const filtered = conversations.filter(c =>
    filterStatus === 'all' ? true : c.status === filterStatus
  )

  const totalUnread = conversations.reduce((s, c) => s + c.unread_count, 0)

  const handleConvClick = (conv: Conversation) => {
    setSelectedConv(conv)
    // Optimistically clear unread
    setConversations(cs => cs.map(c => c.id === conv.id ? { ...c, unread_count: 0 } : c))
  }

  const handleStatusChange = (id: string, status: 'open' | 'closed') => {
    setConversations(cs => cs.map(c => c.id === id ? { ...c, status } : c))
    if (selectedConv?.id === id) setSelectedConv(c => c ? { ...c, status } : c)
  }

  const deleteSite = async (siteId: string) => {
    if (!confirm('Delete this site? All conversations will be removed.')) return
    await api.del(`/sites/${siteId}`)
    setSites(s => s.filter(x => x.id !== siteId))
  }

  const fmtTime = (iso: string | null) => {
    if (!iso) return ''
    const d = new Date(iso)
    const now = new Date()
    if (d.toDateString() === now.toDateString()) return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    return d.toLocaleDateString([], { month: 'short', day: 'numeric' })
  }

  // ── Conversation selected — show thread ──
  if (selectedConv) {
    return (
      <div className="flex flex-col h-full">
        <ConvThread
          conv={selectedConv}
          onClose={() => setSelectedConv(null)}
          onStatusChange={handleStatusChange}
        />
      </div>
    )
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between px-6 py-4 border-b border-slate-700/50">
        <div className="flex items-center gap-3">
          <span className="text-2xl">💬</span>
          <div>
            <h1 className="text-white font-semibold text-lg">Live Chat</h1>
            <p className="text-slate-500 text-xs">Receive & reply to visitor chats</p>
          </div>
        </div>
        {/* Stats bar */}
        {stats && (
          <div className="flex items-center gap-4 text-sm">
            <div className="text-center">
              <div className="text-white font-bold">{stats.open_conversations}</div>
              <div className="text-slate-500 text-xs">Open</div>
            </div>
            <div className="text-center">
              <div className={`font-bold ${totalUnread > 0 ? 'text-red-400' : 'text-white'}`}>{totalUnread}</div>
              <div className="text-slate-500 text-xs">Unread</div>
            </div>
            <div className="text-center">
              <div className="text-white font-bold">{stats.total_sites}</div>
              <div className="text-slate-500 text-xs">Sites</div>
            </div>
          </div>
        )}
      </div>

      {/* Tabs */}
      <div className="flex gap-1 px-6 pt-3">
        {(['conversations', 'sites'] as const).map(t => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition capitalize ${
              tab === t ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white hover:bg-slate-700/50'
            }`}
          >
            {t}
            {t === 'conversations' && totalUnread > 0 && (
              <span className="ml-2 bg-red-500 text-white text-xs rounded-full px-1.5 py-0.5">{totalUnread}</span>
            )}
          </button>
        ))}
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto px-6 py-4">

        {/* ── Conversations Tab ── */}
        {tab === 'conversations' && (
          <div>
            {/* Filter */}
            <div className="flex gap-2 mb-4">
              {(['open', 'all', 'closed'] as const).map(s => (
                <button
                  key={s}
                  onClick={() => setFilterStatus(s)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-medium transition capitalize ${
                    filterStatus === s ? 'bg-slate-600 text-white' : 'text-slate-500 hover:text-white'
                  }`}
                >
                  {s}
                </button>
              ))}
            </div>

            {loading && (
              <div className="text-slate-500 text-sm text-center py-12">Loading…</div>
            )}

            {!loading && filtered.length === 0 && (
              <div className="text-center py-16">
                <div className="text-5xl mb-4">💬</div>
                <p className="text-slate-400 font-medium">No {filterStatus !== 'all' ? filterStatus : ''} conversations</p>
                <p className="text-slate-500 text-sm mt-1">
                  Add a website in the <button onClick={() => setTab('sites')} className="text-indigo-400 hover:underline">Sites tab</button> and embed the chat widget to start receiving chats.
                </p>
              </div>
            )}

            <div className="space-y-2">
              {filtered.map(conv => (
                <div
                  key={conv.id}
                  onClick={() => handleConvClick(conv)}
                  className={`flex items-center gap-4 p-4 rounded-xl border cursor-pointer transition group ${
                    conv.unread_count > 0
                      ? 'bg-indigo-600/10 border-indigo-500/30 hover:bg-indigo-600/15'
                      : 'bg-slate-800/40 border-slate-700/40 hover:bg-slate-700/40'
                  }`}
                >
                  {/* Avatar */}
                  <div className={`w-10 h-10 rounded-full flex items-center justify-center font-bold text-sm flex-shrink-0 ${
                    conv.unread_count > 0 ? 'bg-indigo-600 text-white' : 'bg-slate-700 text-slate-300'
                  }`}>
                    {conv.visitor_name.charAt(0).toUpperCase()}
                  </div>

                  {/* Info */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className={`text-sm font-medium truncate ${conv.unread_count > 0 ? 'text-white' : 'text-slate-300'}`}>
                        {conv.visitor_name}
                      </span>
                      {conv.status === 'closed' && (
                        <span className="text-xs bg-slate-600/60 text-slate-400 px-2 py-0.5 rounded-full">closed</span>
                      )}
                    </div>
                    <p className={`text-xs truncate mt-0.5 ${conv.unread_count > 0 ? 'text-slate-300' : 'text-slate-500'}`}>
                      {conv.last_message || conv.visitor_email || 'No messages yet'}
                    </p>
                  </div>

                  {/* Right */}
                  <div className="flex flex-col items-end gap-1.5 flex-shrink-0">
                    <span className="text-xs text-slate-500">{fmtTime(conv.last_message_at || conv.created_at)}</span>
                    {conv.unread_count > 0 && (
                      <span className="bg-red-500 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center font-bold">
                        {conv.unread_count > 9 ? '9+' : conv.unread_count}
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ── Sites Tab ── */}
        {tab === 'sites' && (
          <div>
            <div className="flex justify-between items-center mb-4">
              <p className="text-slate-400 text-sm">Register websites to get embed codes for the chat widget.</p>
              <button
                onClick={() => setShowAddSite(true)}
                className="flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-sm rounded-lg font-medium transition"
              >
                <span>+</span> Add Website
              </button>
            </div>

            {sites.length === 0 && !loading && (
              <div className="text-center py-16">
                <div className="text-5xl mb-4">🌐</div>
                <p className="text-slate-400 font-medium">No websites yet</p>
                <p className="text-slate-500 text-sm mt-1">Add your website to get an embed code for the chat widget.</p>
                <button
                  onClick={() => setShowAddSite(true)}
                  className="mt-4 px-5 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white text-sm rounded-lg font-medium transition"
                >
                  Add Your First Website
                </button>
              </div>
            )}

            <div className="grid gap-4 sm:grid-cols-2">
              {sites.map(site => (
                <div key={site.id} className="bg-slate-800/50 border border-slate-700/50 rounded-xl p-4">
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-lg flex items-center justify-center text-white font-bold text-sm"
                        style={{ background: site.color }}>
                        {site.name.charAt(0).toUpperCase()}
                      </div>
                      <div>
                        <div className="text-white font-medium text-sm">{site.name}</div>
                        <div className="text-slate-500 text-xs truncate max-w-[160px]">{site.url}</div>
                      </div>
                    </div>
                    <div className="flex gap-2">
                      <button
                        onClick={() => setEmbedSite(site)}
                        className="text-xs px-3 py-1.5 bg-indigo-600/20 text-indigo-400 hover:bg-indigo-600/30 rounded-lg transition font-medium"
                      >
                        &lt;/&gt; Embed
                      </button>
                      <button
                        onClick={() => deleteSite(site.id)}
                        className="text-xs px-3 py-1.5 bg-red-500/10 text-red-400 hover:bg-red-500/20 rounded-lg transition"
                      >
                        Delete
                      </button>
                    </div>
                  </div>
                  <div className="bg-slate-900/60 rounded-lg px-3 py-2">
                    <p className="text-slate-500 text-xs mb-0.5">Greeting</p>
                    <p className="text-slate-300 text-xs truncate">{site.greeting}</p>
                  </div>
                  <div className="mt-2 flex items-center gap-2">
                    <div className="w-2 h-2 rounded-full" style={{ background: site.color }} />
                    <span className="text-slate-500 text-xs font-mono">{site.site_key.slice(0, 16)}…</span>
                    <span className={`ml-auto text-xs px-2 py-0.5 rounded-full ${site.is_active ? 'bg-green-500/15 text-green-400' : 'bg-slate-600/40 text-slate-500'}`}>
                      {site.is_active ? 'Active' : 'Disabled'}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Modals */}
      {showAddSite && (
        <AddSiteModal
          onClose={() => setShowAddSite(false)}
          onCreated={site => { setSites(s => [site, ...s]); setShowAddSite(false); setEmbedSite(site) }}
        />
      )}
      {embedSite && <EmbedCodeModal site={embedSite} onClose={() => setEmbedSite(null)} />}
    </div>
  )
}
