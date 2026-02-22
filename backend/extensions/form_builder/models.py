"""Form Builder — SQLAlchemy models."""
from __future__ import annotations
import uuid
from datetime import UTC, datetime
from sqlalchemy import String, Text, Integer, Boolean, ForeignKey, JSON
from sqlalchemy import DateTime as SADateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column
from api.database import Base


def utcnow() -> datetime:
    return datetime.now(UTC)


class Form(Base):
    __tablename__ = "ext_form_builder_forms"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    tenant_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False, index=True)
    created_by: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    fields: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    submit_button_text: Mapped[str] = mapped_column(String(100), default="Submit", nullable=False)
    success_message: Mapped[str] = mapped_column(
        String(500), default="Thank you for your submission!", nullable=False
    )
    embed_token: Mapped[str] = mapped_column(
        UUID(as_uuid=False), unique=True, nullable=False, index=True,
        default=lambda: str(uuid.uuid4())
    )
    submission_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(SADateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        SADateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )


class FormSubmission(Base):
    __tablename__ = "ext_form_builder_submissions"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    tenant_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False, index=True)
    form_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("ext_form_builder_forms.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    created_by: Mapped[str] = mapped_column(String(100), default="anonymous", nullable=False)
    data: Mapped[dict] = mapped_column(JSONB, nullable=False)
    ip_address: Mapped[str | None] = mapped_column(String(50), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(SADateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        SADateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )
