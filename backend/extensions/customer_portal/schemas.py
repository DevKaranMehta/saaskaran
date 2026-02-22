"""Customer Portal — Pydantic schemas."""
from __future__ import annotations
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from .models import TicketStatus, TicketPriority, TicketCategory


# ── Ticket ────────────────────────────────────────────────────────────────────

class TicketCreate(BaseModel):
    title:          str            = Field(..., min_length=1, max_length=255)
    description:    str            = Field(..., min_length=1)
    customer_name:  str            = Field(..., min_length=1, max_length=255)
    customer_email: str            = Field(..., min_length=1, max_length=255)
    priority:       TicketPriority = TicketPriority.medium
    category:       TicketCategory = TicketCategory.general
    assigned_to:    Optional[str]  = None


class TicketUpdate(BaseModel):
    title:       Optional[str]            = None
    description: Optional[str]            = None
    status:      Optional[TicketStatus]   = None
    priority:    Optional[TicketPriority] = None
    category:    Optional[TicketCategory] = None
    assigned_to: Optional[str]            = None


class TicketResponse(BaseModel):
    id:             str
    tenant_id:      str
    created_by:     str
    created_at:     datetime
    updated_at:     datetime
    title:          str
    description:    str
    customer_name:  str
    customer_email: str
    status:         TicketStatus
    priority:       TicketPriority
    category:       TicketCategory
    assigned_to:    Optional[str]
    reply_count:    int
    resolved_at:    Optional[datetime]

    class Config:
        from_attributes = True


# ── Reply ─────────────────────────────────────────────────────────────────────

class ReplyCreate(BaseModel):
    content:     str  = Field(..., min_length=1)
    author_name: str  = Field(..., min_length=1, max_length=255)
    is_agent:    bool = True


class ReplyResponse(BaseModel):
    id:          str
    ticket_id:   str
    tenant_id:   str
    created_by:  str
    created_at:  datetime
    content:     str
    author_name: str
    is_agent:    bool

    class Config:
        from_attributes = True


# ── Stats ─────────────────────────────────────────────────────────────────────

class TicketStats(BaseModel):
    total:            int
    by_status:        dict[str, int]
    by_priority:      dict[str, int]
    by_category:      dict[str, int]
    open_urgent:      int
    avg_reply_count:  float
