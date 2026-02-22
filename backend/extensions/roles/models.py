"""Roles — SQLAlchemy models."""
from __future__ import annotations
import uuid
from datetime import UTC, datetime
from sqlalchemy import Boolean, String, Text
from sqlalchemy import DateTime as SADateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column
from api.database import Base


def utcnow() -> datetime:
    return datetime.now(UTC)


class Role(Base):
    __tablename__ = "ext_roles_roles"

    id:          Mapped[str]      = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id:   Mapped[str]      = mapped_column(UUID(as_uuid=False), nullable=False, index=True)
    name:        Mapped[str]      = mapped_column(String(100), nullable=False)
    description: Mapped[str|None] = mapped_column(Text, nullable=True)
    permissions: Mapped[list]     = mapped_column(JSONB, default=list, nullable=False)
    is_default:  Mapped[bool]     = mapped_column(Boolean, default=False, nullable=False)
    created_at:  Mapped[datetime] = mapped_column(SADateTime(timezone=True), default=utcnow, nullable=False)
    updated_at:  Mapped[datetime] = mapped_column(SADateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)
