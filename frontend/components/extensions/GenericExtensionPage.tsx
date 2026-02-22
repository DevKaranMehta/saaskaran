'use client'

/**
 * GenericExtensionPage
 * Reads ui_spec.json from the backend and renders a full CRUD UI.
 * No frontend rebuild needed when AI generates a new extension.
 */

import { useEffect, useState, useCallback } from 'react'

// ── Spec types ────────────────────────────────────────────────────────────

export interface FieldSpec {
  key: string
  label: string
  type: 'text' | 'textarea' | 'email' | 'number' | 'select' | 'date' | 'boolean' | 'tags'
  required?: boolean
  options?: string[]         // for type=select
  show_in_list?: boolean     // default true
  placeholder?: string
}

export interface ResourceSpec {
  key: string                // e.g. "todos"
  label: string              // e.g. "Todos"
  list?: string              // e.g. "GET /todos"
  create?: string            // e.g. "POST /todos"
  update?: string            // e.g. "PATCH /todos/{id}"
  delete?: string            // e.g. "DELETE /todos/{id}"
  id_field?: string          // default "id"
  fields: FieldSpec[]
  empty_message?: string
}

export interface UiSpec {
  label: string
  icon?: string
  color?: string
  api_base: string           // e.g. "/api/v1/my-extension"
  description?: string
  resources: ResourceSpec[]
}

// ── Helpers ───────────────────────────────────────────────────────────────

function authFetch(url: string, opts: RequestInit = {}) {
  const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null
  return fetch(url, {
    ...opts,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(opts.headers ?? {}),
    },
  })
}

function buildUrl(apiBase: string, endpoint: string, id?: string) {
  // endpoint example: "GET /todos/{id}" → extract path part
  const path = endpoint.replace(/^(GET|POST|PATCH|PUT|DELETE)\s+/, '')
  const resolved = id ? path.replace(/\{[^}]+\}/, id) : path
  return `/api/v1${apiBase.replace(/^\/api\/v1/, '')}${resolved}`
}

function getMethod(endpoint: string) {
  const m = endpoint.match(/^(GET|POST|PATCH|PUT|DELETE)/)
  return m ? m[1] : 'GET'
}

// ── Field renderer (list cell) ────────────────────────────────────────────

function CellValue({ field, value }: { field: FieldSpec; value: unknown }) {
  if (value === null || value === undefined || value === '') return <span className="text-slate-600">—</span>
  if (field.type === 'boolean') return <span className={value ? 'text-green-400' : 'text-slate-500'}>{value ? 'Yes' : 'No'}</span>
  if (field.type === 'select') {
    const colors: Record<string, string> = {
      active: 'text-green-400 bg-green-900/30',
      inactive: 'text-slate-400 bg-slate-800',
      done: 'text-green-400 bg-green-900/30',
      completed: 'text-green-400 bg-green-900/30',
      high: 'text-red-400 bg-red-900/30',
      urgent: 'text-red-400 bg-red-900/30',
      medium: 'text-amber-400 bg-amber-900/30',
      low: 'text-slate-400 bg-slate-800',
      pending: 'text-blue-400 bg-blue-900/30',
      in_progress: 'text-amber-400 bg-amber-900/30',
    }
    const str = String(value)
    const cls = colors[str] ?? 'text-indigo-400 bg-indigo-900/30'
    return <span className={`text-xs px-2 py-0.5 rounded font-medium ${cls}`}>{str.replace(/_/g, ' ')}</span>
  }
  if (field.type === 'tags') {
    const tags = Array.isArray(value) ? value : String(value).split(',').map(t => t.trim()).filter(Boolean)
    return (
      <div className="flex gap-1 flex-wrap">
        {tags.map((t, i) => <span key={i} className="text-xs px-1.5 py-0.5 bg-slate-700 text-slate-400 rounded">{t}</span>)}
      </div>
    )
  }
  if (field.type === 'date' && value) {
    try { return <span>{new Date(String(value)).toLocaleDateString()}</span> } catch { /* fallthrough */ }
  }
  const str = String(value)
  return <span title={str}>{str.length > 40 ? str.slice(0, 40) + '…' : str}</span>
}

