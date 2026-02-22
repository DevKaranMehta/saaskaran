"""Kanban Board — SQLAlchemy models."""
from __future__ import annotations

import enum
import uuid
from datetime import UTC, datetime

from sqlalchemy import Enum, ForeignKey, Integer, JSON, String, Text
from sqlalchemy import DateTime as SADateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.database import Base


def utcnow() -> datetime:
    return datetime.now(UTC)


class CardStatus(str, enum.Enum):
    backlog = "backlog"
    todo = "todo"
    in_progress = "in_progress"
    review = "review"
    done = "done"


class Priority(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"


class KanbanBoard(Base):
    __tablename__ = "ext_kanban_boards"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    tenant_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        SADateTime(timezone=True), default=utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        SADateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )

    cards: Mapped[list["KanbanCard"]] = relationship(
        "KanbanCard", back_populates="board", cascade="all, delete-orphan", lazy="selectin"
    )


class KanbanCard(Base):
    __tablename__ = "ext_kanban_cards"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    board_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("ext_kanban_boards.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    tenant_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[CardStatus] = mapped_column(
        Enum(CardStatus), default=CardStatus.todo, nullable=False, index=True
    )
    priority: Mapped[Priority] = mapped_column(
        Enum(Priority), default=Priority.medium, nullable=False
    )
    due_date: Mapped[datetime | None] = mapped_column(SADateTime(timezone=True), nullable=True)
    position: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    tags: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    assigned_to: Mapped[str | None] = mapped_column(UUID(as_uuid=False), nullable=True)
    created_by: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        SADateTime(timezone=True), default=utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        SADateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )

    board: Mapped["KanbanBoard"] = relationship("KanbanBoard", back_populates="cards")
