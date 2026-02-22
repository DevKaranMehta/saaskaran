"""Pattern library for the AI extension builder.

Contains 3 complete, production-quality reference extension examples.
select_reference(user_message) picks the best match based on keywords.

Patterns:
  PATTERN_NOTES        — simple flat CRUD (default)
  PATTERN_TASK_MANAGER — enums + filtering + stats endpoint (tasks, tickets, projects)
  PATTERN_INVOICING    — relational models + financial fields (billing, orders, expenses)
"""

from __future__ import annotations

# ── Keyword tables ───────────────────────────────────────────────────────────

_RELATIONAL_KW = {
    "invoice", "invoic", "billing", "payment", "pay", "receipt",
    "client", "quote", "subscription", "expense", "revenue",
    "line item", "purchase", "order", "sale", "product",
    "inventory", "stock", "sku", "price", "cost",
}

_TASK_KW = {
    "task", "todo", "to-do", "project", "kanban", "sprint",
    "backlog", "milestone", "workflow", "assignment", "deadline",
    "ticket", "helpdesk", "support ticket", "bug", "issue",
    "track", "tracker",
}


def select_reference(user_message: str) -> str:
    """Return the most relevant pattern for the user's request."""
    msg = user_message.lower()
    rel  = sum(1 for kw in _RELATIONAL_KW if kw in msg)
    task = sum(1 for kw in _TASK_KW       if kw in msg)
    if rel  and rel  >= task: return PATTERN_INVOICING
    if task:                  return PATTERN_TASK_MANAGER
    return PATTERN_NOTES


# ── Pattern: Notes (simple flat CRUD) ───────────────────────────────────────

