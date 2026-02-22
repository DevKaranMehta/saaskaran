"""Kanban Board — Pydantic schemas."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from .models import CardStatus, Priority


# ── Board schemas ─────────────────────────────────────────────────────────────

class BoardCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None


class BoardUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None


class BoardResponse(BaseModel):
    id: str
    tenant_id: str
    name: str
    description: Optional[str]
    created_by: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ── Card schemas ──────────────────────────────────────────────────────────────

class CardCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    status: CardStatus = CardStatus.todo
    priority: Priority = Priority.medium
    due_date: Optional[datetime] = None
    position: int = 0
    tags: list[str] = Field(default_factory=list)
    assigned_to: Optional[str] = None


class CardUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    status: Optional[CardStatus] = None
    priority: Optional[Priority] = None
    due_date: Optional[datetime] = None
    position: Optional[int] = None
    tags: Optional[list[str]] = None
    assigned_to: Optional[str] = None


class CardResponse(BaseModel):
    id: str
    board_id: str
    tenant_id: str
    title: str
    description: Optional[str]
    status: CardStatus
    priority: Priority
    due_date: Optional[datetime]
    position: int
    tags: list[str]
    assigned_to: Optional[str]
    created_by: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
