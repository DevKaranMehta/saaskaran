"""Invoicing — SQLAlchemy models."""
from __future__ import annotations
import enum
import uuid
from datetime import UTC, datetime
from sqlalchemy import Date, Enum as SAEnum, ForeignKey, Numeric, String, Text
from sqlalchemy import DateTime as SADateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from api.database import Base


def utcnow() -> datetime:
    return datetime.now(UTC)


class InvoiceStatus(str, enum.Enum):
    draft     = "draft"
    sent      = "sent"
    paid      = "paid"
    overdue   = "overdue"
    cancelled = "cancelled"


class Client(Base):
    __tablename__ = "ext_inv_clients"

    id:              Mapped[str]       = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id:       Mapped[str]       = mapped_column(UUID(as_uuid=False), nullable=False, index=True)
    name:            Mapped[str]       = mapped_column(String(255), nullable=False)
    email:           Mapped[str|None]  = mapped_column(String(255), nullable=True)
    phone:           Mapped[str|None]  = mapped_column(String(50),  nullable=True)
    company:         Mapped[str|None]  = mapped_column(String(255), nullable=True)
    billing_address: Mapped[str|None]  = mapped_column(Text, nullable=True)
    tax_id:          Mapped[str|None]  = mapped_column(String(100), nullable=True)
    notes:           Mapped[str|None]  = mapped_column(Text, nullable=True)
    created_by:      Mapped[str]       = mapped_column(UUID(as_uuid=False), nullable=False)
    created_at:      Mapped[datetime]  = mapped_column(SADateTime(timezone=True), default=utcnow, nullable=False)
    updated_at:      Mapped[datetime]  = mapped_column(SADateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    invoices: Mapped[list["Invoice"]] = relationship("Invoice", back_populates="client_ref", lazy="select")


class Invoice(Base):
    __tablename__ = "ext_inv_invoices"

    id:             Mapped[str]               = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id:      Mapped[str]               = mapped_column(UUID(as_uuid=False), nullable=False, index=True)
    client_id:      Mapped[str|None]          = mapped_column(UUID(as_uuid=False), ForeignKey("ext_inv_clients.id", ondelete="SET NULL"), nullable=True, index=True)
    client_name:    Mapped[str]               = mapped_column(String(255), nullable=False, default="Unknown")
    invoice_number: Mapped[str]               = mapped_column(String(50),  nullable=False)
    status:         Mapped[InvoiceStatus]     = mapped_column(SAEnum(InvoiceStatus), default=InvoiceStatus.draft, nullable=False, index=True)
    issue_date:     Mapped[datetime|None]     = mapped_column(Date, nullable=True)
    due_date:       Mapped[datetime|None]     = mapped_column(Date, nullable=True)
    subtotal:       Mapped[float]             = mapped_column(Numeric(12, 2), default=0.0, nullable=False)
    tax_rate:       Mapped[float]             = mapped_column(Numeric(5,  2), default=0.0, nullable=False)
    total:          Mapped[float]             = mapped_column(Numeric(12, 2), default=0.0, nullable=False)
    currency:       Mapped[str]               = mapped_column(String(3), default="USD", nullable=False)
    notes:          Mapped[str|None]          = mapped_column(Text, nullable=True)
    paid_at:        Mapped[datetime|None]     = mapped_column(SADateTime(timezone=True), nullable=True)
    created_by:     Mapped[str]               = mapped_column(UUID(as_uuid=False), nullable=False)
    created_at:     Mapped[datetime]          = mapped_column(SADateTime(timezone=True), default=utcnow, nullable=False)
    updated_at:     Mapped[datetime]          = mapped_column(SADateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    client_ref: Mapped["Client|None"]    = relationship("Client", back_populates="invoices")
    line_items: Mapped[list["LineItem"]] = relationship("LineItem", back_populates="invoice", cascade="all, delete-orphan", lazy="selectin")


class LineItem(Base):
    __tablename__ = "ext_inv_line_items"

    id:          Mapped[str]      = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id:   Mapped[str]      = mapped_column(UUID(as_uuid=False), nullable=False, index=True)
    invoice_id:  Mapped[str]      = mapped_column(UUID(as_uuid=False), ForeignKey("ext_inv_invoices.id", ondelete="CASCADE"), nullable=False, index=True)
    description: Mapped[str]      = mapped_column(String(500), nullable=False)
    quantity:    Mapped[float]    = mapped_column(Numeric(10, 3), default=1.0, nullable=False)
    unit_price:  Mapped[float]    = mapped_column(Numeric(12, 2), default=0.0, nullable=False)
    amount:      Mapped[float]    = mapped_column(Numeric(12, 2), default=0.0, nullable=False)
    created_by:  Mapped[str]      = mapped_column(UUID(as_uuid=False), nullable=False)
    created_at:  Mapped[datetime] = mapped_column(SADateTime(timezone=True), default=utcnow, nullable=False)
    updated_at:  Mapped[datetime] = mapped_column(SADateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    invoice: Mapped["Invoice"] = relationship("Invoice", back_populates="line_items")
