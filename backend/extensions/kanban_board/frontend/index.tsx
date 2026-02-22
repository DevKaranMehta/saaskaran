import React, { useState, useEffect, useRef, useCallback } from "react";

// ─── Types ────────────────────────────────────────────────────────────────────
type Priority = "low" | "medium" | "high";
type CardStatus = "backlog" | "todo" | "in_progress" | "review" | "done";

interface Board {
  id: string;
  name: string;
  description: string | null;
  created_at: string;
  updated_at: string;
}

interface KanbanCard {
  id: string;
  board_id: string;
  title: string;
  description: string | null;
  status: CardStatus;
  priority: Priority;
  due_date: string | null;
  position: number;
  tags: string[];
  assigned_to: string | null;
  created_at: string;
  updated_at: string;
}

// ─── Constants ────────────────────────────────────────────────────────────────
const STATUSES: { key: CardStatus; label: string; bg: string; border: string; dot: string }[] = [
  { key: "backlog",     label: "Backlog",      bg: "bg-slate-50",   border: "border-slate-200", dot: "bg-slate-400"  },
  { key: "todo",        label: "To Do",        bg: "bg-blue-50",    border: "border-blue-200",  dot: "bg-blue-500"   },
  { key: "in_progress", label: "In Progress",  bg: "bg-amber-50",   border: "border-amber-200", dot: "bg-amber-500"  },
  { key: "review",      label: "Review",       bg: "bg-purple-50",  border: "border-purple-200",dot: "bg-purple-500" },
  { key: "done",        label: "Done",         bg: "bg-emerald-50", border: "border-emerald-200",dot: "bg-emerald-500"},
];

const PRIORITY_CONFIG: Record<Priority, { label: string; badge: string; icon: string }> = {
  low:    { label: "Low",    badge: "bg-slate-100 text-slate-600",   icon: "🔵" },
  medium: { label: "Medium", badge: "bg-amber-100 text-amber-700",   icon: "🟡" },
  high:   { label: "High",   badge: "bg-red-100 text-red-600 font-semibold", icon: "🔴" },
};

const API = "/api/v1/kanban-board";

// ─── API helper ───────────────────────────────────────────────────────────────
async function api<T = void>(
  path: string,
  options?: RequestInit
): Promise<T> {
  const token =
    localStorage.getItem("access_token") ||
    sessionStorage.getItem("access_token") ||
    "";
  const res = await fetch(`${API}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options?.headers,
    },
    ...options,
  });
  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText);
    throw new Error(text || `HTTP ${res.status}`);
  }
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

// ─── Toast ────────────────────────────────────────────────────────────────────
const Toast: React.FC<{ msg: string; onClose: () => void }> = ({ msg, onClose }) => {
  useEffect(() => {
    const t = setTimeout(onClose, 4000);
    return () => clearTimeout(t);
  }, [onClose]);
  return (
    <div className="fixed bottom-4 right-4 z-50 bg-red-600 text-white px-4 py-2.5 rounded-lg shadow-lg flex items-center gap-3 text-sm max-w-sm">
      <span className="flex-1">{msg}</span>
      <button onClick={onClose} className="text-white/70 hover:text-white font-bold">✕</button>
    </div>
  );
};

// ─── Card Item ────────────────────────────────────────────────────────────────
const CardItem: React.FC<{
  card: KanbanCard;
  onEdit: (card: KanbanCard) => void;
  onDelete: (id: string) => void;
  onDragStart: (card: KanbanCard) => void;
}> = ({ card, onEdit, onDelete, onDragStart }) => {
  const isOverdue =
    card.due_date &&
    new Date(card.due_date) < new Date() &&
    card.status !== "done";
  const p = PRIORITY_CONFIG[card.priority];

  return (
    <div
      draggable
      onDragStart={(e) => {
        e.dataTransfer.effectAllowed = "move";
        onDragStart(card);
      }}
      className="bg-white rounded-xl border border-gray-100 shadow-sm p-3 cursor-grab active:cursor-grabbing hover:shadow-md hover:border-gray-200 transition-all group select-none"
    >
      {/* Header row */}
      <div className="flex items-start gap-1.5">
        <p className="text-sm font-medium text-gray-800 flex-1 leading-snug break-words">{card.title}</p>
        <div className="flex gap-0.5 opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0 mt-0.5">
          <button
            onClick={() => onEdit(card)}
            className="p-1 rounded-md text-gray-400 hover:text-indigo-600 hover:bg-indigo-50 transition-colors"
            title="Edit"
          >
            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
            </svg>
          </button>
          <button
            onClick={() => onDelete(card.id)}
            className="p-1 rounded-md text-gray-400 hover:text-red-600 hover:bg-red-50 transition-colors"
            title="Delete"
          >
            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
          </button>
        </div>
      </div>

      {/* Description */}
      {card.description && (
        <p className="text-xs text-gray-400 mt-1.5 line-clamp-2 leading-relaxed">{card.description}</p>
      )}

      {/* Footer chips */}
      <div className="flex flex-wrap gap-1 mt-2.5">
        <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${p.badge}`}>
          {p.icon} {p.label}
        </span>
        {card.due_date && (
          <span
            className={`text-xs px-2 py-0.5 rounded-full ${
              isOverdue
                ? "bg-red-100 text-red-600 font-semibold"
                : "bg-gray-100 text-gray-500"
            }`}
          >
            📅 {new Date(card.due_date).toLocaleDateString(undefined, { month: "short", day: "numeric" })}
          </span>
        )}
        {card.tags?.slice(0, 3).map((tag) => (
          <span key={tag} className="text-xs px-2 py-0.5 rounded-full bg-indigo-50 text-indigo-600">
            #{tag}
          </span>
        ))}
        {(card.tags?.length || 0) > 3 && (
          <span className="text-xs px-2 py-0.5 rounded-full bg-gray-100 text-gray-500">
            +{card.tags.length - 3}
          </span>
        )}
      </div>
    </div>
  );
};

