"""Audit Log — SQLAlchemy models."""
from __future__ import annotations
import uuid
from datetime import UTC, datetime
from sqlalchemy import String
from sqlalchemy import DateTime as SADateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column
from api.database import Base


def utcnow() -> datetime:
    return datetime.now(UTC)


class AuditEntry(Base):
    __tablename__ = "ext_audit_log_entries"

    id:            Mapped[str]      = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id:     Mapped[str]      = mapped_column(UUID(as_uuid=False), nullable=False, index=True)
    user_id:       Mapped[str|None] = mapped_column(UUID(as_uuid=False), nullable=True)
    action:        Mapped[str]      = mapped_column(String(100), nullable=False)   # e.g. "create", "update", "delete"
    resource_type: Mapped[str]      = mapped_column(String(100), nullable=False)   # e.g. "invoice", "contact"
    resource_id:   Mapped[str|None] = mapped_column(String(255), nullable=True)
    metadata:      Mapped[dict]     = mapped_column(JSONB, default=dict, nullable=False)
    ip_address:    Mapped[str|None] = mapped_column(String(50), nullable=True)
    created_at:    Mapped[datetime] = mapped_column(SADateTime(timezone=True), default=utcnow, nullable=False, index=True)
