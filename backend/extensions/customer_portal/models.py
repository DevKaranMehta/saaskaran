"""Customer Portal — SQLAlchemy models."""
from __future__ import annotations
import uuid
import enum
from datetime import UTC, datetime
from typing import Optional
from sqlalchemy import String, Text, Integer, Boolean, ForeignKey
from sqlalchemy import DateTime as SADateTime
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from api.database import Base


def utcnow() -> datetime:
    return datetime.now(UTC)


class TicketStatus(str, enum.Enum):
    open        = "open"
    in_progress = "in_progress"
    resolved    = "resolved"
    closed      = "closed"


class TicketPriority(str, enum.Enum):
    low    = "low"
    medium = "medium"
    high   = "high"
    urgent = "urgent"


class TicketCategory(str, enum.Enum):
    billing         = "billing"
    technical       = "technical"
    general         = "general"
    feature_request = "feature_request"


class Ticket(Base):
    __tablename__ = "ext_customer_tickets"

    id:             Mapped[str]                = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id:      Mapped[str]                = mapped_column(UUID(as_uuid=False), nullable=False, index=True)
    created_by:     Mapped[str]                = mapped_column(UUID(as_uuid=False), nullable=False)
    created_at:     Mapped[datetime]           = mapped_column(SADateTime(timezone=True), default=utcnow, nullable=False)
    updated_at:     Mapped[datetime]           = mapped_column(SADateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)
    title:          Mapped[str]                = mapped_column(String(255), nullable=False)
    description:    Mapped[str]                = mapped_column(Text, nullable=False)
    customer_name:  Mapped[str]                = mapped_column(String(255), nullable=False)
    customer_email: Mapped[str]                = mapped_column(String(255), nullable=False, index=True)
    status:         Mapped[TicketStatus]       = mapped_column(SAEnum(TicketStatus), default=TicketStatus.open, nullable=False, index=True)
    priority:       Mapped[TicketPriority]     = mapped_column(SAEnum(TicketPriority), default=TicketPriority.medium, nullable=False, index=True)
    category:       Mapped[TicketCategory]     = mapped_column(SAEnum(TicketCategory), default=TicketCategory.general, nullable=False)
    assigned_to:    Mapped[Optional[str]]      = mapped_column(String(255), nullable=True)
    reply_count:    Mapped[int]                = mapped_column(Integer, default=0, nullable=False)
    resolved_at:    Mapped[Optional[datetime]] = mapped_column(SADateTime(timezone=True), nullable=True)


class TicketReply(Base):
    __tablename__ = "ext_ticket_replies"

    id:          Mapped[str]      = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id:   Mapped[str]      = mapped_column(UUID(as_uuid=False), nullable=False, index=True)
    created_by:  Mapped[str]      = mapped_column(UUID(as_uuid=False), nullable=False)
    created_at:  Mapped[datetime] = mapped_column(SADateTime(timezone=True), default=utcnow, nullable=False)
    updated_at:  Mapped[datetime] = mapped_column(SADateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)
    ticket_id:   Mapped[str]      = mapped_column(UUID(as_uuid=False), ForeignKey("ext_customer_tickets.id", ondelete="CASCADE"), nullable=False, index=True)
    content:     Mapped[str]      = mapped_column(Text, nullable=False)
    author_name: Mapped[str]      = mapped_column(String(255), nullable=False)
    is_agent:    Mapped[bool]     = mapped_column(Boolean, default=True, nullable=False)
