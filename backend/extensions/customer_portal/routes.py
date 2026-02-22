"""Customer Portal — API routes."""
from __future__ import annotations
from datetime import UTC, datetime
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth import get_current_user
from api.database import get_db
from api.models import User

from .models import Ticket, TicketReply, TicketStatus, TicketPriority, TicketCategory
from .schemas import (
    TicketCreate, TicketUpdate, TicketResponse,
    ReplyCreate, ReplyResponse, TicketStats,
)

router = APIRouter()


# ── Tickets ───────────────────────────────────────────────────────────────────

@router.get("/tickets", response_model=list[TicketResponse])
async def list_tickets(
    status:   Optional[TicketStatus]   = Query(None),
    priority: Optional[TicketPriority] = Query(None),
    category: Optional[TicketCategory] = Query(None),
    search:   Optional[str]            = Query(None),
    current_user: Annotated[User, Depends(get_current_user)] = None,
    db:            Annotated[AsyncSession, Depends(get_db)]  = None,
):
    q = select(Ticket).where(Ticket.tenant_id == current_user.tenant_id)
    if status:
        q = q.where(Ticket.status == status)
    if priority:
        q = q.where(Ticket.priority == priority)
    if category:
        q = q.where(Ticket.category == category)
    if search:
        q = q.where(
            Ticket.title.ilike(f"%{search}%") |
            Ticket.customer_email.ilike(f"%{search}%") |
            Ticket.customer_name.ilike(f"%{search}%")
        )
    # Urgent+high first, then newest
    q = q.order_by(
        Ticket.priority.in_([TicketPriority.urgent, TicketPriority.high]).desc(),
        Ticket.created_at.desc(),
    )
    result = await db.execute(q)
    return result.scalars().all()


@router.post("/tickets", response_model=TicketResponse, status_code=201)
async def create_ticket(
    payload:      TicketCreate,
    current_user: Annotated[User, Depends(get_current_user)] = None,
    db:            Annotated[AsyncSession, Depends(get_db)]  = None,
):
    ticket = Ticket(
        **payload.model_dump(),
        tenant_id=current_user.tenant_id,
        created_by=current_user.id,
    )
    db.add(ticket)
    await db.commit()
    await db.refresh(ticket)
    return ticket


@router.get("/tickets/{ticket_id}", response_model=TicketResponse)
async def get_ticket(
    ticket_id:    str,
    current_user: Annotated[User, Depends(get_current_user)] = None,
    db:            Annotated[AsyncSession, Depends(get_db)]  = None,
):
    result = await db.execute(
        select(Ticket).where(Ticket.id == ticket_id, Ticket.tenant_id == current_user.tenant_id)
    )
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket


@router.patch("/tickets/{ticket_id}", response_model=TicketResponse)
async def update_ticket(
    ticket_id:    str,
    payload:      TicketUpdate,
    current_user: Annotated[User, Depends(get_current_user)] = None,
    db:            Annotated[AsyncSession, Depends(get_db)]  = None,
):
    result = await db.execute(
        select(Ticket).where(Ticket.id == ticket_id, Ticket.tenant_id == current_user.tenant_id)
    )
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    data = payload.model_dump(exclude_unset=True)
    # Track resolved_at timestamp
    if data.get("status") == TicketStatus.resolved and ticket.status != TicketStatus.resolved:
        data["resolved_at"] = datetime.now(UTC)
    for k, v in data.items():
        setattr(ticket, k, v)

    await db.commit()
    await db.refresh(ticket)
    return ticket


@router.delete("/tickets/{ticket_id}", status_code=204)
async def delete_ticket(
    ticket_id:    str,
    current_user: Annotated[User, Depends(get_current_user)] = None,
    db:            Annotated[AsyncSession, Depends(get_db)]  = None,
):
    result = await db.execute(
        select(Ticket).where(Ticket.id == ticket_id, Ticket.tenant_id == current_user.tenant_id)
    )
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    await db.delete(ticket)
    await db.commit()


# ── Replies ───────────────────────────────────────────────────────────────────