// ── Form field renderer ───────────────────────────────────────────────────

function FormField({ field, value, onChange }: { field: FieldSpec; value: unknown; onChange: (v: unknown) => void }) {
  const base = 'w-full bg-slate-900 border border-slate-600 rounded-lg px-3 py-2 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500'

  if (field.type === 'boolean') {
    return (
      <label className="flex items-center gap-2 cursor-pointer">
        <input type="checkbox" checked={Boolean(value)} onChange={e => onChange(e.target.checked)}
          className="w-4 h-4 rounded text-indigo-600 bg-slate-900 border-slate-600" />
        <span className="text-sm text-slate-300">{field.label}</span>
      </label>
    )
  }
  if (field.type === 'select') {
    return (
      <select value={String(value ?? '')} onChange={e => onChange(e.target.value)} className={base + ' cursor-pointer'}>
        {!field.required && <option value="">— select —</option>}
        {(field.options ?? []).map(opt => <option key={opt} value={opt}>{opt.replace(/_/g, ' ')}</option>)}
      </select>
    )
  }
  if (field.type === 'textarea') {
    return (
      <textarea value={String(value ?? '')} onChange={e => onChange(e.target.value)}
        placeholder={field.placeholder ?? field.label} rows={3}
        className={base + ' resize-none'} />
    )
  }
  if (field.type === 'tags') {
    const val = Array.isArray(value) ? value.join(', ') : String(value ?? '')
    return (
      <input type="text" value={val}
        onChange={e => onChange(e.target.value.split(',').map(t => t.trim()).filter(Boolean))}
        placeholder={field.placeholder ?? 'tag1, tag2, tag3'}
        className={base} />
    )
  }
  const inputType = field.type === 'email' ? 'email' : field.type === 'number' ? 'number' : field.type === 'date' ? 'datetime-local' : 'text'
  return (
    <input type={inputType} value={String(value ?? '')} onChange={e => onChange(e.target.value)}
      placeholder={field.placeholder ?? field.label} className={base} />
  )
}

// ── Resource CRUD view ────────────────────────────────────────────────────

