"""Billing — Pydantic schemas."""
from __future__ import annotations
from typing import Optional
from pydantic import BaseModel


class PlanCreate(BaseModel):
    name: str
    description: Optional[str] = None
    price: float = 0.0
    currency: str = "USD"
    interval: str = "month"
    features: list[str] = []


class PlanResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    price: float
    currency: str
    interval: str
    features: list
    is_active: bool

    class Config:
        from_attributes = True


class SubscriptionResponse(BaseModel):
    id: str
    tenant_id: str
    plan_id: Optional[str]
    status: str
    started_at: str
    ends_at: Optional[str]

    class Config:
        from_attributes = True
