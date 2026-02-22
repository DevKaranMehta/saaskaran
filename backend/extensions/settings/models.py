"""Settings — SQLAlchemy models."""
from __future__ import annotations
import uuid
from datetime import UTC, datetime
from sqlalchemy import String, Text, UniqueConstraint
from sqlalchemy import DateTime as SADateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from api.database import Base


def utcnow() -> datetime:
    return datetime.now(UTC)


class WorkspaceSetting(Base):
    __tablename__ = "ext_settings_entries"
    __table_args__ = (UniqueConstraint("tenant_id", "key", name="uq_settings_tenant_key"),)

    id:         Mapped[str]      = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id:  Mapped[str]      = mapped_column(UUID(as_uuid=False), nullable=False, index=True)
    key:        Mapped[str]      = mapped_column(String(100), nullable=False)
    value:      Mapped[str|None] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(SADateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)
