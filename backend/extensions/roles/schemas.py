"""Roles — Pydantic schemas."""
from __future__ import annotations
from typing import Optional
from pydantic import BaseModel


class RoleCreate(BaseModel):
    name: str
    description: Optional[str] = None
    permissions: list[str] = []
    is_default: bool = False


class RoleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    permissions: Optional[list[str]] = None
    is_default: Optional[bool] = None


class RoleResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    permissions: list[str]
    is_default: bool
    created_at: str

    class Config:
        from_attributes = True
