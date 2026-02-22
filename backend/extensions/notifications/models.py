"""Notifications — SQLAlchemy models."""
from __future__ import annotations
import uuid
from datetime import UTC, datetime
from sqlalchemy import Boolean, String, Text
from sqlalchemy import DateTime as SADateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from api.database import Base


def utcnow() -> datetime:
    return datetime.now(UTC)


class Notification(Base):
    __tablename__ = "ext_notifications_items"

    id:         Mapped[str]      = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id:  Mapped[str]      = mapped_column(UUID(as_uuid=False), nullable=False, index=True)
    user_id:    Mapped[str|None] = mapped_column(UUID(as_uuid=False), nullable=True, index=True)  # None = broadcast
    title:      Mapped[str]      = mapped_column(String(255), nullable=False)
    message:    Mapped[str|None] = mapped_column(Text, nullable=True)
    link:       Mapped[str|None] = mapped_column(String(500), nullable=True)
    is_read:    Mapped[bool]     = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(SADateTime(timezone=True), default=utcnow, nullable=False, index=True)
