"""Audit Log — Pydantic schemas."""
from __future__ import annotations
from typing import Optional
from pydantic import BaseModel


class AuditEntryCreate(BaseModel):
    action: str
    resource_type: str
    resource_id: Optional[str] = None
    metadata: dict = {}


class AuditEntryResponse(BaseModel):
    id: str
    user_id: Optional[str]
    action: str
    resource_type: str
    resource_id: Optional[str]
    metadata: dict
    created_at: str

    class Config:
        from_attributes = True
