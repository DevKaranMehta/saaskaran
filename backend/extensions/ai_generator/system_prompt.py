"""System prompt builder for the AI extension generator."""

from __future__ import annotations
from pathlib import Path

EXTENSIONS_BASE_PATH = "/home/chatwoot/saaskaran/backend/extensions"

# ─────────────────────────────────────────────────────────────────────────────
# ABSOLUTE CONSTRAINT — placed at top of every prompt
# ─────────────────────────────────────────────────────────────────────────────

AGENTIC_PREAMBLE = '''## OUTPUT FORMAT — [WRITE_FILE:] BLOCKS

You output files using this format:

[WRITE_FILE: path/to/file.py]
file content here
[/WRITE_FILE]

The system automatically writes files to disk. Paths can be:
- `extensions/my_ext/models.py`      → writes to backend/extensions/my_ext/models.py
- `frontend/components/extensions/MyPage.tsx` → writes to frontend/components/extensions/MyPage.tsx
- `frontend/app/(dashboard)/extensions/[name]/page.tsx` → updates the extension router

DO NOT use markdown fences (```) inside [WRITE_FILE:] blocks.
DO NOT output file content outside of [WRITE_FILE:] blocks.

'''


def _load_actual_codebase() -> str:
    """Read real source files and inject them so Claude has exact imports/patterns."""
    base = Path(EXTENSIONS_BASE_PATH).parent  # backend/

    # Use the first available working extension as a reference
    ref_candidates = ["todo_list", "invoicing", "kanban_board", "chatbot"]
    ref_ext = next((e for e in ref_candidates if (base / "extensions" / e / "models.py").exists()), None)

    files_to_read = [
        "api/database.py",
        "api/auth.py",
        "api/models.py",
    ]
    if ref_ext:
        files_to_read += [
            f"extensions/{ref_ext}/__init__.py",
            f"extensions/{ref_ext}/extension.py",
            f"extensions/{ref_ext}/models.py",
            f"extensions/{ref_ext}/schemas.py",
            f"extensions/{ref_ext}/routes.py",
        ]
        if (base / "extensions" / ref_ext / "ui_spec.json").exists():
            files_to_read.append(f"extensions/{ref_ext}/ui_spec.json")

    parts = [f"## ACTUAL CODEBASE (reference: {ref_ext}) — copy these exact imports\n"]
    for rel in files_to_read:
        path = base / rel
        if path.exists():
            content = path.read_text(encoding="utf-8")
            parts.append(f"\n### {rel}\n```\n{content}\n```\n")
    return "\n".join(parts)

# ─────────────────────────────────────────────────────────────────────────────
# REFERENCE EXTENSION — the "notes" extension. Study every import exactly.
# ─────────────────────────────────────────────────────────────────────────────

REFERENCE_EXTENSION = '''
## REFERENCE EXTENSION (simple) — "notes"

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
    admin_menu  = [{"label": "Notes", "icon": "file-text", "route": "/admin/notes"}]

    def default_config(self) -> dict:
        return {"max_notes_per_tenant": 1000}

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
    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
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
from sqlalchemy import select
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

──────────────────────────────────────────────────────────
FILE: extensions/notes/tests/__init__.py
──────────────────────────────────────────────────────────
(empty)

──────────────────────────────────────────────────────────
FILE: extensions/notes/tests/test_extension.py
──────────────────────────────────────────────────────────
import pytest
def test_extension_name():
    from extensions.notes.extension import NotesExtension
    assert NotesExtension().name == "notes"
def test_model_tablename():
    from extensions.notes.models import Note
    assert Note.__tablename__ == "ext_notes"
'''

# ─────────────────────────────────────────────────────────────────────────────
# ADVANCED PATTERNS — what separates a great extension from a mediocre one
# Every one of these patterns must be applied wherever relevant
# ─────────────────────────────────────────────────────────────────────────────

