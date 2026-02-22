'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'

interface ExtensionInfo {
  name: string
  version: string
  description: string
  author: string
  installed: boolean
  active: boolean
}

const EXTENSION_ICONS: Record<string, string> = {
  ai_generator: '✦',
  contacts: '👥',
  crm: '📊',
  invoicing: '💳',
  helpdesk: '🎧',
  appointments: '📅',
  roles: '🔑',
  courses: '📚',
  tasks: '✅',
}

export default function ExtensionsPage() {
  const [extensions, setExtensions] = useState<ExtensionInfo[]>([])
  const [loading, setLoading] = useState(true)
  const [deleting, setDeleting] = useState<string | null>(null)
  const [confirmDelete, setConfirmDelete] = useState<string | null>(null)

  const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null
  const headers = { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) }

  useEffect(() => {
    fetch('/api/v1/extensions/', { headers })
      .then((r) => r.json())
      .then((d) => setExtensions(d.extensions || []))
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [])

  const toggle = async (name: string, currentlyActive: boolean) => {
    const action = currentlyActive ? 'deactivate' : 'activate'
    const res = await fetch(`/api/v1/extensions/${name}/${action}`, { method: 'POST', headers })
    if (res.ok) {
      setExtensions((prev) =>
        prev.map((e) => (e.name === name ? { ...e, active: !currentlyActive } : e))
      )
    }
  }

  const deleteExtension = async (name: string) => {
    setDeleting(name)
    setConfirmDelete(null)
    try {
      const res = await fetch(`/api/v1/extensions/${name}`, { method: 'DELETE', headers })
      if (res.ok) {
        setExtensions((prev) => prev.filter((e) => e.name !== name))
      }
    } finally {
      setDeleting(null)
    }
  }

  if (loading) {
    return (
      <div className="p-8 flex items-center justify-center h-full">
        <div className="text-slate-500">Loading extensions...</div>
      </div>
    )
  }

  return (
    <div className="p-8">
      {/* Confirm delete modal */}
      {confirmDelete && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50">
          <div className="bg-slate-800 border border-slate-700 rounded-xl p-6 w-full max-w-sm shadow-xl">
            <h2 className="text-white font-semibold text-lg mb-2">Delete Extension?</h2>
            <p className="text-slate-400 text-sm mb-5">
              This will permanently delete <span className="text-white font-medium">{confirmDelete.replace(/_/g, ' ')}</span> and all its files. This cannot be undone.
            </p>
            <div className="flex gap-3">
              <button
                onClick={() => setConfirmDelete(null)}
                className="flex-1 py-2 rounded-lg text-sm font-medium bg-slate-700 text-slate-300 hover:bg-slate-600 transition"
              >
                Cancel
              </button>
              <button
                onClick={() => deleteExtension(confirmDelete)}
                className="flex-1 py-2 rounded-lg text-sm font-medium bg-red-600 text-white hover:bg-red-700 transition"
              >
                Delete
              </button>
            </div>
          </div>
        </div>
      )}

      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Extensions</h1>
          <p className="text-slate-400 mt-1">Install and manage pluggable features for your SaaS.</p>
        </div>
        <div className="text-sm text-slate-500">
          {extensions.filter((e) => e.active).length} of {extensions.length} active
        </div>
      </div>

      {extensions.length === 0 ? (
        <div className="text-center py-16 text-slate-500">
          <div className="text-4xl mb-3">⬡</div>
          <p>No extensions discovered yet.</p>
          <p className="text-sm mt-1">Use the AI builder to generate your first extension.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {extensions.map((ext) => (
            <div
              key={ext.name}
              className={`bg-slate-800 rounded-xl p-5 border transition ${
                ext.active ? 'border-indigo-500/40' : 'border-slate-700'
              }`}
            >
              <div className="flex items-start justify-between mb-3">
                <div className="text-2xl">{EXTENSION_ICONS[ext.name] || '⬡'}</div>
                <div className="flex items-center gap-2">
                  <span
                    className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                      ext.active
                        ? 'bg-indigo-500/20 text-indigo-400'
                        : 'bg-slate-700 text-slate-400'
                    }`}
                  >
                    {ext.active ? 'Active' : 'Inactive'}
                  </span>
                  <button
                    onClick={() => setConfirmDelete(ext.name)}
                    disabled={deleting === ext.name}
                    title="Delete extension"
                    className="text-slate-600 hover:text-red-400 transition text-sm leading-none p-1 rounded hover:bg-red-500/10"
                  >
                    {deleting === ext.name ? '…' : '🗑'}
                  </button>
                </div>
              </div>

              <h3 className="font-semibold text-white capitalize mb-1">
                {ext.name.replace(/_/g, ' ')}
              </h3>
              <p className="text-xs text-slate-400 mb-1">{ext.description}</p>
              <p className="text-xs text-slate-600 mb-4">v{ext.version} · {ext.author}</p>

              <div className="flex gap-2">
                {ext.active && (
                  <Link
                    href={`/extensions/${ext.name}`}
                    className="flex-1 py-2 rounded-lg text-sm font-medium text-center bg-indigo-600 text-white hover:bg-indigo-700 transition"
                  >
                    Open
                  </Link>
                )}
                <button
                  onClick={() => toggle(ext.name, ext.active)}
                  className={`${ext.active ? 'px-3' : 'w-full'} py-2 rounded-lg text-sm font-medium transition ${
                    ext.active
                      ? 'bg-slate-700 text-slate-400 hover:bg-slate-600 hover:text-white'
                      : 'bg-indigo-600 text-white hover:bg-indigo-700'
                  }`}
                >
                  {ext.active ? 'Deactivate' : 'Activate'}
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
