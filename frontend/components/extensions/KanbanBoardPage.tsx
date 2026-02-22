'use client'

import { useEffect, useState, useCallback, useRef } from 'react'

type CardStatus = 'backlog' | 'todo' | 'in_progress' | 'review' | 'done'
type Priority = 'low' | 'medium' | 'high'

interface Card {
  id: string
  board_id: string
  title: string
  description?: string
  status: CardStatus
  priority: Priority
  position: number
  tags: string[]
  due_date?: string
  assigned_to?: string
  created_at: string
  updated_at: string
}

interface Board {
  id: string
  name: string
  description?: string
  created_at: string
  updated_at: string
}

const COLUMNS: { status: CardStatus; label: string; color: string; bg: string }[] = [
  { status: 'backlog',     label: 'Backlog',      color: '#6b7280', bg: '#374151' },
  { status: 'todo',        label: 'To Do',        color: '#3b82f6', bg: '#1e3a5f' },
  { status: 'in_progress', label: 'In Progress',  color: '#f59e0b', bg: '#451a03' },
  { status: 'review',      label: 'Review',       color: '#8b5cf6', bg: '#2e1065' },
  { status: 'done',        label: 'Done',         color: '#10b981', bg: '#022c22' },
]

const PRIORITY_BADGE: Record<Priority, string> = {
  low:    'text-slate-400 bg-slate-700',
  medium: 'text-amber-400 bg-amber-900/40',
  high:   'text-red-400 bg-red-900/40',
}

function apiCall(path: string, opts: RequestInit = {}) {
  const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null
  return fetch(`/api/v1/kanban-board${path}`, {
    ...opts,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(opts.headers ?? {}),
    },
  })
}

// ── Editable card detail modal ─────────────────────────────────────────────

interface CardModalProps {
  card: Card
  onClose: () => void
  onUpdate: (updated: Card) => void
  onDelete: (id: string) => void
}