PATTERN_NOTES = '''
## REFERENCE EXTENSION (simple flat CRUD) — "notes"

Use EXACT same imports, structure, and conventions. Never invent alternatives.

──────────────────────────────────────────────────────────
FILE: extensions/notes/__init__.py
──────────────────────────────────────────────────────────
from .extension import NotesExtension

──────────────────────────────────────────────────────────
FILE: extensions/notes/extension.py
──────────────────────────────────────────────────────────
"""Notes Extension."""
from __future__ import annotations
from saas_builder.core import ExtensionBase

class NotesExtension(ExtensionBase):
    name        = "notes"
    version     = "1.0.0"
    description = "Simple notes with title, content, and tags."
    author      = "SaaS Factory"
    dependencies: list[str] = []
    api_prefix  = "/notes"
    permissions = ["notes.read", "notes.write"]

    def on_install(self) -> None:
        from . import models  # noqa: F401

    def on_activate(self, app) -> None:
        from .routes import router
        app.include_router(router, prefix=f"/api/v1{self.api_prefix}")

    def on_deactivate(self, app) -> None:
        pass

──────────────────────────────────────────────────────────
FILE: extensions/notes/models.py
──────────────────────────────────────────────────────────
"""Notes — SQLAlchemy models."""
from __future__ import annotations
import uuid
from datetime import UTC, datetime
from sqlalchemy import String, Text, JSON
from sqlalchemy import DateTime as SADateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from api.database import Base

def utcnow() -> datetime:
    return datetime.now(UTC)

class Note(Base):
    __tablename__ = "ext_notes"
    id:         Mapped[str]      = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id:  Mapped[str]      = mapped_column(UUID(as_uuid=False), nullable=False, index=True)
    title:      Mapped[str]      = mapped_column(String(255), nullable=False)
    content:    Mapped[str|None] = mapped_column(Text, nullable=True)
    tags:       Mapped[list]     = mapped_column(JSON, default=list, nullable=False)
    is_pinned:  Mapped[bool]     = mapped_column(default=False, nullable=False)
    created_by: Mapped[str]      = mapped_column(UUID(as_uuid=False), nullable=False)
    created_at: Mapped[datetime] = mapped_column(SADateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(SADateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

──────────────────────────────────────────────────────────
FILE: extensions/notes/schemas.py
──────────────────────────────────────────────────────────
from __future__ import annotations
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

class NoteCreate(BaseModel):
    title:     str           = Field(..., min_length=1, max_length=255)
    content:   Optional[str] = None
    tags:      list[str]     = Field(default_factory=list)
    is_pinned: bool          = False

class NoteUpdate(BaseModel):
    title:     Optional[str]       = Field(None, min_length=1, max_length=255)
    content:   Optional[str]       = None
    tags:      Optional[list[str]] = None
    is_pinned: Optional[bool]      = None

class NoteResponse(BaseModel):
    id: str; tenant_id: str; title: str; content: Optional[str]
    tags: list[str]; is_pinned: bool; created_by: str
    created_at: datetime; updated_at: datetime
    class Config:
        from_attributes = True

──────────────────────────────────────────────────────────
FILE: extensions/notes/routes.py
──────────────────────────────────────────────────────────
from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from api.auth import get_current_user
from api.database import get_db
from api.models import User
from .models import Note
from .schemas import NoteCreate, NoteResponse, NoteUpdate

router = APIRouter(tags=["notes"])

@router.get("/", response_model=list[NoteResponse])
async def list_notes(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Note).where(Note.tenant_id == current_user.tenant_id).order_by(Note.is_pinned.desc(), Note.created_at.desc()))
    return result.scalars().all()

@router.post("/", response_model=NoteResponse, status_code=status.HTTP_201_CREATED)
async def create_note(payload: NoteCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    note = Note(tenant_id=current_user.tenant_id, created_by=current_user.id, **payload.model_dump())
    db.add(note); await db.commit(); await db.refresh(note); return note

@router.patch("/{item_id}", response_model=NoteResponse)
async def update_note(item_id: str, payload: NoteUpdate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Note).where(Note.id == item_id, Note.tenant_id == current_user.tenant_id))
    note = result.scalar_one_or_none()
    if not note: raise HTTPException(status_code=404, detail="Note not found")
    for f, v in payload.model_dump(exclude_unset=True).items(): setattr(note, f, v)
    await db.commit(); await db.refresh(note); return note

@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_note(item_id: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Note).where(Note.id == item_id, Note.tenant_id == current_user.tenant_id))
    note = result.scalar_one_or_none()
    if not note: raise HTTPException(status_code=404, detail="Note not found")
    await db.delete(note); await db.commit()

@router.get("/stats")
async def get_stats(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    total = (await db.execute(select(func.count(Note.id)).where(Note.tenant_id == current_user.tenant_id))).scalar_one()
    pinned = (await db.execute(select(func.count(Note.id)).where(Note.tenant_id == current_user.tenant_id, Note.is_pinned == True))).scalar_one()
    return {"total": total, "pinned": pinned}

──────────────────────────────────────────────────────────
FILE: extensions/notes/ui_spec.json
──────────────────────────────────────────────────────────
{
  "label": "Notes", "icon": "📝", "color": "#6366f1",
  "description": "Simple notes with title, content and tags.",
  "api_base": "/notes",
  "resources": [{
    "key": "notes", "label": "Notes",
    "list": "GET /", "create": "POST /", "update": "PATCH /{id}", "delete": "DELETE /{id}",
    "id_field": "id", "empty_message": "No notes yet. Create your first note!",
    "fields": [
      { "key": "title",     "label": "Title",   "type": "text",    "required": true,  "show_in_list": true },
      { "key": "content",   "label": "Content", "type": "textarea","required": false, "show_in_list": false },
      { "key": "tags",      "label": "Tags",    "type": "tags",    "required": false, "show_in_list": true },
      { "key": "is_pinned", "label": "Pinned",  "type": "boolean", "required": false, "show_in_list": true },
      { "key": "created_at","label": "Created", "type": "date",    "required": false, "show_in_list": true }
    ]
  }]
}
'''


# ── Pattern: Task Manager (enums + filtering + stats) ───────────────────────

