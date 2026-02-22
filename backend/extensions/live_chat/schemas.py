"""Live Chat — Pydantic schemas."""
from __future__ import annotations
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr
from .models import ConvStatus, MsgSender


# ── Sites ──────────────────────────────────────────────────────────────────

class SiteCreate(BaseModel):
    name: str
    url: str
    color: str = "#6366f1"
    greeting: str = "Hi! How can we help you today?"


class SiteUpdate(BaseModel):
    name: Optional[str] = None
    color: Optional[str] = None
    greeting: Optional[str] = None
    is_active: Optional[bool] = None


class SiteResponse(BaseModel):
    id: str
    tenant_id: str
    name: str
    url: str
    site_key: str
    color: str
    greeting: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ── Conversations ──────────────────────────────────────────────────────────

class ConvUpdate(BaseModel):
    status: Optional[ConvStatus] = None
    assigned_to: Optional[str] = None


class ConvResponse(BaseModel):
    id: str
    tenant_id: str
    site_id: str
    visitor_name: str
    visitor_email: Optional[str]
    status: ConvStatus
    message_count: int
    unread_count: int
    last_message: Optional[str]
    last_message_at: Optional[datetime]
    assigned_to: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ── Messages ───────────────────────────────────────────────────────────────

class AgentReply(BaseModel):
    content: str


class MsgResponse(BaseModel):
    id: str
    conversation_id: str
    content: str
    sender: MsgSender
    sender_name: str
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ── Widget API (no JWT) ────────────────────────────────────────────────────

class WidgetStartConv(BaseModel):
    visitor_name: str
    visitor_email: Optional[str] = None


class WidgetSendMsg(BaseModel):
    content: str
    visitor_name: str


# ── Stats ──────────────────────────────────────────────────────────────────

class LiveChatStats(BaseModel):
    total_conversations: int
    open_conversations: int
    total_unread: int
    total_sites: int
