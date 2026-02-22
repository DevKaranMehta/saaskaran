"""Appointment Booking — Pydantic schemas."""
from __future__ import annotations
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, EmailStr
from .models import AppointmentStatus


# ── Services ──────────────────────────────────────────────────────────────────

class ServiceCreate(BaseModel):
    name:             str            = Field(..., min_length=1, max_length=255)
    description:      Optional[str] = None
    duration_minutes: int            = Field(60, ge=5, le=480)
    price:            Optional[float] = Field(None, ge=0)
    is_active:        bool           = True


class ServiceUpdate(BaseModel):
    name:             Optional[str]   = Field(None, min_length=1, max_length=255)
    description:      Optional[str]   = None
    duration_minutes: Optional[int]   = Field(None, ge=5, le=480)
    price:            Optional[float] = Field(None, ge=0)
    is_active:        Optional[bool]  = None


class ServiceResponse(BaseModel):
    id:               str
    tenant_id:        str
    name:             str
    description:      Optional[str]
    duration_minutes: int
    price:            Optional[float]
    is_active:        bool
    created_by:       str
    created_at:       datetime
    updated_at:       datetime

    class Config:
        from_attributes = True


# ── Appointments ───────────────────────────────────────────────────────────────

class AppointmentCreate(BaseModel):
    service_id:   str      = Field(..., min_length=1)
    client_name:  str      = Field(..., min_length=1, max_length=255)
    client_email: str      = Field(..., min_length=1, max_length=255)
    start_time:   datetime
    end_time:     datetime
    notes:        Optional[str] = None


class AppointmentUpdate(BaseModel):
    client_name:  Optional[str]               = Field(None, min_length=1, max_length=255)
    client_email: Optional[str]               = Field(None, min_length=1, max_length=255)
    start_time:   Optional[datetime]          = None
    end_time:     Optional[datetime]          = None
    status:       Optional[AppointmentStatus] = None
    notes:        Optional[str]               = None


class AppointmentResponse(BaseModel):
    id:           str
    tenant_id:    str
    service_id:   str
    client_name:  str
    client_email: str
    start_time:   datetime
    end_time:     datetime
    status:       AppointmentStatus
    notes:        Optional[str]
    created_by:   str
    created_at:   datetime
    updated_at:   datetime

    class Config:
        from_attributes = True
