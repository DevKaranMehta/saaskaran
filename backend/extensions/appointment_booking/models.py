"""Appointment Booking — SQLAlchemy models."""
from __future__ import annotations
import uuid
import enum
from datetime import UTC, datetime
from sqlalchemy import String, Text, Numeric, Integer, ForeignKey
from sqlalchemy import DateTime as SADateTime
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from api.database import Base


def utcnow() -> datetime:
    return datetime.now(UTC)


class AppointmentStatus(str, enum.Enum):
    pending   = "pending"
    confirmed = "confirmed"
    completed = "completed"
    cancelled = "cancelled"


class Service(Base):
    __tablename__ = "ext_appointment_services"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    tenant_id: Mapped[str]      = mapped_column(UUID(as_uuid=False), nullable=False, index=True)
    name: Mapped[str]           = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration_minutes: Mapped[int]   = mapped_column(Integer, nullable=False, default=60)
    price: Mapped[float | None]     = mapped_column(Numeric(10, 2), nullable=True)
    is_active: Mapped[bool]         = mapped_column(default=True, nullable=False)
    created_by: Mapped[str]         = mapped_column(UUID(as_uuid=False), nullable=False)
    created_at: Mapped[datetime]    = mapped_column(SADateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime]    = mapped_column(SADateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    appointments: Mapped[list["Appointment"]] = relationship(
        "Appointment", back_populates="service", cascade="all, delete-orphan", lazy="selectin"
    )


class Appointment(Base):
    __tablename__ = "ext_appointments"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    tenant_id: Mapped[str]  = mapped_column(UUID(as_uuid=False), nullable=False, index=True)
    service_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("ext_appointment_services.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    client_name: Mapped[str]           = mapped_column(String(255), nullable=False)
    client_email: Mapped[str]          = mapped_column(String(255), nullable=False)
    start_time: Mapped[datetime]       = mapped_column(SADateTime(timezone=True), nullable=False)
    end_time: Mapped[datetime]         = mapped_column(SADateTime(timezone=True), nullable=False)
    status: Mapped[AppointmentStatus]  = mapped_column(
        SAEnum(AppointmentStatus), default=AppointmentStatus.pending, nullable=False, index=True
    )
    notes: Mapped[str | None]          = mapped_column(Text, nullable=True)
    created_by: Mapped[str]            = mapped_column(UUID(as_uuid=False), nullable=False)
    created_at: Mapped[datetime]       = mapped_column(SADateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime]       = mapped_column(SADateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    service: Mapped["Service"] = relationship("Service", back_populates="appointments")
