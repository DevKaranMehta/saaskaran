import { useState, useEffect, useRef, useCallback } from "react";

const API = "/api/v1/kanban-board";

function getAuthHeader() {
  const token = localStorage.getItem("auth_token") || window.__auth_token || "";
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function apiFetch(path, options = {}) {
  const res = await fetch(`${API}${path}`, {
    headers: { "Content-Type": "application/json", ...getAuthHeader(), ...options.headers },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "Request failed");
  }
  if (res.status === 204) return null;
  return res.json();
}

const PRIORITY_COLORS = { low: "#10b981", medium: "#f59e0b", high: "#ef4444" };
const PRIORITY_LABELS = { low: "Low", medium: "Medium", high: "High" };

function Modal({ title, onClose, children }) {
  return (
    <div style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.5)", display: "flex", alignItems: "center", justifyContent: "center", zIndex: 1000 }}>
      <div style={{ background: "#fff", borderRadius: 12, padding: 28, minWidth: 360, maxWidth: 480, width: "90%", boxShadow: "0 20px 60px rgba(0,0,0,0.3)" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
          <h3 style={{ margin: 0, fontSize: 18, fontWeight: 700 }}>{title}</h3>
          <button onClick={onClose} style={{ background: "none", border: "none", fontSize: 22, cursor: "pointer", color: "#6b7280", lineHeight: 1 }}>×</button>
        </div>
        {children}
      </div>
    </div>
  );
}

function Input({ label, ...props }) {
  return (
    <div style={{ marginBottom: 14 }}>
      {label && <label style={{ display: "block", fontSize: 13, fontWeight: 600, color: "#374151", marginBottom: 5 }}>{label}</label>}
      <input style={{ width: "100%", padding: "8px 12px", border: "1.5px solid #d1d5db", borderRadius: 7, fontSize: 14, boxSizing: "border-box", outline: "none" }} {...props} />
    </div>
  );
}

function Textarea({ label, ...props }) {
  return (
    <div style={{ marginBottom: 14 }}>
      {label && <label style={{ display: "block", fontSize: 13, fontWeight: 600, color: "#374151", marginBottom: 5 }}>{label}</label>}
      <textarea style={{ width: "100%", padding: "8px 12px", border: "1.5px solid #d1d5db", borderRadius: 7, fontSize: 14, boxSizing: "border-box", resize: "vertical", minHeight: 80, outline: "none" }} {...props} />
    </div>
  );
}

function Select({ label, children, ...props }) {
  return (
    <div style={{ marginBottom: 14 }}>
      {label && <label style={{ display: "block", fontSize: 13, fontWeight: 600, color: "#374151", marginBottom: 5 }}>{label}</label>}
      <select style={{ width: "100%", padding: "8px 12px", border: "1.5px solid #d1d5db", borderRadius: 7, fontSize: 14, boxSizing: "border-box", background: "#fff", outline: "none" }} {...props}>{children}</select>
    </div>
  );
}

function Btn({ children, variant = "primary", style: extraStyle = {}, ...props }) {
  const styles = {
    primary: { background: "#6366f1", color: "#fff", border: "none" },
    danger:  { background: "#ef4444", color: "#fff", border: "none" },
    ghost:   { background: "transparent", color: "#6b7280", border: "1.5px solid #d1d5db" },
  };
  return (
    <button style={{ padding: "9px 18px", borderRadius: 8, fontSize: 14, fontWeight: 600, cursor: "pointer", ...styles[variant], ...extraStyle }} {...props}>
      {children}
    </button>
  );
}

function CardModal({ card, onSave, onClose }) {
  const [form, setForm] = useState({
    title: card?.title || "",
    description: card?.description || "",
    priority: card?.priority || "medium",
    due_date: card?.due_date ? card.due_date.slice(0, 10) : "",
  });
  const [saving, setSaving] = useState(false);
  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }));

  const submit = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      await onSave({ ...form, due_date: form.due_date || null });
      onClose();
    } catch (err) {
      alert(err.message);
    } finally {
      setSaving(false);
    }
  };

  return (
    <Modal title={card ? "Edit Card" : "New Card"} onClose={onClose}>
      <form onSubmit={submit}>
        <Input label="Title *" value={form.title} onChange={set("title")} required />
        <Textarea label="Description" value={form.description} onChange={set("description")} />
        <Select label="Priority" value={form.priority} onChange={set("priority")}>
          <option value="low">Low</option>
          <option value="medium">Medium</option>
          <option value="high">High</option>
        </Select>
        <Input label="Due Date" type="date" value={form.due_date} onChange={set("due_date")} />
        <div style={{ display: "flex", gap: 10, justifyContent: "flex-end", marginTop: 8 }}>
          <Btn variant="ghost" type="button" onClick={onClose}>Cancel</Btn>
          <Btn type="submit" disabled={saving}>{saving ? "Saving…" : "Save Card"}</Btn>
        </div>
      </form>
    </Modal>
  );
}

