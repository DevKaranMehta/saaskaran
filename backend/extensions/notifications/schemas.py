"""Notifications — Pydantic schemas."""
from __future__ import annotations
from typing import Optional
from pydantic import BaseModel


class NotificationCreate(BaseModel):
    title: str
    message: Optional[str] = None
    link: Optional[str] = None
    user_id: Optional[str] = None  # None = broadcast to whole tenant


class NotificationResponse(BaseModel):
    id: str
    title: str
    message: Optional[str]
    link: Optional[str]
    is_read: bool
    created_at: str

    class Config:
        from_attributes = True