function ResourceView({ spec, resource }: { spec: UiSpec; resource: ResourceSpec }) {
  const idField = resource.id_field ?? 'id'
  const listFields = resource.fields.filter(f => f.show_in_list !== false)

  const [items, setItems] = useState<Record<string, unknown>[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [showForm, setShowForm] = useState(false)
  const [editItem, setEditItem] = useState<Record<string, unknown> | null>(null)
  const [formData, setFormData] = useState<Record<string, unknown>>({})
  const [saving, setSaving] = useState(false)

  const fetchItems = useCallback(async () => {
    if (!resource.list) { setLoading(false); return }
    setLoading(true)
    setError('')
    try {
      const url = buildUrl(spec.api_base, resource.list)
      const r = await authFetch(url)
      if (!r.ok) throw new Error(`${r.status} ${r.statusText}`)
      const data = await r.json()
      setItems(Array.isArray(data) ? data : data[resource.key] ?? data.items ?? data.data ?? [])
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load')
    } finally {
      setLoading(false)
    }
  }, [spec.api_base, resource])

  useEffect(() => { fetchItems() }, [fetchItems])

  const openCreate = () => {
    const defaults: Record<string, unknown> = {}
    resource.fields.forEach(f => {
      if (f.type === 'boolean') defaults[f.key] = false
      else if (f.type === 'tags') defaults[f.key] = []
      else if (f.type === 'select' && f.options?.length) defaults[f.key] = f.options[0]
      else defaults[f.key] = ''
    })
    setFormData(defaults)
    setEditItem(null)
    setShowForm(true)
  }

  const openEdit = (item: Record<string, unknown>) => {
    setFormData({ ...item })
    setEditItem(item)
    setShowForm(true)
  }

  const saveItem = async () => {
    setSaving(true)
    try {
      let url: string
      let method: string
      if (editItem && resource.update) {
        url = buildUrl(spec.api_base, resource.update, String(editItem[idField]))
        method = getMethod(resource.update)
      } else if (resource.create) {
        url = buildUrl(spec.api_base, resource.create)
        method = getMethod(resource.create)
      } else {
        return
      }
      const r = await authFetch(url, { method, body: JSON.stringify(formData) })
      if (!r.ok) {
        const err = await r.json().catch(() => ({}))
        throw new Error(err.detail ?? `${r.status}`)
      }
      setShowForm(false)
      fetchItems()
    } catch (e) {
      alert(e instanceof Error ? e.message : 'Save failed')
    } finally {
      setSaving(false)
    }
  }

  const deleteItem = async (item: Record<string, unknown>) => {
    if (!resource.delete || !confirm('Delete this item?')) return
    const url = buildUrl(spec.api_base, resource.delete, String(item[idField]))
    const method = getMethod(resource.delete)
    const r = await authFetch(url, { method })
    if (r.ok || r.status === 204) {
      setItems(prev => prev.filter(i => i[idField] !== item[idField]))
    } else {
      alert('Delete failed')
    }
  }

  return (
    <div className="h-full flex flex-col">
      {/* Toolbar */}
      <div className="flex items-center justify-between mb-4 flex-shrink-0">
        <div>
          <h2 className="font-semibold text-white">{resource.label}</h2>
          {!loading && <p className="text-xs text-slate-500">{items.length} item{items.length !== 1 ? 's' : ''}</p>}
        </div>
        <div className="flex gap-2">
          <button onClick={fetchItems} className="text-xs px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-400 rounded-lg transition">↺ Refresh</button>
          {resource.create && (
            <button onClick={openCreate} className="text-sm px-4 py-1.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg transition font-medium">
              + New {resource.label.replace(/s$/, '')}
            </button>
          )}
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="mb-4 p-3 bg-red-900/30 border border-red-800 rounded-lg text-sm text-red-400">
          ⚠ {error}
        </div>
      )}

      {/* Table */}
      {loading ? (
        <div className="text-slate-500 text-sm">Loading…</div>
      ) : items.length === 0 ? (
        <div className="flex-1 flex flex-col items-center justify-center text-center py-16">
          <div className="text-4xl mb-3">{spec.icon ?? '📦'}</div>
          <p className="text-slate-400 mb-1">{resource.empty_message ?? `No ${resource.label.toLowerCase()} yet`}</p>
          {resource.create && (
            <button onClick={openCreate} className="mt-3 text-sm px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg transition">
              Create first {resource.label.toLowerCase().replace(/s$/, '')}
            </button>
          )}
        </div>
      ) : (
        <div className="flex-1 overflow-auto rounded-xl border border-slate-800">
          <table className="w-full text-sm">
            <thead className="bg-slate-800/80 sticky top-0">
              <tr>
                {listFields.map(f => (
                  <th key={f.key} className="px-4 py-2.5 text-left text-xs font-semibold text-slate-400 uppercase tracking-wide whitespace-nowrap">
                    {f.label}
                  </th>
                ))}
                {(resource.update || resource.delete) && (
                  <th className="px-4 py-2.5 text-right text-xs font-semibold text-slate-400 uppercase tracking-wide">Actions</th>
                )}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800">
              {items.map((item, i) => (
                <tr key={String(item[idField] ?? i)} className="hover:bg-slate-800/50 transition">
                  {listFields.map(f => (
                    <td key={f.key} className="px-4 py-3 text-slate-300 max-w-xs">
                      <CellValue field={f} value={item[f.key]} />
                    </td>
                  ))}
                  {(resource.update || resource.delete) && (
                    <td className="px-4 py-3 text-right">
                      <div className="flex items-center justify-end gap-2">
                        {resource.update && (
                          <button onClick={() => openEdit(item)}
                            className="text-xs px-2.5 py-1 bg-slate-700 hover:bg-slate-600 text-slate-300 rounded transition">
                            Edit
                          </button>
                        )}
                        {resource.delete && (
                          <button onClick={() => deleteItem(item)}
                            className="text-xs px-2.5 py-1 bg-red-900/30 hover:bg-red-900/60 text-red-400 rounded transition">
                            Delete
                          </button>
                        )}
                      </div>
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Create/Edit modal */}
      {showForm && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4" onClick={() => setShowForm(false)}>
          <div className="bg-slate-800 rounded-xl w-full max-w-lg border border-slate-700 shadow-2xl max-h-[90vh] overflow-y-auto"
            onClick={e => e.stopPropagation()}>
            <div className="p-5">
              <div className="flex items-center justify-between mb-5">
                <h3 className="font-semibold text-white">{editItem ? 'Edit' : 'New'} {resource.label.replace(/s$/, '')}</h3>
                <button onClick={() => setShowForm(false)} className="text-slate-500 hover:text-slate-300 transition">✕</button>
              </div>

              <div className="space-y-4">
                {resource.fields.map(field => (
                  <div key={field.key}>
                    {field.type !== 'boolean' && (
                      <label className="block text-xs font-medium text-slate-400 mb-1.5">
                        {field.label}{field.required && <span className="text-red-500 ml-0.5">*</span>}
                      </label>
                    )}
                    <FormField
                      field={field}
                      value={formData[field.key]}
                      onChange={v => setFormData(prev => ({ ...prev, [field.key]: v }))}
                    />
                  </div>
                ))}
              </div>

              <div className="flex gap-2 mt-6">
                <button
                  onClick={saveItem}
                  disabled={saving || resource.fields.filter(f => f.required).some(f => !formData[f.key])}
                  className="flex-1 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-sm rounded-lg transition disabled:opacity-40"
                >
                  {saving ? 'Saving…' : editItem ? 'Save Changes' : 'Create'}
                </button>
                <button onClick={() => setShowForm(false)}
                  className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-slate-300 text-sm rounded-lg transition">
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

// ── Main export ───────────────────────────────────────────────────────────

export default function GenericExtensionPage({ extensionName }: { extensionName: string }) {
  const [spec, setSpec] = useState<UiSpec | null>(null)
  const [loading, setLoading] = useState(true)
  const [activeResource, setActiveResource] = useState(0)

  useEffect(() => {
    const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null
    fetch(`/api/v1/extensions/${extensionName}/ui-spec`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    })
      .then(r => r.ok ? r.json() : null)
      .then(data => { setSpec(data); setLoading(false) })
      .catch(() => setLoading(false))
  }, [extensionName])

  if (loading) return <div className="p-8 text-slate-500 text-sm">Loading extension…</div>

  if (!spec) return null  // caller shows fallback

  return (
    <div className="flex flex-col h-full">
      {/* Extension header */}
      <div className="flex items-center gap-3 px-5 py-3 border-b border-slate-800 flex-shrink-0">
        {spec.icon && <span className="text-xl">{spec.icon}</span>}
        <div>
          <h1 className="font-semibold text-white">{spec.label}</h1>
          {spec.description && <p className="text-xs text-slate-500">{spec.description}</p>}
        </div>
      </div>

      {/* Resource tabs (if multiple resources) */}
      {spec.resources.length > 1 && (
        <div className="flex gap-1 px-4 pt-3 border-b border-slate-800 flex-shrink-0">
          {spec.resources.map((r, i) => (
            <button
              key={r.key}
              onClick={() => setActiveResource(i)}
              className={`px-4 py-2 text-sm rounded-t-lg transition ${
                activeResource === i
                  ? 'bg-slate-800 text-white font-medium border border-b-0 border-slate-700'
                  : 'text-slate-500 hover:text-slate-300'
              }`}
            >
              {r.label}
            </button>
          ))}
        </div>
      )}

      {/* Resource content */}
      <div className="flex-1 overflow-hidden p-5">
        {spec.resources[activeResource] && (
          <ResourceView spec={spec} resource={spec.resources[activeResource]} />
        )}
      </div>
    </div>
  )
}
