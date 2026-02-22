"""Todo List Extension — Pydantic schemas."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from .models import ActivityActionEnum, PriorityEnum, RecurrenceEnum


# ---------------------------------------------------------------------------
# Category
# ---------------------------------------------------------------------------

class CategoryCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    color: str = Field(default="#6366f1", pattern=r"^#[0-9a-fA-F]{6}$")


class CategoryUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    color: Optional[str] = Field(None, pattern=r"^#[0-9a-fA-F]{6}$")


class CategoryResponse(BaseModel):
    id: str
    tenant_id: str
    name: str
    color: str
    created_by: str
    created_at: datetime

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# Subtask
# ---------------------------------------------------------------------------

class SubtaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    order: int = Field(default=0, ge=0)


class SubtaskUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    is_completed: Optional[bool] = None
    order: Optional[int] = Field(None, ge=0)


class SubtaskResponse(BaseModel):
    id: str
    todo_id: str
    title: str
    is_completed: bool
    order: int
    created_at: datetime

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# Comment
# ---------------------------------------------------------------------------

class CommentCreate(BaseModel):
    body: str = Field(..., min_length=1, max_length=5000)


class CommentUpdate(BaseModel):
    body: str = Field(..., min_length=1, max_length=5000)


class CommentResponse(BaseModel):
    id: str
    todo_id: str
    body: str
    created_by: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# Activity Log
# ---------------------------------------------------------------------------

class ActivityLogResponse(BaseModel):
    id: str
    todo_id: str
    action: ActivityActionEnum
    actor_id: str
    detail: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# Todo
# ---------------------------------------------------------------------------

class TodoCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    priority: PriorityEnum = PriorityEnum.medium
    due_date: Optional[datetime] = None
    recurrence: RecurrenceEnum = RecurrenceEnum.none
    category_id: Optional[str] = None
    subtasks: list[SubtaskCreate] = Field(default_factory=list)


class TodoUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    priority: Optional[PriorityEnum] = None
    due_date: Optional[datetime] = None
    recurrence: Optional[RecurrenceEnum] = None
    category_id: Optional[str] = None


class TodoResponse(BaseModel):
    id: str
    tenant_id: str
    title: str
    description: Optional[str]
    is_completed: bool
    priority: PriorityEnum
    due_date: Optional[datetime]
    completed_at: Optional[datetime]
    recurrence: RecurrenceEnum
    next_occurrence: Optional[datetime]
    category_id: Optional[str]
    category: Optional[CategoryResponse]
    progress: float
    created_by: str
    created_at: datetime
    updated_at: datetime
    subtasks: list[SubtaskResponse] = []
    comments: list[CommentResponse] = []
    activity_logs: list[ActivityLogResponse] = []

    class Config:
        from_attributes = True