function ColumnModal({ column, onSave, onClose }) {
  const COLORS = ["#6366f1", "#f59e0b", "#10b981", "#ef4444", "#3b82f6", "#8b5cf6", "#ec4899"];
  const [form, setForm] = useState({ name: column?.name || "", color: column?.color || "#6366f1" });
  const [saving, setSaving] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      await onSave(form);
      onClose();
    } catch (err) {
      alert(err.message);
    } finally {
      setSaving(false);
    }
  };

  return (
    <Modal title={column ? "Edit Column" : "Add Column"} onClose={onClose}>
      <form onSubmit={submit}>
        <Input label="Column Name *" value={form.name} onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))} required />
        <div style={{ marginBottom: 14 }}>
          <label style={{ display: "block", fontSize: 13, fontWeight: 600, color: "#374151", marginBottom: 8 }}>Color</label>
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
            {COLORS.map((c) => (
              <div
                key={c}
                onClick={() => setForm((f) => ({ ...f, color: c }))}
                style={{
                  width: 28, height: 28, borderRadius: "50%", background: c, cursor: "pointer",
                  border: form.color === c ? "3px solid #1f2937" : "3px solid transparent",
                  transition: "border 0.1s",
                }}
              />
            ))}
          </div>
        </div>
        <div style={{ display: "flex", gap: 10, justifyContent: "flex-end", marginTop: 8 }}>
          <Btn variant="ghost" type="button" onClick={onClose}>Cancel</Btn>
          <Btn type="submit" disabled={saving}>{saving ? "Saving…" : "Save"}</Btn>
        </div>
      </form>
    </Modal>
  );
}

function BoardModal({ board, onSave, onClose }) {
  const [form, setForm] = useState({ name: board?.name || "", description: board?.description || "" });
  const [saving, setSaving] = useState(false);
  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }));

  const submit = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      await onSave(form);
      onClose();
    } catch (err) {
      alert(err.message);
    } finally {
      setSaving(false);
    }
  };

  return (
    <Modal title={board ? "Edit Board" : "New Board"} onClose={onClose}>
      <form onSubmit={submit}>
        <Input label="Board Name *" value={form.name} onChange={set("name")} required />
        <Textarea label="Description" value={form.description} onChange={set("description")} />
        <div style={{ display: "flex", gap: 10, justifyContent: "flex-end", marginTop: 8 }}>
          <Btn variant="ghost" type="button" onClick={onClose}>Cancel</Btn>
          <Btn type="submit" disabled={saving}>{saving ? "Saving…" : board ? "Update" : "Create Board"}</Btn>
        </div>
      </form>
    </Modal>
  );
}

