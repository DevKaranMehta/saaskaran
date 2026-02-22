"""Audit Log — API routes."""
from __future__ import annotations
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from api.auth import get_current_user
from api.database import get_db
from api.models import User
from .models import AuditEntry
from .schemas import AuditEntryCreate, AuditEntryResponse

router = APIRouter(tags=["audit-log"])


@router.get("/", response_model=list[AuditEntryResponse])
async def list_entries(
    action: Optional[str] = Query(None),
    resource_type: Optional[str] = Query(None),
    limit: int = Query(50, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = select(AuditEntry).where(AuditEntry.tenant_id == current_user.tenant_id).order_by(AuditEntry.created_at.desc()).limit(limit)
    if action:
        q = q.where(AuditEntry.action == action)
    if resource_type:
        q = q.where(AuditEntry.resource_type == resource_type)
    result = await db.execute(q)
    items = result.scalars().all()
    return [AuditEntryResponse(id=e.id, user_id=e.user_id, action=e.action, resource_type=e.resource_type, resource_id=e.resource_id, metadata=e.metadata or {}, created_at=str(e.created_at)) for e in items]


@router.post("/", response_model=AuditEntryResponse, status_code=201)
async def log_entry(
    body: AuditEntryCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    entry = AuditEntry(
        id=str(uuid.uuid4()),
        tenant_id=current_user.tenant_id,
        user_id=current_user.id,
        action=body.action,
        resource_type=body.resource_type,
        resource_id=body.resource_id,
        metadata=body.metadata,
        ip_address=request.client.host if request.client else None,
    )
    db.add(entry)
    await db.commit()
    await db.refresh(entry)
    return AuditEntryResponse(id=entry.id, user_id=entry.user_id, action=entry.action, resource_type=entry.resource_type, resource_id=entry.resource_id, metadata=entry.metadata or {}, created_at=str(entry.created_at))
