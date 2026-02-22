"""Billing — SQLAlchemy models."""
from __future__ import annotations
import uuid
from datetime import UTC, datetime
from sqlalchemy import Boolean, Numeric, String, Text
from sqlalchemy import DateTime as SADateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column
from api.database import Base


def utcnow() -> datetime:
    return datetime.now(UTC)


class Plan(Base):
    __tablename__ = "ext_billing_plans"

    id:          Mapped[str]        = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    name:        Mapped[str]        = mapped_column(String(100), nullable=False)
    description: Mapped[str|None]   = mapped_column(Text, nullable=True)
    price:       Mapped[float]      = mapped_column(Numeric(10, 2), nullable=False, default=0)
    currency:    Mapped[str]        = mapped_column(String(10), default="USD", nullable=False)
    interval:    Mapped[str]        = mapped_column(String(20), default="month", nullable=False)  # month, year
    features:    Mapped[list]       = mapped_column(JSONB, default=list, nullable=False)
    is_active:   Mapped[bool]       = mapped_column(Boolean, default=True, nullable=False)
    created_at:  Mapped[datetime]   = mapped_column(SADateTime(timezone=True), default=utcnow, nullable=False)


class Subscription(Base):
    __tablename__ = "ext_billing_subscriptions"

    id:         Mapped[str]      = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id:  Mapped[str]      = mapped_column(UUID(as_uuid=False), nullable=False, index=True)
    plan_id:    Mapped[str|None] = mapped_column(UUID(as_uuid=False), nullable=True)
    status:     Mapped[str]      = mapped_column(String(30), default="trial", nullable=False)  # trial, active, cancelled, expired
    started_at: Mapped[datetime] = mapped_column(SADateTime(timezone=True), default=utcnow, nullable=False)
    ends_at:    Mapped[datetime|None] = mapped_column(SADateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(SADateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(SADateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)