ADVANCED_PATTERNS = '''
## ADVANCED PATTERNS — apply ALL that are relevant to your extension

These patterns are what make an extension actually useful. A great extension uses
enums, filtering, smart ordering, stats, and workflow — not just basic CRUD.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PATTERN 1 — ENUMS (required for every status/type/priority field)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

```python
# models.py
import enum
from sqlalchemy import Enum as SAEnum

class TicketStatus(str, enum.Enum):
    open        = "open"
    in_progress = "in_progress"
    resolved    = "resolved"
    closed      = "closed"

class TicketPriority(str, enum.Enum):
    low      = "low"
    medium   = "medium"
    high     = "high"
    critical = "critical"

class Ticket(Base):
    __tablename__ = "ext_tickets"
    # ... id, tenant_id, created_by, created_at, updated_at ...
    status:   Mapped[TicketStatus]   = mapped_column(SAEnum(TicketStatus),   default=TicketStatus.open,   nullable=False, index=True)
    priority: Mapped[TicketPriority] = mapped_column(SAEnum(TicketPriority), default=TicketPriority.medium, nullable=False, index=True)

# schemas.py — use plain str, SQLAlchemy serialises the .value automatically
class TicketResponse(BaseModel):
    status:   str
    priority: str
    class Config:
        from_attributes = True
```

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PATTERN 2 — FILTERING IN LIST ENDPOINTS (required whenever status/priority exists)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

```python
# routes.py
from typing import Optional
from fastapi import Query

@router.get("/", response_model=list[TicketResponse])
async def list_tickets(
    status:   Optional[str] = Query(None, description="Filter by status"),
    priority: Optional[str] = Query(None, description="Filter by priority"),
    db:           AsyncSession = Depends(get_db),
    current_user: User         = Depends(get_current_user),
):
    q = select(Ticket).where(Ticket.tenant_id == current_user.tenant_id)
    if status:
        q = q.where(Ticket.status == status)
    if priority:
        q = q.where(Ticket.priority == priority)
    # Smart ordering: most urgent/important first, then newest
    q = q.order_by(Ticket.priority.desc(), Ticket.created_at.desc())
    result = await db.execute(q)
    return result.scalars().all()
```

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PATTERN 3 — STATS / SUMMARY ENDPOINT (required for every extension)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

```python
# routes.py
from sqlalchemy import func

@router.get("/stats")
async def get_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Count by status
    status_rows = await db.execute(
        select(Ticket.status, func.count(Ticket.id).label("count"))
        .where(Ticket.tenant_id == current_user.tenant_id)
        .group_by(Ticket.status)
    )
    by_status = {row.status: row.count for row in status_rows}
    total = sum(by_status.values())
    return {"total": total, "by_status": by_status}
```

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PATTERN 4 — STATUS WORKFLOW ENDPOINT (for anything with state transitions)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

```python
# routes.py
from pydantic import BaseModel as PM

class StatusUpdate(PM):
    status: str

@router.patch("/{item_id}/status", response_model=TicketResponse)
async def update_status(
    item_id: str,
    payload: StatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Ticket).where(Ticket.id == item_id, Ticket.tenant_id == current_user.tenant_id)
    )
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    ticket.status = payload.status
    # Track timestamp for terminal states
    if payload.status == "resolved":
        ticket.resolved_at = utcnow()
    elif payload.status == "closed":
        ticket.closed_at = utcnow()
    await db.commit()
    await db.refresh(ticket)
    return ticket
```

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PATTERN 5 — FINANCIAL FIELDS (for invoices, deals, expenses, billing)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

```python
# models.py
from sqlalchemy import Numeric

class Invoice(Base):
    # ...
    subtotal:    Mapped[float] = mapped_column(Numeric(12, 2), default=0.0, nullable=False)
    tax_rate:    Mapped[float] = mapped_column(Numeric(5, 2),  default=0.0, nullable=False)
    total:       Mapped[float] = mapped_column(Numeric(12, 2), default=0.0, nullable=False)
    currency:    Mapped[str]   = mapped_column(String(3), default="USD", nullable=False)
    paid_at:     Mapped[datetime|None] = mapped_column(SADateTime(timezone=True), nullable=True)

# routes.py — compute total on create/update
@router.post("/", response_model=InvoiceResponse, status_code=status.HTTP_201_CREATED)
async def create_invoice(payload: InvoiceCreate, ...):
    subtotal = sum(item.quantity * item.unit_price for item in payload.line_items)
    total    = round(subtotal * (1 + payload.tax_rate / 100), 2)
    invoice  = Invoice(subtotal=subtotal, total=total, ...)
```

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PATTERN 6 — RICH ui_spec.json (select fields with options, right fields in list)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

```json
{
  "label": "Tickets", "icon": "🎫", "color": "#f59e0b",
  "description": "Customer support ticket management.",
  "api_base": "/ticket-tracker",
  "resources": [{
    "key": "tickets", "label": "Tickets",
    "list": "GET /", "create": "POST /", "update": "PATCH /{id}", "delete": "DELETE /{id}",
    "id_field": "id", "empty_message": "No tickets yet. Create your first ticket!",
    "fields": [
      { "key": "title",         "label": "Title",       "type": "text",     "required": true,  "show_in_list": true  },
      { "key": "status",        "label": "Status",      "type": "select",   "required": false, "show_in_list": true,
        "options": ["open", "in_progress", "resolved", "closed"] },
      { "key": "priority",      "label": "Priority",    "type": "select",   "required": false, "show_in_list": true,
        "options": ["low", "medium", "high", "critical"] },
      { "key": "assignee_name", "label": "Assigned To", "type": "text",     "required": false, "show_in_list": true  },
      { "key": "requester_email","label": "Requester",  "type": "email",    "required": false, "show_in_list": false },
      { "key": "description",   "label": "Description", "type": "textarea", "required": false, "show_in_list": false },
      { "key": "due_date",      "label": "Due Date",    "type": "date",     "required": false, "show_in_list": true  },
      { "key": "created_at",    "label": "Created",     "type": "date",     "required": false, "show_in_list": false }
    ]
  }]
}
```
Key rules for ui_spec:
- "select" type MUST have "options" array matching the enum values exactly
- "show_in_list": true on 4-5 columns max — status, priority, key name, date
- Choose an emoji icon that matches the domain (🎫 tickets, 💰 invoicing, 📋 tasks, 👥 crm)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PATTERN 7 — SMART ORDERING (always order by what matters most)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

```python
# For tasks/tickets with priority + due_date:
q = q.order_by(Task.priority.desc(), Task.due_date.asc(), Task.created_at.desc())

# For financial records: newest first
q = q.order_by(Invoice.created_at.desc())

# For CRM deals: highest value first, then by stage
q = q.order_by(Deal.value.desc(), Deal.stage.asc())

# For inventory: low stock first (alert items)
q = q.order_by(Product.stock_quantity.asc(), Product.name.asc())

# For pinned items (booleans): pinned first, then newest
q = q.order_by(Note.is_pinned.desc(), Note.created_at.desc())
```

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PATTERN 8 — PARENT-CHILD WITH NESTED ROUTES (for multi-table extensions)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

```python
# routes.py — use mergeParams pattern with nested router
parent_router = APIRouter(tags=["projects"])
child_router  = APIRouter(tags=["tasks"])

# POST /projects/{project_id}/tasks/
@child_router.post("/", response_model=TaskResponse, status_code=201)
async def create_task(project_id: str, payload: TaskCreate, ...):
    # Verify project belongs to tenant first
    proj_result = await db.execute(
        select(Project).where(Project.id == project_id, Project.tenant_id == current_user.tenant_id)
    )
    project = proj_result.scalar_one_or_none()
    if not project:
        raise HTTPException(404, "Project not found")
    task = Task(project_id=project_id, tenant_id=current_user.tenant_id, ...)
    db.add(task); await db.commit(); await db.refresh(task); return task

# In extension.py on_activate — mount both routers:
app.include_router(parent_router, prefix=f"/api/v1{self.api_prefix}")
app.include_router(child_router,  prefix=f"/api/v1{self.api_prefix}/{{project_id}}/tasks")
```

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PATTERN 9 — PUBLIC ENDPOINTS (no JWT — for embeddable widgets, public APIs)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Use this when part of the API must be accessible without a user account — e.g.
an embedded chat widget, a public form submission endpoint, or a webhook receiver.
Auth is done via a `site_key` or `api_key` column in a config/site model.

```python
# models.py — Site/Widget config model with a secret key
import secrets as _secrets

class WidgetSite(Base):
    __tablename__ = "ext_widget_sites"
    id:         Mapped[str]  = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id:  Mapped[str]  = mapped_column(UUID(as_uuid=False), nullable=False, index=True)
    created_by: Mapped[str]  = mapped_column(UUID(as_uuid=False), nullable=False)
    created_at: Mapped[datetime] = mapped_column(SADateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(SADateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)
    name:       Mapped[str]  = mapped_column(String(255), nullable=False)
    site_key:   Mapped[str]  = mapped_column(String(64), nullable=False, unique=True, index=True)
    is_active:  Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

# routes.py — PUBLIC endpoint (NO Depends(get_current_user))
# The site_key in the URL path IS the authentication
@router.post("/public/{site_key}/submit")
async def public_submit(
    site_key: str,
    payload: PublicSubmitPayload,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    # Validate the site_key — this IS the auth check
    result = await db.execute(
        select(WidgetSite).where(WidgetSite.site_key == site_key, WidgetSite.is_active == True)
    )
    site = result.scalar_one_or_none()
    if not site:
        raise HTTPException(status_code=404, detail="Invalid site key")
    # Now use site.tenant_id for all DB operations (no current_user)
    record = MyModel(tenant_id=site.tenant_id, ...)
    db.add(record); await db.commit(); await db.refresh(record)
    return record

# Agent endpoints still use JWT — same router, different paths
@router.post("/sites", response_model=SiteResponse, status_code=201)
async def create_site(
    payload: SiteCreate,
    current_user: Annotated[User, Depends(get_current_user)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    import secrets
    site = WidgetSite(
        **payload.model_dump(),
        tenant_id=current_user.tenant_id,
        created_by=current_user.id,
        site_key=secrets.token_urlsafe(32),  # generate secure random key
    )
    db.add(site); await db.commit(); await db.refresh(site); return site
```

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PATTERN 10 — SERVING JAVASCRIPT / EMBED CODE FROM AN API ROUTE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Use this to serve an embeddable JavaScript widget via a GET route.
The JS is a Python string with placeholders substituted at request time.
CRITICAL: Use request headers to build an absolute URL so the script works
on ANY external website, not just on localhost.

```python
# routes.py
from fastapi import Request
from fastapi.responses import Response

WIDGET_JS = r"""
(function() {
  var API_BASE = '__API_BASE__';
  var SITE_KEY = '__SITE_KEY__';
  var COLOR    = '__COLOR__';
  // ... widget JavaScript here ...
  // All fetch() calls use absolute API_BASE URL, e.g.:
  fetch(API_BASE + '/conversations', { method: 'POST', ... })
})();
"""

@router.get("/widget/{site_key}/script.js", include_in_schema=False)
async def serve_widget_js(
    site_key: str,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    result = await db.execute(
        select(WidgetSite).where(WidgetSite.site_key == site_key, WidgetSite.is_active == True)
    )
    site = result.scalar_one_or_none()
    if not site:
        return Response("/* invalid site key */", media_type="application/javascript")

    # CRITICAL: use forwarded headers to get the real public domain (Nginx proxy)
    scheme = request.headers.get("x-forwarded-proto", request.url.scheme)
    host   = request.headers.get("host", request.url.netloc)
    api_base = f"{scheme}://{host}/api/v1/my-extension/public/{site_key}"

    js = WIDGET_JS \
        .replace("__API_BASE__", api_base) \
        .replace("__SITE_KEY__", site_key) \
        .replace("__COLOR__", site.color)

    return Response(js, media_type="application/javascript",
                    headers={"Cache-Control": "no-cache", "Access-Control-Allow-Origin": "*"})
```

The embed snippet users add to their website:
```html
<script src="https://yourdomain.com/api/v1/my-extension/widget/SITE_KEY/script.js" defer></script>
```

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PATTERN 11 — CORS FOR EMBEDDABLE / PUBLIC EXTENSIONS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

When an extension has PUBLIC endpoints (no JWT) that get called from external
websites (embedded widgets, forms, webhooks), you MUST note in your output that
main.py needs `allow_origins=["*"]` in CORSMiddleware.

Add this note at the END of your ✅ completion message:

```
⚠️ CORS NOTE: This extension serves a public widget API called from external websites.
The backend must allow cross-origin requests. In main.py, change:
  allow_origins=["http://localhost:3000", ...]
to:
  allow_origins=["*"],
  allow_credentials=False,
```
'''

