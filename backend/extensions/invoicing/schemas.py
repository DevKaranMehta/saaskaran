"""Invoicing — Pydantic schemas with robust coercion for HTML form inputs."""
from __future__ import annotations
from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator


# ── helpers ───────────────────────────────────────────────────────────────────

def _coerce_date(v):
    """Accept date, datetime, ISO string with or without time component, or empty string."""
    if v is None or v == "":
        return None
    if isinstance(v, date) and not isinstance(v, datetime):
        return v
    if isinstance(v, datetime):
        return v.date()
    if isinstance(v, str):
        s = v.strip()
        if not s:
            return None
        # Strip timezone/offset so fromisoformat doesn't choke on older Python
        if "T" in s:
            s = s.split("+")[0].split("Z")[0]
            return datetime.fromisoformat(s).date()
        return date.fromisoformat(s)
    return v


def _coerce_float(v):
    if v is None or v == "":
        return 0.0
    return float(v)


def _empty_to_none(v):
    if v == "" or v == "null":
        return None
    return v


# ── Client schemas ─────────────────────────────────────────────────────────────

class ClientCreate(BaseModel):
    name:            str           = Field(..., min_length=1, max_length=255)
    email:           Optional[str] = Field(None, max_length=255)
    phone:           Optional[str] = Field(None, max_length=50)
    company:         Optional[str] = Field(None, max_length=255)
    billing_address: Optional[str] = None
    tax_id:          Optional[str] = Field(None, max_length=100)
    notes:           Optional[str] = None


class ClientUpdate(BaseModel):
    name:            Optional[str] = Field(None, min_length=1, max_length=255)
    email:           Optional[str] = None
    phone:           Optional[str] = None
    company:         Optional[str] = None
    billing_address: Optional[str] = None
    tax_id:          Optional[str] = None
    notes:           Optional[str] = None


class ClientResponse(BaseModel):
    id:              str
    tenant_id:       str
    name:            str
    email:           Optional[str]
    phone:           Optional[str]
    company:         Optional[str]
    billing_address: Optional[str]
    tax_id:          Optional[str]
    notes:           Optional[str]
    created_by:      str
    created_at:      datetime
    updated_at:      datetime

    class Config:
        from_attributes = True


# ── Line item schemas ──────────────────────────────────────────────────────────

class LineItemCreate(BaseModel):
    description: str   = Field(..., min_length=1, max_length=500)
    quantity:    float = Field(1.0, ge=0)
    unit_price:  float = Field(0.0, ge=0)

    @field_validator("quantity", "unit_price", mode="before")
    @classmethod
    def parse_numeric(cls, v):
        return _coerce_float(v)


class LineItemResponse(BaseModel):
    id:          str
    invoice_id:  str
    description: str
    quantity:    float
    unit_price:  float
    amount:      float
    created_at:  datetime

    class Config:
        from_attributes = True


# ── Invoice schemas ────────────────────────────────────────────────────────────

class InvoiceCreate(BaseModel):
    client_id:      Optional[str]            = None
    client_name:    Optional[str]            = Field(None, max_length=255)
    invoice_number: Optional[str]            = Field(None, max_length=50)
    status:         str                      = "draft"
    issue_date:     Optional[date]           = None
    due_date:       Optional[date]           = None
    tax_rate:       float                    = 0.0
    currency:       str                      = "USD"
    notes:          Optional[str]            = None
    line_items:     list[LineItemCreate]     = Field(default_factory=list)

    # ── date coercion: accept "2026-02-22T00:58" from datetime-local inputs ──
    @field_validator("issue_date", "due_date", mode="before")
    @classmethod
    def parse_dates(cls, v):
        return _coerce_date(v)

    # ── line_items: accept "" (empty string) as empty list ───────────────────
    @field_validator("line_items", mode="before")
    @classmethod
    def parse_line_items(cls, v):
        if v is None or v == "":
            return []
        return v

    # ── numeric fields: accept "" as 0.0 ─────────────────────────────────────
    @field_validator("tax_rate", mode="before")
    @classmethod
    def parse_tax_rate(cls, v):
        return _coerce_float(v)

    # ── string fields: accept "" as None ─────────────────────────────────────
    @field_validator("invoice_number", "client_id", "client_name", mode="before")
    @classmethod
    def empty_str_to_none(cls, v):
        return _empty_to_none(v)

    @field_validator("currency", mode="before")
    @classmethod
    def default_currency(cls, v):
        if not v:
            return "USD"
        return v

    @field_validator("status", mode="before")
    @classmethod
    def default_status(cls, v):
        if not v:
            return "draft"
        return v


class InvoiceUpdate(BaseModel):
    client_id:      Optional[str]   = None
    client_name:    Optional[str]   = None
    invoice_number: Optional[str]   = None
    status:         Optional[str]   = None
    issue_date:     Optional[date]  = None
    due_date:       Optional[date]  = None
    tax_rate:       Optional[float] = None
    currency:       Optional[str]   = None
    notes:          Optional[str]   = None

    @field_validator("issue_date", "due_date", mode="before")
    @classmethod
    def parse_dates(cls, v):
        return _coerce_date(v)

    @field_validator("tax_rate", mode="before")
    @classmethod
    def parse_tax_rate(cls, v):
        if v is None or v == "":
            return None
        return float(v)


class StatusUpdate(BaseModel):
    status: str


class InvoiceResponse(BaseModel):
    id:             str
    tenant_id:      str
    client_id:      Optional[str]
    client_name:    str
    invoice_number: str
    status:         str
    issue_date:     Optional[date]
    due_date:       Optional[date]
    subtotal:       float
    tax_rate:       float
    total:          float
    currency:       str
    notes:          Optional[str]
    paid_at:        Optional[datetime]
    created_by:     str
    created_at:     datetime
    updated_at:     datetime
    line_items:     list[LineItemResponse] = Field(default_factory=list)

    class Config:
        from_attributes = True
