"""Notifications — API routes."""
from __future__ import annotations
import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from api.auth import get_current_user
from api.database import get_db
from api.models import User
from .models import Notification
from .schemas import NotificationCreate, NotificationResponse

router = APIRouter(tags=["notifications"])


@router.get("/", response_model=list[NotificationResponse])
async def list_notifications(
    unread_only: bool = False,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = select(Notification).where(
        Notification.tenant_id == current_user.tenant_id,
        or_(Notification.user_id == current_user.id, Notification.user_id == None),
    ).order_by(Notification.created_at.desc()).limit(100)
    if unread_only:
        q = q.where(Notification.is_read == False)
    result = await db.execute(q)
    items = result.scalars().all()
    return [NotificationResponse(id=n.id, title=n.title, message=n.message, link=n.link, is_read=n.is_read, created_at=str(n.created_at)) for n in items]


@router.post("/", response_model=NotificationResponse, status_code=201)
async def create_notification(
    body: NotificationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    notif = Notification(
        id=str(uuid.uuid4()),
        tenant_id=current_user.tenant_id,
        user_id=body.user_id,
        title=body.title,
        message=body.message,
        link=body.link,
    )
    db.add(notif)
    await db.commit()
    await db.refresh(notif)
    return NotificationResponse(id=notif.id, title=notif.title, message=notif.message, link=notif.link, is_read=notif.is_read, created_at=str(notif.created_at))


@router.patch("/{notif_id}/read")
async def mark_read(notif_id: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    await db.execute(
        update(Notification).where(Notification.id == notif_id, Notification.tenant_id == current_user.tenant_id).values(is_read=True)
    )
    await db.commit()
    return {"success": True}


@router.patch("/read-all")
async def mark_all_read(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    await db.execute(
        update(Notification).where(Notification.tenant_id == current_user.tenant_id, Notification.is_read == False).values(is_read=True)
    )
    await db.commit()
    return {"success": True}