function CardItem({ card, onEdit, onDelete, onToggle, onDragStart }) {
  const overdue = card.due_date && !card.is_completed && new Date(card.due_date) < new Date();

  return (
    <div
      draggable
      onDragStart={(e) => onDragStart(e, card)}
      style={{
        background: card.is_completed ? "#f9fafb" : "#fff",
        border: "1.5px solid #e5e7eb",
        borderLeft: `4px solid ${PRIORITY_COLORS[card.priority]}`,
        borderRadius: 8,
        padding: "10px 12px",
        marginBottom: 8,
        cursor: "grab",
        opacity: card.is_completed ? 0.65 : 1,
        userSelect: "none",
      }}
      onMouseEnter={(e) => { e.currentTarget.style.boxShadow = "0 4px 12px rgba(0,0,0,0.1)"; }}
      onMouseLeave={(e) => { e.currentTarget.style.boxShadow = "none"; }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 6 }}>
        <p style={{
          margin: 0, fontSize: 14, fontWeight: 600, color: "#1f2937", flex: 1,
          textDecoration: card.is_completed ? "line-through" : "none",
        }}>
          {card.title}
        </p>
        <div style={{ display: "flex", gap: 2, flexShrink: 0 }}>
          <button onClick={() => onToggle(card)} title={card.is_completed ? "Mark incomplete" : "Mark complete"}
            style={{ background: "none", border: "none", cursor: "pointer", fontSize: 15, padding: "2px 3px" }}>
            {card.is_completed ? "↩" : "✓"}
          </button>
          <button onClick={() => onEdit(card)} title="Edit"
            style={{ background: "none", border: "none", cursor: "pointer", fontSize: 14, padding: "2px 3px" }}>✏️</button>
          <button onClick={() => onDelete(card)} title="Delete"
            style={{ background: "none", border: "none", cursor: "pointer", fontSize: 14, padding: "2px 3px" }}>🗑️</button>
        </div>
      </div>

      {card.description && (
        <p style={{ margin: "5px 0 0", fontSize: 12, color: "#6b7280", lineHeight: 1.4 }}>
          {card.description.slice(0, 90)}{card.description.length > 90 ? "…" : ""}
        </p>
      )}

      <div style={{ display: "flex", gap: 8, marginTop: 8, alignItems: "center", flexWrap: "wrap" }}>
        <span style={{
          fontSize: 11,
          background: PRIORITY_COLORS[card.priority] + "22",
          color: PRIORITY_COLORS[card.priority],
          padding: "2px 7px", borderRadius: 99, fontWeight: 600,
        }}>
          {PRIORITY_LABELS[card.priority]}
        </span>
        {card.due_date && (
          <span style={{ fontSize: 11, color: overdue ? "#ef4444" : "#6b7280" }}>
            📅 {card.due_date.slice(0, 10)}{overdue ? " (overdue)" : ""}
          </span>
        )}
      </div>
    </div>
  );
}