# ─────────────────────────────────────────────────────────────────────────────
# CRITICAL RULES
# ─────────────────────────────────────────────────────────────────────────────

CRITICAL_RULES = '''
## CRITICAL RULES — follow every single one

### Imports — EXACTLY these, no variations:
```python
from api.database  import Base, get_db
from api.auth      import get_current_user
from api.models    import User
from saas_builder.core import ExtensionBase
```

### Models — REQUIRED columns on every model:
- Table name MUST start with `ext_`
- `id`: UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
- `tenant_id`: UUID(as_uuid=False), nullable=False, index=True
- `created_by`: UUID(as_uuid=False), nullable=False
- `created_at`: SADateTime(timezone=True), default=utcnow, nullable=False
- `updated_at`: SADateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False

### Models — field types:
- `String(255)` for short text, `Text` for long text
- `UUID(as_uuid=False)` for ALL UUID columns (stores as string, never Python UUID object)
- `JSON` for list fields, `Numeric(12,2)` for money, `Float` for ratios/rates
- `SAEnum(MyEnum)` for status/type/priority (NEVER raw String for these fields)
- `SADateTime(timezone=True)` for all datetime columns

### Routes:
- Every route: `Depends(get_current_user)` + `Depends(get_db)`
- ALWAYS filter by `tenant_id == current_user.tenant_id`
- Use `result.scalar_one_or_none()` then 404 if None
- `payload.model_dump(exclude_unset=True)` for PATCH
- `created_by = current_user.id` on create
- `status.HTTP_201_CREATED` for POST, `status.HTTP_204_NO_CONTENT` for DELETE

### Schemas:
- Response models: `class Config: from_attributes = True`
- Optional fields: `Optional[str] = None` (not `str | None`)
- Lists: `Field(default_factory=list)`
- String validation: `Field(..., min_length=1, max_length=255)`

### Extension.py:
- `name` = snake_case matching directory
- `api_prefix` = kebab-case e.g. `/ticket-tracker`
- `on_install`: `from . import models  # noqa: F401`
- `on_activate`: `app.include_router(router, prefix=f"/api/v1{self.api_prefix}")`

### ui_spec.json:
- `api_base` MUST exactly match `api_prefix`
- Routes RELATIVE to api_base: `"GET /"` not `"GET /tickets/"`
- `select` fields MUST include `"options": [...]` matching enum values
- `show_in_list: true` for 4-5 most useful columns only

### QUALITY CHECKLIST — every extension must have ALL of these:
☑ Enums (not plain strings) for every status/type/priority field
☑ List endpoint accepts `?status=` query param filter (if status field exists)
☑ Smart ordering in list query (by priority+date or value — not just created_at)
☑ A `/stats` GET endpoint returning counts by status and total
☑ ui_spec "select" fields with "options" arrays for all enum columns
☑ `due_date` field on any entity that has deadlines (tasks, invoices, tickets)
☑ `assignee_name` or `assigned_to` on any entity that can be assigned
☑ Complete, working code — zero TODOs, zero placeholders

### ⚠️ AUTOMATED VALIDATION — your code is checked before being written to disk:
- Python syntax errors → file NOT written, generation stops
- `eval()`, `exec()`, `compile()` in any file → blocked
- Table names NOT starting with `ext_` → blocked
- Missing `tenant_id` column in a model → blocked
- F-string SQL queries (SQL injection risk) → blocked
Write correct code the first time. The validator will catch any of these issues.
'''

