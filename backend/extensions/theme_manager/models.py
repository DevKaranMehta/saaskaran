"""Theme Manager — SQLAlchemy models."""
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


class ThemeConfig(Base):
    __tablename__ = "ext_themes_config"

    id:            Mapped[str]      = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id:     Mapped[str]      = mapped_column(UUID(as_uuid=False), nullable=False, unique=True, index=True)
    theme_name:    Mapped[str]      = mapped_column(String(50), default="dark", nullable=False)
    primary_color: Mapped[str]      = mapped_column(String(20), default="#6366f1", nullable=False)
    logo_url:      Mapped[str|None] = mapped_column(String(500), nullable=True)
    config:        Mapped[dict]     = mapped_column(JSONB, default=dict, nullable=False)
    updated_at:    Mapped[datetime] = mapped_column(SADateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)