function CardModal({ card, onClose, onUpdate, onDelete }: CardModalProps) {
  const [title, setTitle]       = useState(card.title)
  const [desc, setDesc]         = useState(card.description ?? '')
  const [priority, setPriority] = useState<Priority>(card.priority)
  const [saving, setSaving]     = useState(false)

  const save = async () => {
    setSaving(true)
    const r = await apiCall(`/cards/${card.id}`, {
      method: 'PATCH',
      body: JSON.stringify({ title, description: desc || null, priority }),
    })
    if (r.ok) {
      const updated: Card = await r.json()
      onUpdate(updated)
      onClose()
    }
    setSaving(false)
  }

  const del = async () => {
    if (!confirm('Delete this card?')) return
    const r = await apiCall(`/cards/${card.id}`, { method: 'DELETE' })
    if (r.ok || r.status === 204) {
      onDelete(card.id)
      onClose()
    }
  }

  return (
    <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4" onClick={onClose}>
      <div className="bg-slate-800 rounded-xl w-full max-w-md border border-slate-700 shadow-2xl" onClick={e => e.stopPropagation()}>
        <div className="p-5">
          <div className="flex items-start justify-between mb-4">
            <h3 className="font-semibold text-white text-sm">Edit Card</h3>
            <button onClick={onClose} className="text-slate-500 hover:text-slate-300 transition">✕</button>
          </div>

          <input
            autoFocus
            value={title}
            onChange={e => setTitle(e.target.value)}
            className="w-full bg-slate-900 border border-slate-600 rounded-lg px-3 py-2 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 mb-3"
            placeholder="Card title"
          />
          <textarea
            value={desc}
            onChange={e => setDesc(e.target.value)}
            rows={3}
            className="w-full bg-slate-900 border border-slate-600 rounded-lg px-3 py-2 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 mb-3 resize-none"
            placeholder="Description (optional)"
          />

          <div className="flex items-center gap-2 mb-4">
            <span className="text-xs text-slate-400">Priority:</span>
            {(['low', 'medium', 'high'] as Priority[]).map(p => (
              <button
                key={p}
                onClick={() => setPriority(p)}
                className={`text-xs px-2.5 py-1 rounded-lg transition ${priority === p ? PRIORITY_BADGE[p] + ' ring-1 ring-current' : 'text-slate-600 hover:text-slate-400 bg-slate-700'}`}
              >
                {p}
              </button>
            ))}
          </div>

          <div className="flex gap-2">
            <button
              onClick={save}
              disabled={saving || !title.trim()}
              className="flex-1 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-sm rounded-lg transition disabled:opacity-40"
            >
              {saving ? 'Saving…' : 'Save'}
            </button>
            <button
              onClick={del}
              className="px-4 py-2 bg-red-900/40 hover:bg-red-900/70 text-red-400 text-sm rounded-lg transition"
            >
              Delete
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

// ── Main component ─────────────────────────────────────────────────────────

export default function KanbanBoardPage() {
  const [boards, setBoards]           = useState<Board[]>([])
  const [selectedBoard, setSelectedBoard] = useState<Board | null>(null)
  const [cards, setCards]             = useState<Card[]>([])
  const [loading, setLoading]         = useState(true)
  const [cardsLoading, setCardsLoading] = useState(false)

  // New board modal
  const [showNewBoard, setShowNewBoard]   = useState(false)
  const [newBoardName, setNewBoardName]   = useState('')
  const [newBoardDesc, setNewBoardDesc]   = useState('')
  const [creatingBoard, setCreatingBoard] = useState(false)

  // Add card state: per-column input
  const [addingIn, setAddingIn]       = useState<CardStatus | null>(null)
  const [newCardTitle, setNewCardTitle] = useState('')
  const [newCardPriority, setNewCardPriority] = useState<Priority>('medium')

  // Drag-and-drop
  const dragCard = useRef<Card | null>(null)

  // Card detail modal
  const [editCard, setEditCard] = useState<Card | null>(null)

  // ── Fetch boards ─────────────────────────────────────────────────────────

  const fetchBoards = useCallback(async () => {
    setLoading(true)
    try {
      const r = await apiCall('/boards')
      if (r.ok) setBoards(await r.json())
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { fetchBoards() }, [fetchBoards])

  // ── Open board ────────────────────────────────────────────────────────────

  const openBoard = async (board: Board) => {
    setSelectedBoard(board)
    setCardsLoading(true)
    try {
      const r = await apiCall(`/boards/${board.id}/cards`)
      if (r.ok) setCards(await r.json())
    } finally {
      setCardsLoading(false)
    }
  }

  // ── Create board ─────────────────────────────────────────────────────────

  const createBoard = async () => {
    if (!newBoardName.trim()) return
    setCreatingBoard(true)
    const r = await apiCall('/boards', {
      method: 'POST',
      body: JSON.stringify({ name: newBoardName, description: newBoardDesc || null }),
    })
    if (r.ok) {
      const board: Board = await r.json()
      setBoards(prev => [...prev, board])
      setShowNewBoard(false)
      setNewBoardName('')
      setNewBoardDesc('')
      openBoard(board)
    }
    setCreatingBoard(false)
  }

  const deleteBoard = async (id: string) => {
    if (!confirm('Delete this board and all its cards?')) return
    const r = await apiCall(`/boards/${id}`, { method: 'DELETE' })
    if (r.ok || r.status === 204) {
      setBoards(prev => prev.filter(b => b.id !== id))
      if (selectedBoard?.id === id) setSelectedBoard(null)
    }
  }

  // ── Create card ───────────────────────────────────────────────────────────

  const createCard = async (status: CardStatus) => {
    if (!selectedBoard || !newCardTitle.trim()) return
    const r = await apiCall(`/boards/${selectedBoard.id}/cards`, {
      method: 'POST',
      body: JSON.stringify({ title: newCardTitle, status, priority: newCardPriority }),
    })
    if (r.ok) {
      const card: Card = await r.json()
      setCards(prev => [...prev, card])
      setAddingIn(null)
      setNewCardTitle('')
      setNewCardPriority('medium')
    }
  }

  // ── Move card (drag-and-drop) ─────────────────────────────────────────────

  const moveCard = async (cardId: string, newStatus: CardStatus) => {
    const original = cards.find(c => c.id === cardId)
    if (!original || original.status === newStatus) return
    // Optimistic update
    setCards(prev => prev.map(c => c.id === cardId ? { ...c, status: newStatus } : c))
    const r = await apiCall(`/cards/${cardId}`, {
      method: 'PATCH',
      body: JSON.stringify({ status: newStatus }),
    })
    if (!r.ok) {
      // Revert on failure
      setCards(prev => prev.map(c => c.id === cardId ? { ...c, status: original.status } : c))
    }
  }

  // ── Update / delete card from modal ──────────────────────────────────────

  const handleCardUpdate = (updated: Card) => {
    setCards(prev => prev.map(c => c.id === updated.id ? updated : c))
  }
  const handleCardDelete = (id: string) => {
    setCards(prev => prev.filter(c => c.id !== id))
  }

  // ── Board list ────────────────────────────────────────────────────────────

  if (!selectedBoard) {
    return (
      <div className="p-6 h-full overflow-y-auto">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-xl font-bold text-white">Kanban Boards</h1>
            <p className="text-sm text-slate-400 mt-0.5">Manage your project boards</p>
          </div>
          <button
            onClick={() => setShowNewBoard(true)}
            className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-medium rounded-lg transition"
          >
            + New Board
          </button>
        </div>

        {loading ? (
          <p className="text-slate-500 text-sm">Loading boards…</p>
        ) : boards.length === 0 ? (
          <div className="text-center py-16">
            <div className="text-5xl mb-3">⬡</div>
            <p className="text-slate-300 font-medium mb-1">No boards yet</p>
            <p className="text-sm text-slate-500 mb-4">Create your first kanban board to get started.</p>
            <button
              onClick={() => setShowNewBoard(true)}
              className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-sm rounded-lg transition"
            >
              Create Board
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {boards.map(b => (
              <div key={b.id} className="group relative bg-slate-800 rounded-xl border border-slate-700 hover:border-indigo-500/50 transition overflow-hidden">
                <button
                  onClick={() => openBoard(b)}
                  className="w-full text-left p-5"
                >
                  <div className="flex items-center gap-2 mb-2">
                    <div className="w-3 h-3 rounded-full bg-indigo-500 flex-shrink-0" />
                    <h3 className="font-semibold text-white group-hover:text-indigo-300 transition">{b.name}</h3>
                  </div>
                  {b.description && <p className="text-xs text-slate-400 truncate">{b.description}</p>}
                  <p className="text-xs text-slate-600 mt-2">{new Date(b.created_at).toLocaleDateString()}</p>
                </button>
                <button
                  onClick={() => deleteBoard(b.id)}
                  className="absolute top-3 right-3 opacity-0 group-hover:opacity-100 text-slate-600 hover:text-red-400 transition text-xs"
                  title="Delete board"
                >
                  ✕
                </button>
              </div>
            ))}
          </div>
        )}

        {/* New board modal */}
        {showNewBoard && (
          <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
            <div className="bg-slate-800 rounded-xl p-6 w-full max-w-sm border border-slate-700">
              <h3 className="font-semibold text-white mb-4">Create New Board</h3>
              <input
                autoFocus
                value={newBoardName}
                onChange={e => setNewBoardName(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && createBoard()}
                placeholder="Board name"
                className="w-full bg-slate-900 border border-slate-600 rounded-lg px-3 py-2 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 mb-3"
              />
              <textarea
                value={newBoardDesc}
                onChange={e => setNewBoardDesc(e.target.value)}
                placeholder="Description (optional)"
                rows={2}
                className="w-full bg-slate-900 border border-slate-600 rounded-lg px-3 py-2 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 mb-4 resize-none"
              />
              <div className="flex gap-2">
                <button
                  onClick={createBoard}
                  disabled={creatingBoard || !newBoardName.trim()}
                  className="flex-1 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-sm rounded-lg transition disabled:opacity-40"
                >
                  {creatingBoard ? 'Creating…' : 'Create'}
                </button>
                <button
                  onClick={() => { setShowNewBoard(false); setNewBoardName(''); setNewBoardDesc('') }}
                  className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-slate-300 text-sm rounded-lg transition"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    )
  }

  // ── Board view (kanban columns) ───────────────────────────────────────────

  const cardsByStatus = (status: CardStatus) =>
    cards.filter(c => c.status === status).sort((a, b) => a.position - b.position || a.created_at.localeCompare(b.created_at))

  return (
    <div className="flex flex-col h-full">
      {/* Board header */}
      <div className="flex items-center gap-3 px-4 py-3 border-b border-slate-800 flex-shrink-0">
        <button onClick={() => { setSelectedBoard(null); setCards([]) }} className="text-slate-400 hover:text-white transition text-sm">
          ← Boards
        </button>
        <span className="text-slate-700">/</span>
        <h2 className="font-semibold text-white">{selectedBoard.name}</h2>
        {cardsLoading && <span className="text-xs text-slate-500 ml-1">Loading…</span>}
        <div className="ml-auto flex items-center gap-2">
          <span className="text-xs text-slate-600">Drag cards to move between columns</span>
          <button
            onClick={() => deleteBoard(selectedBoard.id)}
            className="text-xs px-3 py-1.5 bg-slate-800 hover:bg-red-900/40 text-slate-500 hover:text-red-400 rounded-lg transition"
          >
            Delete board
          </button>
        </div>
      </div>

      {/* Kanban columns */}
      <div className="flex-1 overflow-x-auto p-4">
        <div className="flex gap-3 h-full items-start" style={{ minWidth: 'max-content' }}>
          {COLUMNS.map(col => {
            const colCards = cardsByStatus(col.status)
            return (
              <div
                key={col.status}
                className="w-64 flex-shrink-0 flex flex-col rounded-xl border border-slate-800 bg-slate-900"
                onDragOver={e => e.preventDefault()}
                onDrop={e => {
                  e.preventDefault()
                  if (dragCard.current) moveCard(dragCard.current.id, col.status)
                  dragCard.current = null
                }}
              >
                {/* Column header */}
                <div className="flex items-center gap-2 px-3 py-2.5 rounded-t-xl" style={{ backgroundColor: col.bg + '80', borderBottom: `2px solid ${col.color}` }}>
                  <div className="w-2 h-2 rounded-full flex-shrink-0" style={{ backgroundColor: col.color }} />
                  <span className="text-xs font-semibold text-white tracking-wide uppercase">{col.label}</span>
                  <span className="ml-auto text-xs font-mono" style={{ color: col.color }}>{colCards.length}</span>
                </div>

                {/* Cards */}
                <div className="flex-1 p-2 space-y-2 overflow-y-auto max-h-[calc(100vh-200px)]">
                  {colCards.map(card => (
                    <div
                      key={card.id}
                      draggable
                      onDragStart={() => { dragCard.current = card }}
                      onDragEnd={() => { dragCard.current = null }}
                      onClick={() => setEditCard(card)}
                      className="bg-slate-800 rounded-lg p-3 border border-slate-700 hover:border-slate-500 transition cursor-grab active:cursor-grabbing group select-none"
                    >
                      <p className="text-sm text-white leading-snug mb-2">{card.title}</p>
                      {card.description && (
                        <p className="text-xs text-slate-500 mb-2 line-clamp-2">{card.description}</p>
                      )}
                      <div className="flex items-center gap-1.5 flex-wrap">
                        <span className={`text-xs px-1.5 py-0.5 rounded font-medium ${PRIORITY_BADGE[card.priority]}`}>
                          {card.priority}
                        </span>
                        {card.tags?.map((tag, i) => (
                          <span key={i} className="text-xs px-1.5 py-0.5 rounded bg-slate-700 text-slate-400">{tag}</span>
                        ))}
                        {card.due_date && (
                          <span className="text-xs text-slate-500 ml-auto">
                            {new Date(card.due_date).toLocaleDateString()}
                          </span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>

                {/* Add card */}
                {addingIn === col.status ? (
                  <div className="p-2 border-t border-slate-800">
                    <input
                      autoFocus
                      value={newCardTitle}
                      onChange={e => setNewCardTitle(e.target.value)}
                      onKeyDown={e => {
                        if (e.key === 'Enter') createCard(col.status)
                        if (e.key === 'Escape') { setAddingIn(null); setNewCardTitle('') }
                      }}
                      placeholder="Card title…"
                      className="w-full bg-slate-800 border border-slate-600 rounded-lg px-2.5 py-1.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 mb-2"
                    />
                    <div className="flex gap-1 mb-2">
                      {(['low', 'medium', 'high'] as Priority[]).map(p => (
                        <button
                          key={p}
                          onClick={() => setNewCardPriority(p)}
                          className={`flex-1 text-xs py-0.5 rounded transition ${newCardPriority === p ? PRIORITY_BADGE[p] : 'text-slate-600 hover:text-slate-400 bg-slate-700'}`}
                        >
                          {p}
                        </button>
                      ))}
                    </div>
                    <div className="flex gap-1">
                      <button
                        onClick={() => createCard(col.status)}
                        disabled={!newCardTitle.trim()}
                        className="flex-1 py-1 bg-indigo-600 hover:bg-indigo-700 text-white text-xs rounded-lg transition disabled:opacity-40"
                      >
                        Add
                      </button>
                      <button
                        onClick={() => { setAddingIn(null); setNewCardTitle('') }}
                        className="px-2 py-1 bg-slate-700 text-slate-400 text-xs rounded-lg hover:bg-slate-600 transition"
                      >
                        ✕
                      </button>
                    </div>
                  </div>
                ) : (
                  <button
                    onClick={() => { setAddingIn(col.status); setNewCardTitle('') }}
                    className="mx-2 mb-2 py-1.5 text-xs text-slate-600 hover:text-slate-400 hover:bg-slate-800 rounded-lg transition text-left px-2"
                  >
                    + Add card
                  </button>
                )}
              </div>
            )
          })}
        </div>
      </div>

      {/* Card detail modal */}
      {editCard && (
        <CardModal
          card={editCard}
          onClose={() => setEditCard(null)}
          onUpdate={handleCardUpdate}
          onDelete={handleCardDelete}
        />
      )}
    </div>
  )
}