# ─────────────────────────────────────────────────────────────────────────────
# DOMAIN DESIGN KNOWLEDGE — built-in product expertise per domain
# ─────────────────────────────────────────────────────────────────────────────

DESIGN_KNOWLEDGE = '''
## DOMAIN DESIGN KNOWLEDGE — build the COMPLETE version

You are a senior product engineer. Add ALL fields a real user would need on day one,
even if not mentioned. Build the complete production version, not a skeleton.

### CRM / Sales
Models: Contact (name, email, phone, company, position, tags, notes),
Deal (contact_id, title, value, currency, stage: lead/qualified/proposal/negotiation/won/lost,
close_date, notes, assigned_to)
Smart extras: stage as enum, deal value tracking, last_contacted_at, won/lost timestamps

### Invoicing / Billing
Models: Client (name, email, phone, billing_address, tax_id),
Invoice (client_id, invoice_number, status: draft/sent/paid/overdue, issue_date, due_date,
subtotal, tax_rate, total, currency, notes, paid_at),
LineItem (invoice_id, description, quantity, unit_price, amount)
Smart extras: computed total = subtotal × (1 + tax_rate/100), unique invoice_number,
mark-as-paid endpoint that sets paid_at

### Task / Project Management
Models: Project (name, description, status: active/on_hold/completed/archived, color, due_date),
Task (project_id, title, description, status: todo/in_progress/review/done,
priority: low/medium/high/urgent, due_date, assignee_name, estimated_hours, actual_hours)
Smart extras: ordering by priority desc + due_date, progress counts per project

### Help Desk / Support Tickets
Models: Ticket (title, description, status: open/in_progress/resolved/closed,
priority: low/medium/high/critical, category, requester_name, requester_email,
assigned_to, resolved_at, closed_at),
Reply (ticket_id, content, is_internal, author_name, author_email)
Smart extras: SLA awareness via priority+created_at, internal notes flag,
resolution time = resolved_at − created_at

### Blog / CMS
Models: Category (name, slug, description, color),
Post (category_id, title, slug, excerpt, content, status: draft/published/archived,
published_at, featured_image_url, tags, read_time_minutes, view_count)
Smart extras: scheduled publishing via published_at, auto read-time estimate,
slug as unique identifier

### Appointment / Booking
Models: Service (name, description, duration_minutes, price, color),
Client (name, email, phone, notes),
Appointment (service_id, client_id, start_time, end_time, status: scheduled/confirmed/
cancelled/completed, notes, price, cancellation_reason)
Smart extras: end_time computed from start_time + service.duration, price from service,
upcoming vs past filter

### Inventory / Products
Models: Category (name, description, color),
Product (category_id, sku, name, description, price, cost_price, stock_quantity,
low_stock_threshold, unit, status: active/inactive/discontinued, barcode)
Smart extras: low stock alert via stock_quantity <= low_stock_threshold,
margin = price − cost_price, unique SKU constraint

### HR / People Management
Models: Department (name, description),
Employee (department_id, first_name, last_name, email, phone, position,
employment_type: full_time/part_time/contract/intern,
status: active/on_leave/terminated, hire_date, salary, notes)
Smart extras: full_name as computed property, employment type enum,
years_of_service from hire_date

### Expense Tracking / Finance
Models: Category (name, color, budget_limit),
Expense (category_id, title, amount, currency, date, receipt_url,
status: pending/approved/rejected, notes, submitted_by_name, approved_by_name, approved_at)
Smart extras: approval workflow with approved_by + approved_at, budget vs actual per category,
currency support

### Lead / Contact Management
Models: Lead (name, email, phone, company, source: website/referral/ad/cold_outreach/other,
status: new/contacted/qualified/converted/lost, assigned_to, notes, last_contacted_at,
estimated_value, converted_at)
Smart extras: source + status as enums, conversion tracking, time-in-stage analytics

### Live Chat / Embeddable Chat Widget
Uses Pattern 9 (public endpoints) + Pattern 10 (JS file serving) + Pattern 11 (CORS note).
Models: Site (name, url, site_key, color, greeting, is_active, tenant_id, created_by),
Conversation (site_id FK, tenant_id, visitor_name, visitor_email, status: open/closed,
unread_count, message_count, last_message, last_message_at),
Message (conversation_id FK, tenant_id, content, sender: visitor/agent, sender_name, is_read)
Agent API (JWT): GET /sites, POST /sites, DELETE /sites/{id},
GET /conversations, GET /conversations/{id}/messages, POST /conversations/{id}/reply,
POST /conversations/{id}/mark-read (resets unread_count, marks all visitor messages is_read=True),
PATCH /conversations/{id} (status update), GET /stats
Widget API (NO JWT, site_key in path): POST /widget/{site_key}/conversations (start chat),
GET /widget/{site_key}/conversations/{id}/messages (poll for replies),
POST /widget/{site_key}/conversations/{id}/messages (visitor sends message — increments unread_count),
GET /widget/{site_key}/script.js (serves JavaScript with absolute URL from forwarded headers)
Smart extras: site_key = secrets.token_urlsafe(32), unread_count increments on visitor message
and resets on agent mark-read, message_count tracks total, last_message truncated to 200 chars,
widget JS uses polling every 3s (no WebSocket needed), visitor info stored in localStorage

### Form Builder / Public Form Submissions
Uses Pattern 9 (public endpoints) + Pattern 11 (CORS note).
Models: Form (name, description, status: draft/published, site_key, tenant_id, created_by),
FormField (form_id FK, label, field_type: text/email/number/textarea/select/checkbox,
is_required, options JSON, sort_order),
Submission (form_id FK, tenant_id, data JSON, visitor_ip, submitted_at)
Agent API (JWT): full CRUD on forms and fields, GET /forms/{id}/submissions
Public API (NO JWT): GET /public/{site_key} (get form schema),
POST /public/{site_key}/submit (save submission — uses site_key as auth, not JWT)
Smart extras: site_key = secrets.token_urlsafe(32), submission data stored as JSON blob,
visitor_ip from request.client.host

### ⚠️ WHEN THE EXTENSION NEEDS A CUSTOM UI
Some extensions need a custom React UI (real-time inbox, drag-and-drop, canvas, chat threads).
The GenericExtensionPage (ui_spec.json) only handles flat table + create/edit form.
If the extension needs something the generic page cannot do, STILL generate backend + ui_spec.json,
but add this note at the end BEFORE the ✅:

```
📌 CUSTOM UI NOTE: This extension needs a custom React component for the [describe feature].
The GenericExtensionPage (ui_spec.json) will show a basic table view which works for data management,
but for the full [feature] experience a LiveChatPage/KanbanPage style custom component is needed.
```
'''