function ColumnView({ column, onAddCard, onEditCard, onDeleteCard, onToggleCard, onDragStart, onDragOver, onDrop, onEditColumn, onDeleteColumn }) {
  const [dragOver, setDragOver] = useState(false);

  return (
    <div
      style={{
        width: 285,
        flexShrink: 0,
        background: dragOver ? "#ede9fe" : "#f3f4f6",
        borderRadius: 12,
        display: "flex",
        flexDirection: "column",
        maxHeight: "calc(100vh - 130px)",
        border: dragOver ? "2px dashed #6366f1" : "2px solid transparent",
        transition: "background 0.15s, border 0.15s",
      }}
      onDragOver={(e) => { e.preventDefault(); setDragOver(true); onDragOver(e, column); }}
      onDragLeave={() => setDragOver(false)}
      onDrop={(e) => { setDragOver(false); onDrop(e, column); }}
    >
      <div style={{
        padding: "14px 14px 10px",
        borderBottom: `3px solid ${column.color || "#6366f1"}`,
        borderRadius: "10px 10px 0 0",
      }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <span style={{ width: 10, height: 10, borderRadius: "50%", background: column.color || "#6366f1", display: "inline-block", flexShrink: 0 }} />
            <span style={{ fontWeight: 700, fontSize: 14, color: "#1f2937" }}>{column.name}</span>
            <span style={{ fontSize: 11, background: "#e5e7eb", color: "#6b7280", borderRadius: 99, padding: "1px 7px", fontWeight: 600 }}>
              {column.cards?.length || 0}
            </span>
          </div>
          <div style={{ display: "flex", gap: 2 }}>
            <button onClick={() => onEditColumn(column)} style={{ background: "none", border: "none", cursor: "pointer", fontSize: 12, padding: "2px 4px", color: "#9ca3af" }}>✏️</button>
            <button onClick={() => onDeleteColumn(column)} style={{ background: "none", border: "none", cursor: "pointer", fontSize: 12, padding: "2px 4px", color: "#9ca3af" }}>🗑️</button>
          </div>
        </div>
      </div>

      <div style={{ padding: 10, overflowY: "auto", flex: 1 }}>
        {(column.cards || []).map((card) => (
          <CardItem
            key={card.id}
            card={card}
            onEdit={onEditCard}
            onDelete={onDeleteCard}
            onToggle={onToggleCard}
            onDragStart={onDragStart}
          />
        ))}
        {(!column.cards || column.cards.length === 0) && (
          <div style={{ textAlign: "center", color: "#9ca3af", fontSize: 13, padding: "24px 0", pointerEvents: "none" }}>
            Drop cards here
          </div>
        )}
      </div>

      <div style={{ padding: "6px 10px 12px" }}>
        <button
          onClick={() => onAddCard(column)}
          style={{
            width: "100%", padding: "8px", background: "none",
            border: "1.5px dashed #d1d5db", borderRadius: 8,
            cursor: "pointer", color: "#6b7280", fontSize: 13, fontWeight: 600,
          }}
          onMouseEnter={(e) => { e.currentTarget.style.borderColor = "#6366f1"; e.currentTarget.style.color = "#6366f1"; }}
          onMouseLeave={(e) => { e.currentTarget.style.borderColor = "#d1d5db"; e.currentTarget.style.color = "#6b7280"; }}
        >
          + Add card
        </button>
      </div>
    </div>
  );
}

function BoardView({ board, onBack, onReload }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [modal, setModal] = useState(null);
  const dragCard = useRef(null);

  const fetchBoard = useCallback(async () => {
    setLoading(true);
    try {
      setData(await apiFetch(`/boards/${board.id}`));
    } catch (e) {
      alert(e.message);
    } finally {
      setLoading(false);
    }
  }, [board.id]);

  useEffect(() => { fetchBoard(); }, [fetchBoard]);

  const closeModal = () => setModal(null);

  const handleDragStart = (e, card) => {
    dragCard.current = card;
    e.dataTransfer.effectAllowed = "move";
  };
  const handleDragOver = (e) => { e.preventDefault(); };
  const handleDrop = async (e, targetColumn) => {
    e.preventDefault();
    const card = dragCard.current;
    if (!card || card.column_id === targetColumn.id) return;
    const pos = targetColumn.cards?.length || 0;
    try {
      await apiFetch(`/cards/${card.id}/move`, {
        method: "POST",
        body: JSON.stringify({ column_id: targetColumn.id, position: pos }),
      });
      await fetchBoard();
    } catch (err) {
      alert(err.message);
    }
    dragCard.current = null;
  };

  const handleAddCard = (col) => setModal({ type: "card", columnId: col.id, card: null });
  const handleEditCard = (card) => setModal({ type: "card", columnId: card.column_id, card });
  const handleDeleteCard = async (card) => {
    if (!confirm(`Delete "${card.title}"?`)) return;
    try { await apiFetch(`/cards/${card.id}`, { method: "DELETE" }); await fetchBoard(); }
    catch (e) { alert(e.message); }
  };
  const handleToggleCard = async (card) => {
    try {
      await apiFetch(`/cards/${card.id}`, { method: "PATCH", body: JSON.stringify({ is_completed: !card.is_completed }) });
      await fetchBoard();
    } catch (e) { alert(e.message); }
  };
  const handleSaveCard = async (form) => {
    if (modal.card) {
      await apiFetch(`/cards/${modal.card.id}`, { method: "PATCH", body: JSON.stringify(form) });
    } else {
      await apiFetch(`/columns/${modal.columnId}/cards`, { method: "POST", body: JSON.stringify(form) });
    }
    await fetchBoard();
  };

  const handleAddColumn = () => setModal({ type: "column", column: null });
  const handleEditColumn = (col) => setModal({ type: "column", column: col });
  const handleDeleteColumn = async (col) => {
    if (!confirm(`Delete column "${col.name}" and all its cards?`)) return;
    try { await apiFetch(`/columns/${col.id}`, { method: "DELETE" }); await fetchBoard(); }
    catch (e) { alert(e.message); }
  };
  const handleSaveColumn = async (form) => {
    if (modal.column) {
      await apiFetch(`/columns/${modal.column.id}`, { method: "PATCH", body: JSON.stringify(form) });
    } else {
      const pos = data?.columns?.length || 0;
      await apiFetch(`/boards/${board.id}/columns`, { method: "POST", body: JSON.stringify({ ...form, position: pos }) });
    }
    await fetchBoard();
  };

  const handleEditBoard = () => setModal({ type: "board" });
  const handleSaveBoard = async (form) => {
    await apiFetch(`/boards/${board.id}`, { method: "PATCH", body: JSON.stringify(form) });
    await fetchBoard();
    onReload();
  };

  if (loading) {
    return (
      <div style={{ display: "flex", alignItems: "center", justifyContent: "center", height: "100%", color: "#6b7280", fontSize: 15 }}>
        Loading board…
      </div>
    );
  }

  return (
    <div style={{ height: "100%", display: "flex", flexDirection: "column" }}>
      <div style={{
        padding: "14px 24px", background: "#fff", borderBottom: "1px solid #e5e7eb",
        display: "flex", alignItems: "center", gap: 16, flexShrink: 0,
      }}>
        <button onClick={onBack} style={{ background: "none", border: "none", cursor: "pointer", fontSize: 22, color: "#6b7280", padding: 0, lineHeight: 1 }}>←</button>
        <div style={{ flex: 1, minWidth: 0 }}>
          <h2 style={{ margin: 0, fontSize: 20, fontWeight: 800, color: "#1f2937" }}>{data?.name}</h2>
          {data?.description && (
            <p style={{ margin: "2px 0 0", fontSize: 13, color: "#6b7280", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{data.description}</p>
          )}
        </div>
        <div style={{ display: "flex", gap: 10, flexShrink: 0 }}>
          <Btn variant="ghost" onClick={handleEditBoard}>✏️ Edit</Btn>
          <Btn onClick={handleAddColumn}>+ Column</Btn>
        </div>
      </div>

      <div style={{ flex: 1, overflowX: "auto", overflowY: "hidden", padding: "20px 20px 20px", display: "flex", gap: 16, alignItems: "flex-start" }}>
        {(data?.columns || []).map((col) => (
          <ColumnView
            key={col.id}
            column={col}
            onAddCard={handleAddCard}
            onEditCard={handleEditCard}
            onDeleteCard={handleDeleteCard}
            onToggleCard={handleToggleCard}
            onDragStart={handleDragStart}
            onDragOver={handleDragOver}
            onDrop={handleDrop}
            onEditColumn={handleEditColumn}
            onDeleteColumn={handleDeleteColumn}
          />
        ))}
        {(!data?.columns || data.columns.length === 0) && (
          <div style={{ color: "#9ca3af", fontSize: 15, padding: "60px 0", textAlign: "center", width: "100%" }}>
            No columns yet. Click "+ Column" to get started.
          </div>
        )}
      </div>

      {modal?.type === "card" && (
        <CardModal card={modal.card} onSave={handleSaveCard} onClose={closeModal} />
      )}
      {modal?.type === "column" && (
        <ColumnModal column={modal.column} onSave={handleSaveColumn} onClose={closeModal} />
      )}
      {modal?.type === "board" && (
        <BoardModal board={data} onSave={handleSaveBoard} onClose={closeModal} />
      )}
    </div>
  );
}

function BoardList({ onSelect, reload }) {
  const [boards, setBoards] = useState([]);
  const [loading, setLoading] = useState(true);
  const [modal, setModal] = useState(false);

  const fetchBoards = useCallback(async () => {
    setLoading(true);
    try { setBoards(await apiFetch("/boards")); }
    catch (e) { alert(e.message); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { fetchBoards(); }, [fetchBoards, reload]);

  const handleCreate = async (form) => {
    await apiFetch("/boards", { method: "POST", body: JSON.stringify(form) });
    await fetchBoards();
  };

  const handleDelete = async (board, e) => {
    e.stopPropagation();
    if (!confirm(`Delete board "${board.name}" and all its data?`)) return;
    try { await apiFetch(`/boards/${board.id}`, { method: "DELETE" }); await fetchBoards(); }
    catch (err) { alert(err.message); }
  };

  return (
    <div style={{ padding: "32px 32px 60px", maxWidth: 960, margin: "0 auto" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 32 }}>
        <div>
          <h1 style={{ margin: 0, fontSize: 28, fontWeight: 800, color: "#1f2937" }}>📋 Kanban Boards</h1>
          <p style={{ margin: "4px 0 0", color: "#6b7280", fontSize: 14 }}>Organize your work visually, Trello-style</p>
        </div>
        <Btn onClick={() => setModal(true)}>+ New Board</Btn>
      </div>

      {loading ? (
        <div style={{ textAlign: "center", color: "#9ca3af", padding: 60, fontSize: 15 }}>Loading boards…</div>
      ) : boards.length === 0 ? (
        <div style={{ textAlign: "center", padding: 60, border: "2px dashed #e5e7eb", borderRadius: 16, color: "#9ca3af" }}>
          <div style={{ fontSize: 52, marginBottom: 12 }}>🗂️</div>
          <p style={{ fontSize: 17, fontWeight: 600, margin: "0 0 8px", color: "#6b7280" }}>No boards yet</p>
          <p style={{ fontSize: 14, margin: "0 0 20px" }}>Create your first Kanban board to get started</p>
          <Btn onClick={() => setModal(true)}>Create First Board</Btn>
        </div>
      ) : (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(270px, 1fr))", gap: 20 }}>
          {boards.map((b) => (
            <div
              key={b.id}
              onClick={() => onSelect(b)}
              style={{
                background: "#fff", border: "1.5px solid #e5e7eb", borderRadius: 12,
                padding: 22, cursor: "pointer", position: "relative",
                transition: "all 0.15s",
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.borderColor = "#6366f1";
                e.currentTarget.style.boxShadow = "0 4px 20px rgba(99,102,241,0.13)";
                e.currentTarget.style.transform = "translateY(-2px)";
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.borderColor = "#e5e7eb";
                e.currentTarget.style.boxShadow = "none";
                e.currentTarget.style.transform = "none";
              }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                <h3 style={{ margin: "0 0 6px", fontSize: 16, fontWeight: 700, color: "#1f2937", flex: 1, paddingRight: 8 }}>{b.name}</h3>
                <button
                  onClick={(e) => handleDelete(b, e)}
                  style={{ background: "none", border: "none", cursor: "pointer", fontSize: 15, color: "#d1d5db", padding: 0, lineHeight: 1, flexShrink: 0 }}
                  onMouseEnter={(e) => { e.currentTarget.style.color = "#ef4444"; }}
                  onMouseLeave={(e) => { e.currentTarget.style.color = "#d1d5db"; }}
                >🗑️</button>
              </div>
              {b.description && (
                <p style={{ margin: "0 0 14px", fontSize: 13, color: "#6b7280", lineHeight: 1.5 }}>
                  {b.description.slice(0, 100)}{b.description.length > 100 ? "…" : ""}
                </p>
              )}
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                <span style={{ fontSize: 12, color: "#9ca3af" }}>
                  Created {new Date(b.created_at).toLocaleDateString()}
                </span>
                <span style={{ fontSize: 12, color: "#6366f1", fontWeight: 600 }}>Open →</span>
              </div>
            </div>
          ))}
        </div>
      )}

      {modal && (
        <BoardModal board={null} onSave={handleCreate} onClose={() => setModal(false)} />
      )}
    </div>
  );
}

export default function KanbanApp() {
  const [selectedBoard, setSelectedBoard] = useState(null);
  const [reloadTick, setReloadTick] = useState(0);

  return (
    <div style={{
      fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
      height: "100vh",
      overflow: "hidden",
      display: "flex",
      flexDirection: "column",
      background: "#f9fafb",
    }}>
      {selectedBoard ? (
        <BoardView
          board={selectedBoard}
          onBack={() => setSelectedBoard(null)}
          onReload={() => setReloadTick((t) => t + 1)}
        />
      ) : (
        <div style={{ flex: 1, overflowY: "auto" }}>
          <BoardList onSelect={setSelectedBoard} reload={reloadTick} />
        </div>
      )}
    </div>
  );
}
