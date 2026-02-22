'use client'

import { useEffect, useState, useCallback } from 'react'

interface Todo {
  id: string
  title: string
  description?: string
  priority: 'low' | 'medium' | 'high'
  is_completed: boolean
  due_date?: string
  created_at: string
}

const PRIORITY_COLORS = {
  low: 'bg-slate-700 text-slate-300',
  medium: 'bg-amber-500/20 text-amber-400',
  high: 'bg-red-500/20 text-red-400',
}

const PRIORITY_DOT = {
  low: 'bg-slate-500',
  medium: 'bg-amber-400',
  high: 'bg-red-400',
}

function api(path: string, opts?: RequestInit) {
  const token = typeof window !== 'undefined' ? localStorage.getItem('token') : ''
  return fetch(`/api/v1/todo-list${path}`, {
    ...opts,
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
      ...opts?.headers,
    },
  })
}

export default function TodoListPage() {
  const [todos, setTodos] = useState<Todo[]>([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState<'all' | 'active' | 'done'>('all')
  const [priority, setPriority] = useState<'all' | 'low' | 'medium' | 'high'>('all')
  const [showForm, setShowForm] = useState(false)
  const [editingId, setEditingId] = useState<string | null>(null)
  const [form, setForm] = useState({ title: '', description: '', priority: 'medium', due_date: '' })
  const [saving, setSaving] = useState(false)

  const load = useCallback(async () => {
    setLoading(true)
    const params = new URLSearchParams()
    if (filter === 'active') params.set('is_completed', 'false')
    if (filter === 'done') params.set('is_completed', 'true')
    if (priority !== 'all') params.set('priority', priority)
    const r = await api(`/todos?${params}`)
    if (r.ok) setTodos(await r.json())
    setLoading(false)
  }, [filter, priority])

  useEffect(() => { load() }, [load])

  const resetForm = () => {
    setForm({ title: '', description: '', priority: 'medium', due_date: '' })
    setEditingId(null)
    setShowForm(false)
  }

  const openEdit = (todo: Todo) => {
    setForm({
      title: todo.title,
      description: todo.description || '',
      priority: todo.priority,
      due_date: todo.due_date ? todo.due_date.split('T')[0] : '',
    })
    setEditingId(todo.id)
    setShowForm(true)
  }

  const submit = async () => {
    if (!form.title.trim()) return
    setSaving(true)
    const body: Record<string, unknown> = {
      title: form.title,
      priority: form.priority,
    }
    if (form.description) body.description = form.description
    if (form.due_date) body.due_date = new Date(form.due_date).toISOString()

    if (editingId) {
      const r = await api(`/todos/${editingId}`, { method: 'PATCH', body: JSON.stringify(body) })
      if (r.ok) { resetForm(); load() }
    } else {
      const r = await api('/todos', { method: 'POST', body: JSON.stringify(body) })
      if (r.ok) { resetForm(); load() }
    }
    setSaving(false)
  }

  const toggle = async (id: string) => {
    const r = await api(`/todos/${id}/toggle`, { method: 'POST' })
    if (r.ok) setTodos(prev => prev.map(t => t.id === id ? { ...t, is_completed: !t.is_completed } : t))
  }

  const remove = async (id: string) => {
    const r = await api(`/todos/${id}`, { method: 'DELETE' })
    if (r.ok) setTodos(prev => prev.filter(t => t.id !== id))
  }

  const counts = {
    all: todos.length,
    active: todos.filter(t => !t.is_completed).length,
    done: todos.filter(t => t.is_completed).length,
  }

  return (
    <div className="flex flex-col h-full bg-slate-950">
      {/* Header */}
      <div className="px-8 py-5 border-b border-slate-800 flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-white">Todo List</h1>
          <p className="text-xs text-slate-500 mt-0.5">{counts.active} remaining · {counts.done} done</p>
        </div>
        <button
          onClick={() => { resetForm(); setShowForm(true) }}
          className="flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-medium rounded-lg transition"
        >
          <span className="text-lg leading-none">+</span> New Todo
        </button>
      </div>

      {/* Filters */}
      <div className="px-8 py-3 border-b border-slate-800 flex items-center gap-6">
        {/* Status tabs */}
        <div className="flex gap-1 bg-slate-900 rounded-lg p-1">
          {(['all', 'active', 'done'] as const).map(f => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`px-3 py-1 rounded-md text-xs font-medium transition capitalize ${
                filter === f ? 'bg-slate-700 text-white' : 'text-slate-500 hover:text-white'
              }`}
            >
              {f} {f !== 'all' && <span className="ml-1 opacity-60">{counts[f]}</span>}
            </button>
          ))}
        </div>

        {/* Priority filter */}
        <div className="flex gap-1">
          {(['all', 'high', 'medium', 'low'] as const).map(p => (
            <button
              key={p}
              onClick={() => setPriority(p)}
              className={`px-2.5 py-1 rounded-md text-xs font-medium transition capitalize ${
                priority === p ? 'bg-slate-700 text-white' : 'text-slate-600 hover:text-slate-300'
              }`}
            >
              {p !== 'all' && <span className={`inline-block w-1.5 h-1.5 rounded-full mr-1.5 ${PRIORITY_DOT[p]}`} />}
              {p}
            </button>
          ))}
        </div>
      </div>

      {/* Add / Edit form */}
      {showForm && (
        <div className="px-8 py-4 border-b border-slate-800 bg-slate-900/50">
          <div className="flex flex-col gap-3 max-w-2xl">
            <input
              autoFocus
              value={form.title}
              onChange={e => setForm(f => ({ ...f, title: e.target.value }))}
              onKeyDown={e => e.key === 'Enter' && !e.shiftKey && submit()}
              placeholder="What needs to be done?"
              className="bg-slate-800 border border-slate-700 rounded-lg px-4 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500"
            />
            <textarea
              value={form.description}
              onChange={e => setForm(f => ({ ...f, description: e.target.value }))}
              placeholder="Description (optional)"
              rows={2}
              className="bg-slate-800 border border-slate-700 rounded-lg px-4 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 resize-none"
            />
            <div className="flex gap-3 items-center">
              <select
                value={form.priority}
                onChange={e => setForm(f => ({ ...f, priority: e.target.value }))}
                className="bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500"
              >
                <option value="low">Low priority</option>
                <option value="medium">Medium priority</option>
                <option value="high">High priority</option>
              </select>
              <input
                type="date"
                value={form.due_date}
                onChange={e => setForm(f => ({ ...f, due_date: e.target.value }))}
                className="bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500"
              />
              <div className="flex gap-2 ml-auto">
                <button onClick={resetForm} className="px-4 py-2 text-sm text-slate-400 hover:text-white transition">Cancel</button>
                <button
                  onClick={submit}
                  disabled={!form.title.trim() || saving}
                  className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-medium rounded-lg transition disabled:opacity-40"
                >
                  {saving ? 'Saving…' : editingId ? 'Save changes' : 'Add todo'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Todo list */}
      <div className="flex-1 overflow-y-auto px-8 py-4">
        {loading ? (
          <div className="flex items-center justify-center h-32 text-slate-500 text-sm">Loading...</div>
        ) : todos.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-48 text-center">
            <div className="text-4xl mb-3">✓</div>
            <p className="text-slate-400 text-sm">
              {filter === 'done' ? 'No completed todos yet.' : filter === 'active' ? 'No active todos.' : 'No todos yet — add one above!'}
            </p>
          </div>
        ) : (
          <div className="space-y-2 max-w-3xl">
            {todos.map(todo => (
              <div
                key={todo.id}
                className={`group flex items-start gap-3 p-4 rounded-xl border transition ${
                  todo.is_completed
                    ? 'bg-slate-900/40 border-slate-800/50 opacity-60'
                    : 'bg-slate-900 border-slate-800 hover:border-slate-700'
                }`}
              >
                {/* Checkbox */}
                <button
                  onClick={() => toggle(todo.id)}
                  className={`mt-0.5 w-5 h-5 rounded-full border-2 flex items-center justify-center flex-shrink-0 transition ${
                    todo.is_completed
                      ? 'bg-indigo-600 border-indigo-600'
                      : 'border-slate-600 hover:border-indigo-500'
                  }`}
                >
                  {todo.is_completed && (
                    <svg className="w-3 h-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                    </svg>
                  )}
                </button>

                {/* Content */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className={`text-sm font-medium ${todo.is_completed ? 'line-through text-slate-500' : 'text-white'}`}>
                      {todo.title}
                    </span>
                    <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${PRIORITY_COLORS[todo.priority]}`}>
                      {todo.priority}
                    </span>
                    {todo.due_date && (
                      <span className={`text-xs flex items-center gap-1 ${
                        !todo.is_completed && new Date(todo.due_date) < new Date()
                          ? 'text-red-400'
                          : 'text-slate-500'
                      }`}>
                        📅 {new Date(todo.due_date).toLocaleDateString()}
                      </span>
                    )}
                  </div>
                  {todo.description && (
                    <p className="text-xs text-slate-500 mt-1 truncate">{todo.description}</p>
                  )}
                </div>

                {/* Actions — show on hover */}
                <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition flex-shrink-0">
                  <button
                    onClick={() => openEdit(todo)}
                    className="p-1.5 text-slate-500 hover:text-white rounded-lg hover:bg-slate-700 transition"
                    title="Edit"
                  >
                    <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.232 5.232l3.536 3.536M9 11l6.586-6.586a2 2 0 012.828 2.828L11.828 13.828a2 2 0 01-1.414.586H8v-2.414a2 2 0 01.586-1.414z" />
                    </svg>
                  </button>
                  <button
                    onClick={() => remove(todo.id)}
                    className="p-1.5 text-slate-500 hover:text-red-400 rounded-lg hover:bg-red-500/10 transition"
                    title="Delete"
                  >
                    <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
