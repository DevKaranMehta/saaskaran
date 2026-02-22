"""Marketplace — SQLAlchemy models."""
from __future__ import annotations
import uuid
from datetime import UTC, datetime
from sqlalchemy import Boolean, Integer, Numeric, String, Text
from sqlalchemy import DateTime as SADateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column
from api.database import Base


def utcnow() -> datetime:
    return datetime.now(UTC)


class MarketplaceListing(Base):
    __tablename__ = "ext_marketplace_listings"

    id:             Mapped[str]      = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id:      Mapped[str]      = mapped_column(UUID(as_uuid=False), nullable=False, index=True)  # publisher
    name:           Mapped[str]      = mapped_column(String(100), nullable=False)
    display_name:   Mapped[str]      = mapped_column(String(200), nullable=False)
    description:    Mapped[str|None] = mapped_column(Text, nullable=True)
    version:        Mapped[str]      = mapped_column(String(20), default="1.0.0", nullable=False)
    author:         Mapped[str]      = mapped_column(String(100), nullable=False)
    price:          Mapped[float]    = mapped_column(Numeric(10, 2), default=0, nullable=False)
    tags:           Mapped[list]     = mapped_column(JSONB, default=list, nullable=False)
    download_count: Mapped[int]      = mapped_column(Integer, default=0, nullable=False)
    is_approved:    Mapped[bool]     = mapped_column(Boolean, default=False, nullable=False)
    is_active:      Mapped[bool]     = mapped_column(Boolean, default=True, nullable=False)
    created_at:     Mapped[datetime] = mapped_column(SADateTime(timezone=True), default=utcnow, nullable=False)
    updated_at:     Mapped[datetime] = mapped_column(SADateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)
