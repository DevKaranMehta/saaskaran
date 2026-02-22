"""Todo List Extension — SQLAlchemy models."""
from __future__ import annotations

import enum
import uuid
from datetime import UTC, datetime

from sqlalchemy import (
    Boolean,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy import DateTime as SADateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.database import Base


def utcnow() -> datetime:
    return datetime.now(UTC)


class PriorityEnum(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"


class RecurrenceEnum(str, enum.Enum):
    none = "none"
    daily = "daily"
    weekly = "weekly"
    monthly = "monthly"


class ActivityActionEnum(str, enum.Enum):
    created = "created"
    updated = "updated"
    completed = "completed"
    reopened = "reopened"
    subtask_added = "subtask_added"
    subtask_completed = "subtask_completed"
    comment_added = "comment_added"
    category_changed = "category_changed"


# ---------------------------------------------------------------------------
# Category
# ---------------------------------------------------------------------------

class TodoCategory(Base):
    __tablename__ = "ext_todo_categories"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    tenant_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    color: Mapped[str] = mapped_column(String(7), nullable=False, default="#6366f1")
    created_by: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False)
    created_at: Mapped[datetime] = mapped_column(SADateTime(timezone=True), default=utcnow, nullable=False)

    todos: Mapped[list["Todo"]] = relationship("Todo", back_populates="category", lazy="selectin")


# ---------------------------------------------------------------------------
# Todo
# ---------------------------------------------------------------------------

class Todo(Base):
    __tablename__ = "ext_todos"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    tenant_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    priority: Mapped[PriorityEnum] = mapped_column(
        Enum(PriorityEnum), default=PriorityEnum.medium, nullable=False
    )
    due_date: Mapped[datetime | None] = mapped_column(SADateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(SADateTime(timezone=True), nullable=True)

    # Recurrence
    recurrence: Mapped[RecurrenceEnum] = mapped_column(
        Enum(RecurrenceEnum), default=RecurrenceEnum.none, nullable=False
    )
    next_occurrence: Mapped[datetime | None] = mapped_column(SADateTime(timezone=True), nullable=True)

    # Category FK (optional)
    category_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("ext_todo_categories.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Progress (0.0 – 100.0), auto-managed by routes
    progress: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    created_by: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False)
    created_at: Mapped[datetime] = mapped_column(SADateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        SADateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )

    category: Mapped["TodoCategory | None"] = relationship(
        "TodoCategory", back_populates="todos", lazy="selectin"
    )
    subtasks: Mapped[list["TodoSubtask"]] = relationship(
        "TodoSubtask", back_populates="todo", cascade="all, delete-orphan", lazy="selectin"
    )
    comments: Mapped[list["TodoComment"]] = relationship(
        "TodoComment", back_populates="todo", cascade="all, delete-orphan", lazy="selectin"
    )
    activity_logs: Mapped[list["TodoActivityLog"]] = relationship(
        "TodoActivityLog", back_populates="todo", cascade="all, delete-orphan", lazy="selectin"
    )


# ---------------------------------------------------------------------------
# Subtask
# ---------------------------------------------------------------------------

class TodoSubtask(Base):
    __tablename__ = "ext_todo_subtasks"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    tenant_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False, index=True)
    todo_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("ext_todos.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(SADateTime(timezone=True), default=utcnow, nullable=False)

    todo: Mapped["Todo"] = relationship("Todo", back_populates="subtasks")


# ---------------------------------------------------------------------------
# Comment
# ---------------------------------------------------------------------------

class TodoComment(Base):
    __tablename__ = "ext_todo_comments"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    tenant_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False, index=True)
    todo_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("ext_todos.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    body: Mapped[str] = mapped_column(Text, nullable=False)
    created_by: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False)
    created_at: Mapped[datetime] = mapped_column(SADateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        SADateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )

    todo: Mapped["Todo"] = relationship("Todo", back_populates="comments")


# ---------------------------------------------------------------------------
# Activity Log
# ---------------------------------------------------------------------------

class TodoActivityLog(Base):
    __tablename__ = "ext_todo_activity_logs"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    tenant_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False, index=True)
    todo_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("ext_todos.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    action: Mapped[ActivityActionEnum] = mapped_column(Enum(ActivityActionEnum), nullable=False)
    actor_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False)
    detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(SADateTime(timezone=True), default=utcnow, nullable=False)

    todo: Mapped["Todo"] = relationship("Todo", back_populates="activity_logs")