// ─── Column ───────────────────────────────────────────────────────────────────
const Column: React.FC<{
  col: (typeof STATUSES)[0];
  cards: KanbanCard[];
  onAddCard: (status: CardStatus) => void;
  onEditCard: (card: KanbanCard) => void;
  onDeleteCard: (id: string) => void;
  onDragStart: (card: KanbanCard) => void;
  onDrop: (status: CardStatus) => void;
}> = ({ col, cards, onAddCard, onEditCard, onDeleteCard, onDragStart, onDrop }) => {
  const [over, setOver] = useState(false);

  return (
    <div
      className={`flex flex-col rounded-2xl border-2 ${col.border} ${col.bg} w-64 flex-shrink-0 transition-shadow ${over ? "shadow-lg" : ""}`}
      onDragOver={(e) => { e.preventDefault(); setOver(true); }}
      onDragLeave={() => setOver(false)}
      onDrop={() => { setOver(false); onDrop(col.key); }}
    >
      {/* Column header */}
      <div className="px-3.5 pt-3.5 pb-2.5 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className={`w-2.5 h-2.5 rounded-full ${col.dot} flex-shrink-0`} />
          <span className="text-sm font-semibold text-gray-700">{col.label}</span>
        </div>
        <span className="text-xs bg-white/70 text-gray-500 rounded-full px-2 py-0.5 font-medium border border-white/50">
          {cards.length}
        </span>
      </div>

      {/* Cards list */}
      <div
        className={`flex-1 px-2.5 space-y-2 overflow-y-auto transition-colors rounded-xl ${over ? "bg-white/40" : ""}`}
        style={{ minHeight: 80, maxHeight: 560 }}
      >
        {cards.map((card) => (
          <CardItem
            key={card.id}
            card={card}
            onEdit={onEditCard}
            onDelete={onDeleteCard}
            onDragStart={onDragStart}
          />
        ))}
        {over && cards.length === 0 && (
          <div className="border-2 border-dashed border-gray-300 rounded-xl h-16 flex items-center justify-center">
            <span className="text-xs text-gray-400">Drop here</span>
          </div>
        )}
      </div>

      {/* Add card button */}
      <button
        onClick={() => onAddCard(col.key)}
        className="mx-2.5 my-2.5 flex items-center gap-1.5 text-xs text-gray-500 hover:text-gray-800 hover:bg-white/60 rounded-lg px-3 py-1.5 transition-colors"
      >
        <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4" />
        </svg>
        Add card
      </button>
    </div>
  );
};