@router.get("/tickets/{ticket_id}/replies", response_model=list[ReplyResponse])
async def list_replies(
    ticket_id:    str,
    current_user: Annotated[User, Depends(get_current_user)] = None,
    db:            Annotated[AsyncSession, Depends(get_db)]  = None,
):
    # Verify ticket belongs to tenant
    t = await db.execute(
        select(Ticket).where(Ticket.id == ticket_id, Ticket.tenant_id == current_user.tenant_id)
    )
    if not t.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Ticket not found")

    result = await db.execute(
        select(TicketReply)
        .where(TicketReply.ticket_id == ticket_id, TicketReply.tenant_id == current_user.tenant_id)
        .order_by(TicketReply.created_at.asc())
    )
    return result.scalars().all()


@router.post("/tickets/{ticket_id}/replies", response_model=ReplyResponse, status_code=201)
async def create_reply(
    ticket_id:    str,
    payload:      ReplyCreate,
    current_user: Annotated[User, Depends(get_current_user)] = None,
    db:            Annotated[AsyncSession, Depends(get_db)]  = None,
):
    t_result = await db.execute(
        select(Ticket).where(Ticket.id == ticket_id, Ticket.tenant_id == current_user.tenant_id)
    )
    ticket = t_result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    reply = TicketReply(
        **payload.model_dump(),
        ticket_id=ticket_id,
        tenant_id=current_user.tenant_id,
        created_by=current_user.id,
    )
    db.add(reply)

    # Increment reply count & auto-move to in_progress on first reply
    ticket.reply_count += 1
    if ticket.status == TicketStatus.open:
        ticket.status = TicketStatus.in_progress

    await db.commit()
    await db.refresh(reply)
    return reply


@router.delete("/tickets/{ticket_id}/replies/{reply_id}", status_code=204)
async def delete_reply(
    ticket_id:    str,
    reply_id:     str,
    current_user: Annotated[User, Depends(get_current_user)] = None,
    db:            Annotated[AsyncSession, Depends(get_db)]  = None,
):
    result = await db.execute(
        select(TicketReply).where(
            TicketReply.id == reply_id,
            TicketReply.ticket_id == ticket_id,
            TicketReply.tenant_id == current_user.tenant_id,
        )
    )
    reply = result.scalar_one_or_none()
    if not reply:
        raise HTTPException(status_code=404, detail="Reply not found")
    await db.delete(reply)
    await db.commit()


# ── Stats ─────────────────────────────────────────────────────────────────────

@router.get("/stats", response_model=TicketStats)
async def get_stats(
    current_user: Annotated[User, Depends(get_current_user)] = None,
    db:            Annotated[AsyncSession, Depends(get_db)]  = None,
):
    base = select(Ticket).where(Ticket.tenant_id == current_user.tenant_id)

    total_r = await db.execute(select(func.count()).select_from(base.subquery()))
    total   = total_r.scalar() or 0

    # By status
    by_status: dict[str, int] = {s.value: 0 for s in TicketStatus}
    rows = await db.execute(
        select(Ticket.status, func.count()).where(Ticket.tenant_id == current_user.tenant_id)
        .group_by(Ticket.status)
    )
    for status, count in rows:
        by_status[status.value] = count

    # By priority
    by_priority: dict[str, int] = {p.value: 0 for p in TicketPriority}
    rows = await db.execute(
        select(Ticket.priority, func.count()).where(Ticket.tenant_id == current_user.tenant_id)
        .group_by(Ticket.priority)
    )
    for priority, count in rows:
        by_priority[priority.value] = count

    # By category
    by_category: dict[str, int] = {c.value: 0 for c in TicketCategory}
    rows = await db.execute(
        select(Ticket.category, func.count()).where(Ticket.tenant_id == current_user.tenant_id)
        .group_by(Ticket.category)
    )
    for category, count in rows:
        by_category[category.value] = count

    # Open urgent tickets
    urgent_r = await db.execute(
        select(func.count()).where(
            Ticket.tenant_id == current_user.tenant_id,
            Ticket.priority == TicketPriority.urgent,
            Ticket.status == TicketStatus.open,
        )
    )
    open_urgent = urgent_r.scalar() or 0

    # Avg replies
    avg_r = await db.execute(
        select(func.avg(Ticket.reply_count)).where(Ticket.tenant_id == current_user.tenant_id)
    )
    avg_reply_count = float(avg_r.scalar() or 0)

    return TicketStats(
        total=total,
        by_status=by_status,
        by_priority=by_priority,
        by_category=by_category,
        open_urgent=open_urgent,
        avg_reply_count=round(avg_reply_count, 2),
    )