PATTERN_TASK_MANAGER = '''
## REFERENCE EXTENSION (enums + filtering + stats) — "task_tracker"

Use EXACT same imports, structure, and conventions. Never invent alternatives.
This shows: SQLAlchemy enums, query param filters, stats endpoint, smart ordering.

──────────────────────────────────────────────────────────
FILE: extensions/task_tracker/__init__.py
──────────────────────────────────────────────────────────
from .extension import TaskTrackerExtension

──────────────────────────────────────────────────────────
FILE: extensions/task_tracker/extension.py
──────────────────────────────────────────────────────────
"""Task Tracker Extension."""
from __future__ import annotations
from saas_builder.core import ExtensionBase

class TaskTrackerExtension(ExtensionBase):
    name        = "task_tracker"
    version     = "1.0.0"
    description = "Task and to-do management with priorities, statuses, and deadlines."
    author      = "SaaS Factory"
    dependencies: list[str] = []
    api_prefix  = "/task-tracker"
    permissions = ["task_tracker.read", "task_tracker.write"]

    def on_install(self) -> None:
        from . import models  # noqa: F401

    def on_activate(self, app) -> None:
        from .routes import router
        app.include_router(router, prefix=f"/api/v1{self.api_prefix}")

    def on_deactivate(self, app) -> None:
        pass

──────────────────────────────────────────────────────────
FILE: extensions/task_tracker/models.py
──────────────────────────────────────────────────────────
"""Task Tracker — SQLAlchemy models."""
from __future__ import annotations
import enum
import uuid
from datetime import UTC, datetime
from sqlalchemy import String, Text, Boolean, Enum as SAEnum
from sqlalchemy import DateTime as SADateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from api.database import Base

def utcnow() -> datetime:
    return datetime.now(UTC)

class TaskStatus(str, enum.Enum):
    todo        = "todo"
    in_progress = "in_progress"
    review      = "review"
    done        = "done"

class TaskPriority(str, enum.Enum):
    low    = "low"
    medium = "medium"
    high   = "high"
    urgent = "urgent"

class Task(Base):
    __tablename__ = "ext_task_tracker_tasks"
    id:            Mapped[str]            = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id:     Mapped[str]            = mapped_column(UUID(as_uuid=False), nullable=False, index=True)
    created_by:    Mapped[str]            = mapped_column(UUID(as_uuid=False), nullable=False)
    title:         Mapped[str]            = mapped_column(String(255), nullable=False)
    description:   Mapped[str | None]    = mapped_column(Text, nullable=True)
    status:        Mapped[TaskStatus]     = mapped_column(SAEnum(TaskStatus),   default=TaskStatus.todo,    nullable=False, index=True)
    priority:      Mapped[TaskPriority]   = mapped_column(SAEnum(TaskPriority), default=TaskPriority.medium, nullable=False, index=True)
    assignee_name: Mapped[str | None]    = mapped_column(String(255), nullable=True)
    due_date:      Mapped[datetime | None] = mapped_column(SADateTime(timezone=True), nullable=True)
    is_completed:  Mapped[bool]           = mapped_column(Boolean, default=False, nullable=False)
    completed_at:  Mapped[datetime | None] = mapped_column(SADateTime(timezone=True), nullable=True)
    created_at:    Mapped[datetime]       = mapped_column(SADateTime(timezone=True), default=utcnow, nullable=False)
    updated_at:    Mapped[datetime]       = mapped_column(SADateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

──────────────────────────────────────────────────────────
FILE: extensions/task_tracker/schemas.py
──────────────────────────────────────────────────────────
from __future__ import annotations
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

class TaskCreate(BaseModel):
    title:         str              = Field(..., min_length=1, max_length=255)
    description:   Optional[str]   = None
    status:        str              = "todo"
    priority:      str              = "medium"
    assignee_name: Optional[str]   = None
    due_date:      Optional[datetime] = None

class TaskUpdate(BaseModel):
    title:         Optional[str]      = Field(None, min_length=1, max_length=255)
    description:   Optional[str]      = None
    status:        Optional[str]      = None
    priority:      Optional[str]      = None
    assignee_name: Optional[str]      = None
    due_date:      Optional[datetime] = None
    is_completed:  Optional[bool]     = None

class TaskResponse(BaseModel):
    id: str; tenant_id: str; created_by: str
    title: str; description: Optional[str]
    status: str; priority: str
    assignee_name: Optional[str]; due_date: Optional[datetime]
    is_completed: bool; completed_at: Optional[datetime]
    created_at: datetime; updated_at: datetime
    class Config:
        from_attributes = True

──────────────────────────────────────────────────────────
FILE: extensions/task_tracker/routes.py
──────────────────────────────────────────────────────────
"""Task Tracker — API routes."""
from __future__ import annotations
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from api.auth import get_current_user
from api.database import get_db
from api.models import User
from .models import Task, utcnow
from .schemas import TaskCreate, TaskResponse, TaskUpdate

router = APIRouter(tags=["task_tracker"])

@router.get("/", response_model=list[TaskResponse])
async def list_tasks(
    task_status:   Optional[str] = Query(None, alias="status",   description="Filter by status"),
    task_priority: Optional[str] = Query(None, alias="priority", description="Filter by priority"),
    db:            AsyncSession  = Depends(get_db),
    current_user:  User          = Depends(get_current_user),
):
    q = select(Task).where(Task.tenant_id == current_user.tenant_id)
    if task_status:   q = q.where(Task.status   == task_status)
    if task_priority: q = q.where(Task.priority == task_priority)
    q = q.order_by(Task.priority.desc(), Task.due_date.asc().nullslast(), Task.created_at.desc())
    return (await db.execute(q)).scalars().all()

@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    payload:      TaskCreate,
    db:           AsyncSession = Depends(get_db),
    current_user: User         = Depends(get_current_user),
):
    task = Task(tenant_id=current_user.tenant_id, created_by=current_user.id, **payload.model_dump())
    db.add(task); await db.commit(); await db.refresh(task); return task

@router.patch("/{item_id}", response_model=TaskResponse)
async def update_task(
    item_id:      str,
    payload:      TaskUpdate,
    db:           AsyncSession = Depends(get_db),
    current_user: User         = Depends(get_current_user),
):
    result = await db.execute(select(Task).where(Task.id == item_id, Task.tenant_id == current_user.tenant_id))
    task = result.scalar_one_or_none()
    if not task: raise HTTPException(status_code=404, detail="Task not found")
    data = payload.model_dump(exclude_unset=True)
    if data.get("is_completed") is True and not task.is_completed:
        data.setdefault("status", "done")
        data["completed_at"] = utcnow()
    for f, v in data.items(): setattr(task, f, v)
    await db.commit(); await db.refresh(task); return task

@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    item_id:      str,
    db:           AsyncSession = Depends(get_db),
    current_user: User         = Depends(get_current_user),
):
    result = await db.execute(select(Task).where(Task.id == item_id, Task.tenant_id == current_user.tenant_id))
    task = result.scalar_one_or_none()
    if not task: raise HTTPException(status_code=404, detail="Task not found")
    await db.delete(task); await db.commit()

@router.get("/stats")
async def get_stats(
    db:           AsyncSession = Depends(get_db),
    current_user: User         = Depends(get_current_user),
):
    rows = await db.execute(
        select(Task.status, func.count(Task.id).label("count"))
        .where(Task.tenant_id == current_user.tenant_id)
        .group_by(Task.status)
    )
    by_status = {row.status: row.count for row in rows}
    total     = sum(by_status.values())
    return {"total": total, "completed": by_status.get("done", 0), "open": total - by_status.get("done", 0), "by_status": by_status}

──────────────────────────────────────────────────────────
FILE: extensions/task_tracker/ui_spec.json
──────────────────────────────────────────────────────────
{
  "label": "Task Tracker", "icon": "📋", "color": "#8b5cf6",
  "description": "Manage tasks with priorities, statuses, assignees, and deadlines.",
  "api_base": "/task-tracker",
  "resources": [{
    "key": "tasks", "label": "Tasks",
    "list": "GET /", "create": "POST /", "update": "PATCH /{id}", "delete": "DELETE /{id}",
    "id_field": "id", "empty_message": "No tasks yet. Create your first task!",
    "fields": [
      { "key": "title",         "label": "Title",       "type": "text",     "required": true,  "show_in_list": true  },
      { "key": "status",        "label": "Status",      "type": "select",   "required": false, "show_in_list": true,
        "options": ["todo", "in_progress", "review", "done"] },
      { "key": "priority",      "label": "Priority",    "type": "select",   "required": false, "show_in_list": true,
        "options": ["low", "medium", "high", "urgent"] },
      { "key": "assignee_name", "label": "Assigned To", "type": "text",     "required": false, "show_in_list": true  },
      { "key": "due_date",      "label": "Due Date",    "type": "date",     "required": false, "show_in_list": true  },
      { "key": "description",   "label": "Description", "type": "textarea", "required": false, "show_in_list": false },
      { "key": "is_completed",  "label": "Completed",   "type": "boolean",  "required": false, "show_in_list": false }
    ]
  }]
}
'''