# ─────────────────────────────────────────────────────────────────────────────
# RELATIONAL PATTERN
# ─────────────────────────────────────────────────────────────────────────────

RELATIONAL_PATTERN = '''
## RELATIONAL PATTERN — parent-child models

### models.py:
```python
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship

class Project(Base):
    __tablename__ = "ext_myext_projects"
    # ... standard columns ...
    tasks: Mapped[list["Task"]] = relationship(
        "Task", back_populates="project", cascade="all, delete-orphan", lazy="selectin"
    )

class Task(Base):
    __tablename__ = "ext_myext_tasks"
    project_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("ext_myext_projects.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    tenant_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False, index=True)
    project: Mapped["Project"] = relationship("Project", back_populates="tasks")
```

### routes.py — always verify parent belongs to tenant:
```python
proj = (await db.execute(
    select(Project).where(Project.id == project_id, Project.tenant_id == current_user.tenant_id)
)).scalar_one_or_none()
if not proj:
    raise HTTPException(404, "Project not found")
```

### ui_spec.json multiple resources (tabs):
```json
{
  "api_base": "/project-manager",
  "resources": [
    { "key": "projects", "label": "Projects", "list": "GET /projects/", ... },
    { "key": "tasks",    "label": "Tasks",    "list": "GET /tasks/",    ... }
  ]
}
```
'''

