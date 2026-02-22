"""Billing — API routes."""
from __future__ import annotations
import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from api.auth import get_current_user
from api.database import get_db
from api.models import User
from .models import Plan, Subscription
from .schemas import PlanCreate, PlanResponse, SubscriptionResponse

router = APIRouter(tags=["billing"])


@router.get("/plans", response_model=list[PlanResponse])
async def list_plans(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Plan).where(Plan.is_active == True).order_by(Plan.price))
    plans = result.scalars().all()
    return [PlanResponse(id=p.id, name=p.name, description=p.description, price=float(p.price), currency=p.currency, interval=p.interval, features=p.features or [], is_active=p.is_active) for p in plans]


@router.post("/plans", response_model=PlanResponse, status_code=201)
async def create_plan(body: PlanCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    plan = Plan(id=str(uuid.uuid4()), **body.model_dump())
    db.add(plan)
    await db.commit()
    await db.refresh(plan)
    return PlanResponse(id=plan.id, name=plan.name, description=plan.description, price=float(plan.price), currency=plan.currency, interval=plan.interval, features=plan.features or [], is_active=plan.is_active)


@router.get("/subscription", response_model=SubscriptionResponse | None)
async def get_subscription(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(
        select(Subscription).where(Subscription.tenant_id == current_user.tenant_id).order_by(Subscription.created_at.desc())
    )
    sub = result.scalar_one_or_none()
    if not sub:
        return None
    return SubscriptionResponse(id=sub.id, tenant_id=sub.tenant_id, plan_id=sub.plan_id, status=sub.status, started_at=str(sub.started_at), ends_at=str(sub.ends_at) if sub.ends_at else None)