// ─── Card Modal ───────────────────────────────────────────────────────────────
const CardModal: React.FC<{
  card?: KanbanCard | null;
  defaultStatus: CardStatus;
  onSave: (data: Partial<KanbanCard>) => Promise<void>;
  onClose: () => void;
}> = ({ card, defaultStatus, onSave, onClose }) => {
  const [title, setTitle]           = useState(card?.title ?? "");
  const [desc, setDesc]             = useState(card?.description ?? "");
  const [priority, setPriority]     = useState<Priority>(card?.priority ?? "medium");
  const [cardStatus, setCardStatus] = useState<CardStatus>(card?.status ?? defaultStatus);
  const [dueDate, setDueDate]       = useState(card?.due_date ? card.due_date.split("T")[0] : "");
  const [tagsStr, setTagsStr]       = useState((card?.tags ?? []).join(", "));
  const [saving, setSaving]         = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) return;
    setSaving(true);
    try {
      await onSave({
        title: title.trim(),
        description: desc.trim() || undefined,
        priority,
        status: cardStatus,
        due_date: dueDate ? new Date(dueDate).toISOString() : undefined,
        tags: tagsStr.split(",").map((t) => t.trim()).filter(Boolean),
      });
    } finally {
      setSaving(false);
    }
  };

  return (
    <div
      className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4"
      onClick={onClose}
    >
      <div
        className="bg-white rounded-2xl shadow-2xl w-full max-w-lg overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
          <h2 className="text-base font-semibold text-gray-900">
            {card ? "✏️ Edit Card" : "➕ New Card"}
          </h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-xl leading-none">✕</button>
        </div>

        <form onSubmit={handleSubmit} className="px-6 py-5 space-y-4">
          {/* Title */}
          <div>
            <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1.5">
              Title <span className="text-red-500">*</span>
            </label>
            <input
              autoFocus
              className="w-full border border-gray-200 rounded-xl px-3.5 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent placeholder-gray-300"
              placeholder="What needs to be done?"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
            />
          </div>

          {/* Description */}
          <div>
            <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1.5">Description</label>
            <textarea
              className="w-full border border-gray-200 rounded-xl px-3.5 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 resize-none placeholder-gray-300"
              rows={3}
              placeholder="Add more details..."
              value={desc}
              onChange={(e) => setDesc(e.target.value)}
            />
          </div>

          {/* Status + Priority */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1.5">Status</label>
              <select
                className="w-full border border-gray-200 rounded-xl px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 bg-white"
                value={cardStatus}
                onChange={(e) => setCardStatus(e.target.value as CardStatus)}
              >
                {STATUSES.map((s) => (
                  <option key={s.key} value={s.key}>{s.label}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1.5">Priority</label>
              <select
                className="w-full border border-gray-200 rounded-xl px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 bg-white"
                value={priority}
                onChange={(e) => setPriority(e.target.value as Priority)}
              >
                <option value="low">🔵 Low</option>
                <option value="medium">🟡 Medium</option>
                <option value="high">🔴 High</option>
              </select>
            </div>
          </div>

          {/* Due Date */}
          <div>
            <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1.5">Due Date</label>
            <input
              type="date"
              className="w-full border border-gray-200 rounded-xl px-3.5 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              value={dueDate}
              onChange={(e) => setDueDate(e.target.value)}
            />
          </div>

          {/* Tags */}
          <div>
            <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1.5">
              Tags <span className="font-normal text-gray-400">(comma-separated)</span>
            </label>
            <input
              className="w-full border border-gray-200 rounded-xl px-3.5 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 placeholder-gray-300"
              placeholder="design, bug, frontend"
              value={tagsStr}
              onChange={(e) => setTagsStr(e.target.value)}
            />
          </div>

          {/* Actions */}
          <div className="flex gap-2.5 pt-1">
            <button
              type="submit"
              disabled={saving || !title.trim()}
              className="flex-1 bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-300 text-white rounded-xl py-2.5 text-sm font-semibold transition-colors"
            >
              {saving ? "Saving..." : card ? "Save Changes" : "Create Card"}
            </button>
            <button
              type="button"
              onClick={onClose}
              className="px-5 border border-gray-200 rounded-xl py-2.5 text-sm text-gray-600 hover:bg-gray-50 transition-colors"
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

// ─── Board Modal ──────────────────────────────────────────────────────────────
const BoardModal: React.FC<{
  board?: Board | null;
  onSave: (data: { name: string; description: string }) => Promise<void>;
  onClose: () => void;
}> = ({ board, onSave, onClose }) => {
  const [name, setName]   = useState(board?.name ?? "");
  const [desc, setDesc]   = useState(board?.description ?? "");
  const [saving, setSaving] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;
    setSaving(true);
    try {
      await onSave({ name: name.trim(), description: desc.trim() });
    } finally {
      setSaving(false);
    }
  };

  return (
    <div
      className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4"
      onClick={onClose}
    >
      <div
        className="bg-white rounded-2xl shadow-2xl w-full max-w-sm overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
          <h2 className="text-base font-semibold text-gray-900">
            {board ? "✏️ Edit Board" : "🗂️ New Board"}
          </h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-xl leading-none">✕</button>
        </div>
        <form onSubmit={handleSubmit} className="px-6 py-5 space-y-4">
          <div>
            <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1.5">
              Board Name <span className="text-red-500">*</span>
            </label>
            <input
              autoFocus
              className="w-full border border-gray-200 rounded-xl px-3.5 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 placeholder-gray-300"
              placeholder="e.g. Product Roadmap"
              value={name}
              onChange={(e) => setName(e.target.value)}
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1.5">Description</label>
            <textarea
              className="w-full border border-gray-200 rounded-xl px-3.5 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 resize-none placeholder-gray-300"
              rows={2}
              placeholder="What's this board for?"
              value={desc}
              onChange={(e) => setDesc(e.target.value)}
            />
          </div>
          <div className="flex gap-2.5 pt-1">
            <button
              type="submit"
              disabled={saving || !name.trim()}
              className="flex-1 bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-300 text-white rounded-xl py-2.5 text-sm font-semibold transition-colors"
            >
              {saving ? "Saving..." : board ? "Save Changes" : "Create Board"}
            </button>
            <button
              type="button"
              onClick={onClose}
              className="px-5 border border-gray-200 rounded-xl py-2.5 text-sm text-gray-600 hover:bg-gray-50 transition-colors"
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

// ─── Main Page ────────────────────────────────────────────────────────────────
export default function KanbanBoardPage() {
  const [boards, setBoards]           = useState<Board[]>([]);
  const [activeBoard, setActiveBoard] = useState<Board | null>(null);
  const [cards, setCards]             = useState<KanbanCard[]>([]);
  const [loading, setLoading]         = useState(true);
  const [error, setError]             = useState<string | null>(null);

  // Modals
  const [showBoardModal, setShowBoardModal] = useState(false);
  const [editingBoard, setEditingBoard]     = useState<Board | null>(null);
  const [showCardModal, setShowCardModal]   = useState(false);
  const [editingCard, setEditingCard]       = useState<KanbanCard | null>(null);
  const [newCardStatus, setNewCardStatus]   = useState<CardStatus>("todo");

  // Drag & drop
  const dragCard = useRef<KanbanCard | null>(null);

  // ── Load boards ──────────────────────────────────────────────────────────
  const loadBoards = useCallback(async () => {
    try {
      const data = await api<Board[]>("/boards");
      setBoards(data);
      if (data.length > 0) setActiveBoard((prev) => prev ?? data[0]);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, []);

  // ── Load cards ───────────────────────────────────────────────────────────
  const loadCards = useCallback(async (boardId: string) => {
    try {
      const data = await api<KanbanCard[]>(`/boards/${boardId}/cards`);
      setCards(data);
    } catch (e: any) {
      setError(e.message);
    }
  }, []);

  useEffect(() => { loadBoards(); }, [loadBoards]);
  useEffect(() => { if (activeBoard) loadCards(activeBoard.id); }, [activeBoard, loadCards]);

  // ── Board CRUD ───────────────────────────────────────────────────────────
  const handleSaveBoard = async (data: { name: string; description: string }) => {
    if (editingBoard) {
      const updated = await api<Board>(`/boards/${editingBoard.id}`, {
        method: "PATCH", body: JSON.stringify(data),
      });
      setBoards((b) => b.map((x) => (x.id === updated.id ? updated : x)));
      if (activeBoard?.id === updated.id) setActiveBoard(updated);
    } else {
      const created = await api<Board>("/boards", {
        method: "POST", body: JSON.stringify(data),
      });
      setBoards((b) => [...b, created]);
      setActiveBoard(created);
      setCards([]);
    }
    setShowBoardModal(false);
    setEditingBoard(null);
  };

  const handleDeleteBoard = async (id: string) => {
    if (!window.confirm("Delete this board and all its cards? This cannot be undone.")) return;
    try {
      await api(`/boards/${id}`, { method: "DELETE" });
      const remaining = boards.filter((b) => b.id !== id);
      setBoards(remaining);
      const next = remaining[0] ?? null;
      setActiveBoard(next);
      if (next) loadCards(next.id); else setCards([]);
    } catch (e: any) { setError(e.message); }
  };

  // ── Card CRUD ────────────────────────────────────────────────────────────
  const handleSaveCard = async (data: Partial<KanbanCard>) => {
    if (!activeBoard) return;
    if (editingCard) {
      const updated = await api<KanbanCard>(`/cards/${editingCard.id}`, {
        method: "PATCH", body: JSON.stringify(data),
      });
      setCards((c) => c.map((x) => (x.id === updated.id ? updated : x)));
    } else {
      const created = await api<KanbanCard>(`/boards/${activeBoard.id}/cards`, {
        method: "POST", body: JSON.stringify({ ...data, status: newCardStatus }),
      });
      setCards((c) => [...c, created]);
    }
    setShowCardModal(false);
    setEditingCard(null);
  };

  const handleDeleteCard = async (id: string) => {
    try {
      await api(`/cards/${id}`, { method: "DELETE" });
      setCards((c) => c.filter((x) => x.id !== id));
    } catch (e: any) { setError(e.message); }
  };

  // ── Drag & Drop ──────────────────────────────────────────────────────────
  const handleDrop = async (targetStatus: CardStatus) => {
    const card = dragCard.current;
    dragCard.current = null;
    if (!card || card.status === targetStatus) return;
    // Optimistic update
    setCards((c) =>
      c.map((x) => (x.id === card.id ? { ...x, status: targetStatus } : x))
    );
    try {
      await api(`/cards/${card.id}`, {
        method: "PATCH", body: JSON.stringify({ status: targetStatus }),
      });
    } catch (e: any) {
      // Revert on failure
      setCards((c) =>
        c.map((x) => (x.id === card.id ? { ...x, status: card.status } : x))
      );
      setError(e.message);
    }
  };

  // ── Stats ────────────────────────────────────────────────────────────────
  const totalCards = cards.length;
  const doneCards  = cards.filter((c) => c.status === "done").length;
  const highCards  = cards.filter((c) => c.priority === "high" && c.status !== "done").length;
  const overdueCards = cards.filter(
    (c) => c.due_date && new Date(c.due_date) < new Date() && c.status !== "done"
  ).length;

  // ── Render ───────────────────────────────────────────────────────────────
  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="w-8 h-8 border-4 border-indigo-600 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
          <p className="text-gray-400 text-sm">Loading boards...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-screen bg-gray-50 overflow-hidden">
      {/* Error toast */}
      {error && <Toast msg={error} onClose={() => setError(null)} />}

      {/* ── Top bar ── */}
      <div className="bg-white border-b border-gray-200 px-4 py-3 flex-shrink-0">
        <div className="flex items-center gap-3">
          {/* Logo + title */}
          <div className="flex items-center gap-2 flex-shrink-0">
            <div className="w-8 h-8 bg-indigo-600 rounded-lg flex items-center justify-center text-white text-sm font-bold">K</div>
            <h1 className="text-base font-bold text-gray-900 hidden sm:block">Kanban Board</h1>
          </div>

          {/* Board tabs */}
          <div className="flex items-center gap-1 flex-1 overflow-x-auto min-w-0">
            {boards.map((board) => {
              const isActive = activeBoard?.id === board.id;
              return (
                <div key={board.id} className="flex items-center gap-0.5 flex-shrink-0">
                  <button
                    onClick={() => setActiveBoard(board)}
                    className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors whitespace-nowrap ${
                      isActive
                        ? "bg-indigo-50 text-indigo-700 ring-1 ring-indigo-200"
                        : "text-gray-500 hover:bg-gray-100 hover:text-gray-800"
                    }`}
                  >
                    {board.name}
                  </button>
                  {isActive && (
                    <div className="flex gap-0.5">
                      <button
                        onClick={() => { setEditingBoard(board); setShowBoardModal(true); }}
                        className="p-1.5 rounded-lg text-gray-400 hover:text-indigo-600 hover:bg-indigo-50 transition-colors"
                        title="Edit board"
                      >
                        <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                          <path strokeLinecap="round" strokeLinejoin="round" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                        </svg>
                      </button>
                      <button
                        onClick={() => handleDeleteBoard(board.id)}
                        className="p-1.5 rounded-lg text-gray-400 hover:text-red-600 hover:bg-red-50 transition-colors"
                        title="Delete board"
                      >
                        <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                          <path strokeLinecap="round" strokeLinejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                        </svg>
                      </button>
                    </div>
                  )}
                </div>
              );
            })}
          </div>

          {/* New Board */}
          <button
            onClick={() => { setEditingBoard(null); setShowBoardModal(true); }}
            className="flex items-center gap-1.5 bg-indigo-600 hover:bg-indigo-700 text-white px-3.5 py-1.5 rounded-lg text-sm font-medium transition-colors flex-shrink-0"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4" />
            </svg>
            <span className="hidden sm:inline">New Board</span>
          </button>
        </div>
      </div>

      {/* ── Stats bar (only when board selected) ── */}
      {activeBoard && totalCards > 0 && (
        <div className="bg-white border-b border-gray-100 px-4 py-2 flex-shrink-0">
          <div className="flex items-center gap-6 text-xs text-gray-500">
            <span>📋 <strong className="text-gray-800">{totalCards}</strong> total</span>
            <span>✅ <strong className="text-emerald-600">{doneCards}</strong> done</span>
            {highCards > 0 && <span>🔴 <strong className="text-red-600">{highCards}</strong> high priority</span>}
            {overdueCards > 0 && <span>⚠️ <strong className="text-orange-600">{overdueCards}</strong> overdue</span>}
            {totalCards > 0 && (
              <div className="flex items-center gap-1.5">
                <div className="h-1.5 w-24 bg-gray-100 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-emerald-500 rounded-full transition-all"
                    style={{ width: `${Math.round((doneCards / totalCards) * 100)}%` }}
                  />
                </div>
                <span>{Math.round((doneCards / totalCards) * 100)}%</span>
              </div>
            )}
          </div>
        </div>
      )}

      {/* ── Board content ── */}
      {!activeBoard ? (
        <div className="flex-1 flex flex-col items-center justify-center text-center p-8">
          <div className="w-20 h-20 bg-indigo-50 rounded-2xl flex items-center justify-center mb-5 text-4xl">🗂️</div>
          <h2 className="text-xl font-bold text-gray-800 mb-2">No boards yet</h2>
          <p className="text-gray-400 text-sm mb-6 max-w-xs">
            Create your first Kanban board to start organizing tasks with drag-and-drop
          </p>
          <button
            onClick={() => setShowBoardModal(true)}
            className="bg-indigo-600 hover:bg-indigo-700 text-white px-6 py-2.5 rounded-xl text-sm font-semibold transition-colors"
          >
            Create Your First Board
          </button>
        </div>
      ) : (
        <div className="flex-1 overflow-x-auto overflow-y-hidden p-4">
          <div className="flex gap-3 h-full pb-2" style={{ minWidth: "max-content" }}>
            {STATUSES.map((col) => (
              <Column
                key={col.key}
                col={col}
                cards={cards.filter((c) => c.status === col.key)}
                onAddCard={(s) => {
                  setNewCardStatus(s);
                  setEditingCard(null);
                  setShowCardModal(true);
                }}
                onEditCard={(card) => {
                  setEditingCard(card);
                  setShowCardModal(true);
                }}
                onDeleteCard={handleDeleteCard}
                onDragStart={(card) => { dragCard.current = card; }}
                onDrop={handleDrop}
              />
            ))}

            {/* Empty state within board */}
            {cards.length === 0 && (
              <div className="flex items-center justify-center w-64 flex-shrink-0 rounded-2xl border-2 border-dashed border-gray-200 bg-gray-50/50">
                <div className="text-center p-6">
                  <p className="text-gray-400 text-sm mb-3">No cards yet</p>
                  <button
                    onClick={() => { setNewCardStatus("todo"); setEditingCard(null); setShowCardModal(true); }}
                    className="text-indigo-600 text-sm font-medium hover:underline"
                  >
                    + Add first card
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* ── Modals ── */}
      {showBoardModal && (
        <BoardModal
          board={editingBoard}
          onSave={handleSaveBoard}
          onClose={() => { setShowBoardModal(false); setEditingBoard(null); }}
        />
      )}
      {showCardModal && (
        <CardModal
          card={editingCard}
          defaultStatus={newCardStatus}
          onSave={handleSaveCard}
          onClose={() => { setShowCardModal(false); setEditingCard(null); }}
        />
      )}
    </div>
  );
}