# ── Pattern: Invoicing (relational + financial fields) ───────────────────────

PATTERN_INVOICING = '''
## REFERENCE EXTENSION (relational models + financial fields) — "invoice_manager"

Use EXACT same imports, structure, and conventions. Never invent alternatives.
This shows: ForeignKey with cascade delete, Numeric for money, computed total,
relationship() with lazy="selectin", mark-paid endpoint, multi-resource ui_spec.

──────────────────────────────────────────────────────────
FILE: extensions/invoice_manager/__init__.py
──────────────────────────────────────────────────────────
from .extension import InvoiceManagerExtension

──────────────────────────────────────────────────────────
FILE: extensions/invoice_manager/extension.py
──────────────────────────────────────────────────────────
"""Invoice Manager Extension."""
from __future__ import annotations
from saas_builder.core import ExtensionBase

class InvoiceManagerExtension(ExtensionBase):
    name        = "invoice_manager"
    version     = "1.0.0"
    description = "Invoice management with line items and payment tracking."
    author      = "SaaS Factory"
    dependencies: list[str] = []
    api_prefix  = "/invoice-manager"
    permissions = ["invoice_manager.read", "invoice_manager.write"]

    def on_install(self) -> None:
        from . import models  # noqa: F401

    def on_activate(self, app) -> None:
        from .routes import router
        app.include_router(router, prefix=f"/api/v1{self.api_prefix}")

    def on_deactivate(self, app) -> None:
        pass

──────────────────────────────────────────────────────────
FILE: extensions/invoice_manager/models.py
──────────────────────────────────────────────────────────
"""Invoice Manager — SQLAlchemy models (relational)."""
from __future__ import annotations
import enum
import uuid
from datetime import UTC, datetime
from sqlalchemy import String, Text, Numeric, ForeignKey, Enum as SAEnum
from sqlalchemy import DateTime as SADateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from api.database import Base

def utcnow() -> datetime:
    return datetime.now(UTC)

class InvoiceStatus(str, enum.Enum):
    draft     = "draft"
    sent      = "sent"
    paid      = "paid"
    overdue   = "overdue"
    cancelled = "cancelled"

class Invoice(Base):
    __tablename__ = "ext_invoice_manager_invoices"
    id:             Mapped[str]             = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id:      Mapped[str]             = mapped_column(UUID(as_uuid=False), nullable=False, index=True)
    created_by:     Mapped[str]             = mapped_column(UUID(as_uuid=False), nullable=False)
    invoice_number: Mapped[str]             = mapped_column(String(50), nullable=False)
    client_name:    Mapped[str]             = mapped_column(String(255), nullable=False)
    client_email:   Mapped[str | None]     = mapped_column(String(255), nullable=True)
    status:         Mapped[InvoiceStatus]   = mapped_column(SAEnum(InvoiceStatus), default=InvoiceStatus.draft, nullable=False, index=True)
    subtotal:       Mapped[float]           = mapped_column(Numeric(12, 2), default=0.0, nullable=False)
    tax_rate:       Mapped[float]           = mapped_column(Numeric(5,  2), default=0.0, nullable=False)
    total:          Mapped[float]           = mapped_column(Numeric(12, 2), default=0.0, nullable=False)
    currency:       Mapped[str]             = mapped_column(String(3),  default="USD", nullable=False)
    notes:          Mapped[str | None]     = mapped_column(Text, nullable=True)
    due_date:       Mapped[datetime | None] = mapped_column(SADateTime(timezone=True), nullable=True)
    paid_at:        Mapped[datetime | None] = mapped_column(SADateTime(timezone=True), nullable=True)
    created_at:     Mapped[datetime]        = mapped_column(SADateTime(timezone=True), default=utcnow, nullable=False)
    updated_at:     Mapped[datetime]        = mapped_column(SADateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)
    line_items: Mapped[list["LineItem"]] = relationship(
        "LineItem", back_populates="invoice", cascade="all, delete-orphan", lazy="selectin"
    )

class LineItem(Base):
    __tablename__ = "ext_invoice_manager_line_items"
    id:          Mapped[str]   = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id:   Mapped[str]   = mapped_column(UUID(as_uuid=False), nullable=False, index=True)
    invoice_id:  Mapped[str]   = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("ext_invoice_manager_invoices.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    description: Mapped[str]   = mapped_column(String(500), nullable=False)
    quantity:    Mapped[float]  = mapped_column(Numeric(10, 3), default=1.0, nullable=False)
    unit_price:  Mapped[float]  = mapped_column(Numeric(12, 2), nullable=False)
    amount:      Mapped[float]  = mapped_column(Numeric(12, 2), nullable=False)
    invoice: Mapped["Invoice"] = relationship("Invoice", back_populates="line_items")

──────────────────────────────────────────────────────────
FILE: extensions/invoice_manager/schemas.py
──────────────────────────────────────────────────────────
from __future__ import annotations
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

class LineItemCreate(BaseModel):
    description: str   = Field(..., min_length=1, max_length=500)
    quantity:    float = Field(1.0, gt=0)
    unit_price:  float = Field(..., gt=0)

class LineItemResponse(BaseModel):
    id: str; invoice_id: str; description: str
    quantity: float; unit_price: float; amount: float
    class Config:
        from_attributes = True

class InvoiceCreate(BaseModel):
    client_name:    str                  = Field(..., min_length=1, max_length=255)
    client_email:   Optional[str]        = None
    invoice_number: str                  = Field(..., min_length=1, max_length=50)
    tax_rate:       float                = Field(0.0, ge=0, le=100)
    currency:       str                  = Field("USD", min_length=3, max_length=3)
    notes:          Optional[str]        = None
    due_date:       Optional[datetime]   = None
    line_items:     list[LineItemCreate] = Field(default_factory=list)

class InvoiceUpdate(BaseModel):
    client_name:  Optional[str]      = Field(None, min_length=1, max_length=255)
    client_email: Optional[str]      = None
    status:       Optional[str]      = None
    notes:        Optional[str]      = None
    due_date:     Optional[datetime] = None

class InvoiceResponse(BaseModel):
    id: str; tenant_id: str; created_by: str; invoice_number: str
    client_name: str; client_email: Optional[str]
    status: str; subtotal: float; tax_rate: float; total: float; currency: str
    notes: Optional[str]; due_date: Optional[datetime]; paid_at: Optional[datetime]
    created_at: datetime; updated_at: datetime
    line_items: list[LineItemResponse] = []
    class Config:
        from_attributes = True

──────────────────────────────────────────────────────────
FILE: extensions/invoice_manager/routes.py
──────────────────────────────────────────────────────────
"""Invoice Manager — API routes."""
from __future__ import annotations
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from api.auth import get_current_user
from api.database import get_db
from api.models import User
from .models import Invoice, LineItem, InvoiceStatus, utcnow
from .schemas import InvoiceCreate, InvoiceResponse, InvoiceUpdate

router = APIRouter(tags=["invoice_manager"])

@router.get("/", response_model=list[InvoiceResponse])
async def list_invoices(
    inv_status: Optional[str] = Query(None, alias="status"),
    db:           AsyncSession  = Depends(get_db),
    current_user: User          = Depends(get_current_user),
):
    q = select(Invoice).where(Invoice.tenant_id == current_user.tenant_id)
    if inv_status: q = q.where(Invoice.status == inv_status)
    q = q.order_by(Invoice.created_at.desc())
    return (await db.execute(q)).scalars().all()

@router.post("/", response_model=InvoiceResponse, status_code=status.HTTP_201_CREATED)
async def create_invoice(
    payload:      InvoiceCreate,
    db:           AsyncSession = Depends(get_db),
    current_user: User         = Depends(get_current_user),
):
    subtotal = sum(li.quantity * li.unit_price for li in payload.line_items)
    total    = round(float(subtotal) * (1 + payload.tax_rate / 100), 2)
    data     = payload.model_dump(exclude={"line_items"})
    invoice  = Invoice(tenant_id=current_user.tenant_id, created_by=current_user.id,
                       subtotal=subtotal, total=total, **data)
    db.add(invoice)
    await db.flush()
    for li in payload.line_items:
        amount = round(li.quantity * li.unit_price, 2)
        db.add(LineItem(invoice_id=invoice.id, tenant_id=current_user.tenant_id,
                        amount=amount, **li.model_dump()))
    await db.commit(); await db.refresh(invoice); return invoice

@router.patch("/{item_id}", response_model=InvoiceResponse)
async def update_invoice(
    item_id: str, payload: InvoiceUpdate,
    db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Invoice).where(Invoice.id == item_id, Invoice.tenant_id == current_user.tenant_id))
    invoice = result.scalar_one_or_none()
    if not invoice: raise HTTPException(status_code=404, detail="Invoice not found")
    for f, v in payload.model_dump(exclude_unset=True).items(): setattr(invoice, f, v)
    await db.commit(); await db.refresh(invoice); return invoice

@router.post("/{item_id}/mark-paid", response_model=InvoiceResponse)
async def mark_paid(
    item_id: str,
    db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Invoice).where(Invoice.id == item_id, Invoice.tenant_id == current_user.tenant_id))
    invoice = result.scalar_one_or_none()
    if not invoice: raise HTTPException(status_code=404, detail="Invoice not found")
    invoice.status  = InvoiceStatus.paid
    invoice.paid_at = utcnow()
    await db.commit(); await db.refresh(invoice); return invoice

@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_invoice(
    item_id: str,
    db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Invoice).where(Invoice.id == item_id, Invoice.tenant_id == current_user.tenant_id))
    invoice = result.scalar_one_or_none()
    if not invoice: raise HTTPException(status_code=404, detail="Invoice not found")
    await db.delete(invoice); await db.commit()

@router.get("/stats")
async def get_stats(
    db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user),
):
    rows = await db.execute(
        select(Invoice.status, func.count(Invoice.id).label("cnt"), func.sum(Invoice.total).label("revenue"))
        .where(Invoice.tenant_id == current_user.tenant_id)
        .group_by(Invoice.status)
    )
    by_status: dict = {}
    total_revenue = 0.0
    for row in rows:
        by_status[row.status] = {"count": row.cnt, "revenue": float(row.revenue or 0)}
        if row.status == "paid": total_revenue = float(row.revenue or 0)
    return {"paid_revenue": total_revenue, "by_status": by_status}

──────────────────────────────────────────────────────────
FILE: extensions/invoice_manager/ui_spec.json
──────────────────────────────────────────────────────────
{
  "label": "Invoices", "icon": "💰", "color": "#10b981",
  "description": "Invoice management with line items and payment tracking.",
  "api_base": "/invoice-manager",
  "resources": [{
    "key": "invoices", "label": "Invoices",
    "list": "GET /", "create": "POST /", "update": "PATCH /{id}", "delete": "DELETE /{id}",
    "id_field": "id", "empty_message": "No invoices yet. Create your first invoice!",
    "fields": [
      { "key": "invoice_number", "label": "Invoice #",    "type": "text",     "required": true,  "show_in_list": true  },
      { "key": "client_name",    "label": "Client",       "type": "text",     "required": true,  "show_in_list": true  },
      { "key": "status",         "label": "Status",       "type": "select",   "required": false, "show_in_list": true,
        "options": ["draft", "sent", "paid", "overdue", "cancelled"] },
      { "key": "total",          "label": "Total",        "type": "number",   "required": false, "show_in_list": true  },
      { "key": "currency",       "label": "Currency",     "type": "text",     "required": false, "show_in_list": false },
      { "key": "due_date",       "label": "Due Date",     "type": "date",     "required": false, "show_in_list": true  },
      { "key": "client_email",   "label": "Client Email", "type": "email",    "required": false, "show_in_list": false },
      { "key": "notes",          "label": "Notes",        "type": "textarea", "required": false, "show_in_list": false }
    ]
  }]
}
'''
