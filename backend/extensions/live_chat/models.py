"""Live Chat — SQLAlchemy models."""
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


class ConvStatus(str, enum.Enum):
    open    = "open"
    closed  = "closed"


class MsgSender(str, enum.Enum):
    visitor = "visitor"
    agent   = "agent"


class LiveChatSite(Base):
    __tablename__ = "ext_lc_sites"

    id:         Mapped[str]      = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id:  Mapped[str]      = mapped_column(UUID(as_uuid=False), nullable=False, index=True)
    created_by: Mapped[str]      = mapped_column(UUID(as_uuid=False), nullable=False)
    created_at: Mapped[datetime] = mapped_column(SADateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(SADateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)
    name:       Mapped[str]      = mapped_column(String(255), nullable=False)
    url:        Mapped[str]      = mapped_column(String(500), nullable=False)
    site_key:   Mapped[str]      = mapped_column(String(64), nullable=False, unique=True, index=True)
    color:      Mapped[str]      = mapped_column(String(20), default="#6366f1", nullable=False)
    greeting:   Mapped[str]      = mapped_column(Text, default="Hi! How can we help you today?", nullable=False)
    is_active:  Mapped[bool]     = mapped_column(Boolean, default=True, nullable=False)


class LiveChatConversation(Base):
    __tablename__ = "ext_lc_conversations"

    id:              Mapped[str]           = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id:       Mapped[str]           = mapped_column(UUID(as_uuid=False), nullable=False, index=True)
    site_id:         Mapped[str]           = mapped_column(UUID(as_uuid=False), ForeignKey("ext_lc_sites.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at:      Mapped[datetime]      = mapped_column(SADateTime(timezone=True), default=utcnow, nullable=False)
    updated_at:      Mapped[datetime]      = mapped_column(SADateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)
    visitor_name:    Mapped[str]           = mapped_column(String(255), nullable=False)
    visitor_email:   Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    status:          Mapped[ConvStatus]    = mapped_column(SAEnum(ConvStatus), default=ConvStatus.open, nullable=False, index=True)
    message_count:   Mapped[int]           = mapped_column(Integer, default=0, nullable=False)
    unread_count:    Mapped[int]           = mapped_column(Integer, default=0, nullable=False)
    last_message:    Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    last_message_at: Mapped[Optional[datetime]] = mapped_column(SADateTime(timezone=True), nullable=True)
    assigned_to:     Mapped[Optional[str]] = mapped_column(String(255), nullable=True)


class LiveChatMessage(Base):
    __tablename__ = "ext_lc_messages"

    id:              Mapped[str]       = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id:       Mapped[str]       = mapped_column(UUID(as_uuid=False), nullable=False, index=True)
    conversation_id: Mapped[str]       = mapped_column(UUID(as_uuid=False), ForeignKey("ext_lc_conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at:      Mapped[datetime]  = mapped_column(SADateTime(timezone=True), default=utcnow, nullable=False)
    content:         Mapped[str]       = mapped_column(Text, nullable=False)
    sender:          Mapped[MsgSender] = mapped_column(SAEnum(MsgSender), nullable=False)
    sender_name:     Mapped[str]       = mapped_column(String(255), nullable=False)
    is_read:         Mapped[bool]      = mapped_column(Boolean, default=False, nullable=False)