# ─────────────────────────────────────────────────────────────────────────────
# Sessions dir + context loader
# ─────────────────────────────────────────────────────────────────────────────

SESSIONS_DIR = "/home/chatwoot/saaskaran/ai_sessions"


def _load_session_context(extension_name: str) -> str:
    import os
    safe_name = extension_name.lower().replace(" ", "_")
    path = f"{SESSIONS_DIR}/{safe_name}.md"
    if os.path.exists(path):
        try:
            content = open(path, encoding="utf-8").read()
            return f"""
## PREVIOUS BUILD CONTEXT (from when this extension was first created)

Use this to understand the original requirements and design decisions so
your modifications are consistent with the original intent.

<session_context>
{content}
</session_context>
"""
        except Exception:
            pass
    return ""


# ─────────────────────────────────────────────────────────────────────────────
# Prompt builders
# ─────────────────────────────────────────────────────────────────────────────


def build_system_prompt(
    template: str,
    active_extensions: list[str],
    selected_extension: str | None = None,
) -> str:
    context = f"Project template: **{template}**."
    if active_extensions:
        context += f" Active extensions: {', '.join(active_extensions)}."

    # ── MODIFY MODE ──────────────────────────────────────────────────────────
    if selected_extension:
        session_context = _load_session_context(selected_extension)
        return f"""{AGENTIC_PREAMBLE}You are a senior full-stack engineer modifying the **{selected_extension}** extension.
{session_context}
{context}

## PROJECT STRUCTURE

```
/home/chatwoot/saaskaran/
  backend/
    extensions/{selected_extension}/   ← files you're modifying
    api/database.py                    ← Base, get_db
    api/auth.py                        ← get_current_user, hash_password
    api/models.py                      ← User, Tenant models
  frontend/
    components/extensions/             ← custom React UI components
    app/(dashboard)/extensions/[name]/page.tsx  ← register custom components here
```

## YOUR WORKFLOW

1. Read the existing extension files to understand what's there:
   - Read backend/extensions/{selected_extension}/models.py
   - Read backend/extensions/{selected_extension}/routes.py
   - Read any other relevant files
2. Make the requested changes — complete files, not diffs
3. Use the Write tool to save each changed file
4. If you wrote frontend files → run: `cd /home/chatwoot/saaskaran/frontend && npm run build && pm2 restart saaskaran-frontend`
5. When done: briefly say what you changed and end with ✅

## RULES

- Do NOT change `name = "{selected_extension}"` in extension.py
- Write COMPLETE files — never partial snippets
- Use Bash to run `npm run build` only if you actually wrote frontend files

{CRITICAL_RULES}

{ADVANCED_PATTERNS}

{RELATIONAL_PATTERN}
"""

    # ── CREATE MODE ──────────────────────────────────────────────────────────
    codebase_context = _load_actual_codebase()
    return f"""{AGENTIC_PREAMBLE}You are a senior full-stack engineer building a complete, production-ready SaaS extension.
{context}

{codebase_context}

## REQUIRED FILES — output ALL of these, in order

### Backend (always required):
1. `extensions/{{name}}/__init__.py`
2. `extensions/{{name}}/extension.py`
3. `extensions/{{name}}/models.py`
4. `extensions/{{name}}/schemas.py`
5. `extensions/{{name}}/routes.py`
6. `extensions/{{name}}/ui_spec.json`
7. `extensions/{{name}}/tests/__init__.py`
8. `extensions/{{name}}/tests/test_extension.py`

### Frontend (required when the extension needs a non-trivial UI):

The `GenericExtensionPage` (driven by ui_spec.json) renders a simple table+modal UI.
It is GOOD ENOUGH for most CRUD extensions (contacts, invoices, tasks, blog posts).

Build a CUSTOM React component ONLY when the extension genuinely needs:
- Real-time updates / polling (e.g. live chat, notifications inbox)
- Multi-pane layout (e.g. list + thread view, kanban board)
- Embed code generation / copy-to-clipboard flows
- Drag-and-drop interactions
- Complex wizards or multi-step forms

If a custom React component IS needed, write these TWO additional files:

9.  `frontend/components/extensions/{{PascalName}}Page.tsx`
10. `frontend/app/(dashboard)/extensions/[name]/page.tsx`  ← updated router

**For file 10, use this EXACT template, adding your import and entry:**

[WRITE_FILE: frontend/app/(dashboard)/extensions/[name]/page.tsx]
'use client'

import Link from 'next/link'
import {{ useState, useEffect }} from 'react'
import TodoListPage from '@/components/extensions/TodoListPage'
import KanbanBoardPage from '@/components/extensions/KanbanBoardPage'
import FormBuilderPage from '@/components/extensions/FormBuilderPage'
import LiveChatPage from '@/components/extensions/LiveChatPage'
import {{PascalName}}Page from '@/components/extensions/{{PascalName}}Page'
import GenericExtensionPage from '@/components/extensions/GenericExtensionPage'

const EXTENSION_PAGES: Record<string, React.ComponentType> = {{
  todo_list: TodoListPage,
  kanban_board: KanbanBoardPage,
  form_builder: FormBuilderPage,
  live_chat: LiveChatPage,
  {{snake_name}}: {{PascalName}}Page,
}}

function DynamicOrFallback({{ name }}: {{ name: string }}) {{
  const [hasSpec, setHasSpec] = useState<boolean | null>(null)
  useEffect(() => {{
    const token = localStorage.getItem('token')
    fetch(`/api/v1/extensions/${{name}}/ui-spec`, {{
      headers: token ? {{ Authorization: `Bearer ${{token}}` }} : {{}},
    }}).then(r => setHasSpec(r.ok)).catch(() => setHasSpec(false))
  }}, [name])
  if (hasSpec === null) return <div className="p-8 text-slate-500 text-sm">Loading…</div>
  if (hasSpec) return <GenericExtensionPage extensionName={{name}} />
  return (
    <div className="flex flex-col items-center justify-center h-full text-center p-8">
      <div className="text-5xl mb-4">⬡</div>
      <h2 className="text-xl font-semibold text-white mb-2 capitalize">{{name.replace(/_/g, ' ')}}</h2>
      <p className="text-slate-400 mb-6 max-w-md">
        This extension has a backend API but no UI page yet. Go to the{{' '}}
        <Link href="/ai" className="text-indigo-400 hover:text-indigo-300">AI Builder</Link>
        , select this extension in the dropdown, and ask it to add a UI.
      </p>
      <Link href="/extensions" className="text-sm text-slate-500 hover:text-white transition">← Back to Extensions</Link>
    </div>
  )
}}

export default function ExtensionPage({{ params }}: {{ params: {{ name: string }} }}) {{
  const {{ name }} = params
  const PageComponent = EXTENSION_PAGES[name]
  if (PageComponent) return <PageComponent />
  return <DynamicOrFallback name={{name}} />
}}
[/WRITE_FILE]

**For custom React components (file 9), follow these rules:**
- `'use client'` at top
- Use `useState`, `useEffect` from react (already imported)
- API calls: `fetch('/api/v1/{{api_prefix}}/...', {{ headers: {{ Authorization: 'Bearer ' + localStorage.getItem('token') }} }})`
- Styling: Tailwind CSS only. Dark theme: bg-slate-800/900, text-white/slate-300/400, border-slate-700
- Polling: `setInterval(loadData, 5000)` in useEffect, clear in cleanup
- No external libraries (no axios, react-query, etc.)
- Export as `export default function {{PascalName}}Page()`

## NAMING CONVENTIONS

- Extension directory: `snake_case` → e.g. `ticket_tracker`
- `api_prefix` in extension.py: `/kebab-case` → e.g. `/ticket-tracker`
- `api_base` in ui_spec.json: same as api_prefix
- DB tables: `ext_` prefix → e.g. `ext_tickets`
- React component file: `PascalCase` → e.g. `TicketTrackerPage.tsx`

## HOW TO WORK

1. State your plan in 1-2 lines (extension name, tables, whether custom UI is needed)
2. Output ALL files immediately — no gaps, no pausing
3. End with ✅ Extension **name** generated — activating now...

{CRITICAL_RULES}

{ADVANCED_PATTERNS}

{DESIGN_KNOWLEDGE}

{RELATIONAL_PATTERN}
"""
