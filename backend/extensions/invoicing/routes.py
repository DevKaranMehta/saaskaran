"""Invoicing — API routes."""
from __future__ import annotations
from datetime import UTC, date, datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from api.auth import get_current_user
from api.database import get_db
from api.models import User
from .models import Client, Invoice, InvoiceStatus, LineItem
from .schemas import (
    ClientCreate, ClientResponse, ClientUpdate,
    InvoiceCreate, InvoiceResponse, InvoiceUpdate,
    StatusUpdate,
)

router = APIRouter(tags=["invoicing"])


def utcnow() -> datetime:
    return datetime.now(UTC)


# ── Clients ───────────────────────────────────────────────────────────────────

@router.get("/clients/", response_model=list[ClientResponse])
async def list_clients(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Client)
        .where(Client.tenant_id == current_user.tenant_id)
        .order_by(Client.name.asc())
    )
    return result.scalars().all()


@router.post("/clients/", response_model=ClientResponse, status_code=status.HTTP_201_CREATED)
async def create_client(
    payload: ClientCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    client = Client(
        tenant_id=current_user.tenant_id,
        created_by=current_user.id,
        **payload.model_dump(),
    )
    db.add(client)
    await db.commit()
    await db.refresh(client)
    return client


@router.get("/clients/{client_id}", response_model=ClientResponse)
async def get_client(
    client_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Client).where(Client.id == client_id, Client.tenant_id == current_user.tenant_id)
    )
    client = result.scalar_one_or_none()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return client


@router.patch("/clients/{client_id}", response_model=ClientResponse)
async def update_client(
    client_id: str,
    payload: ClientUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Client).where(Client.id == client_id, Client.tenant_id == current_user.tenant_id)
    )
    client = result.scalar_one_or_none()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    for f, v in payload.model_dump(exclude_unset=True).items():
        setattr(client, f, v)
    await db.commit()
    await db.refresh(client)
    return client


@router.delete("/clients/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_client(
    client_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Client).where(Client.id == client_id, Client.tenant_id == current_user.tenant_id)
    )
    client = result.scalar_one_or_none()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    await db.delete(client)
    await db.commit()


# ── Invoices ──────────────────────────────────────────────────────────────────

@router.get("/invoices/", response_model=list[InvoiceResponse])
async def list_invoices(
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by invoice status"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = (
        select(Invoice)
        .options(selectinload(Invoice.line_items))
        .where(Invoice.tenant_id == current_user.tenant_id)
    )
    if status_filter:
        q = q.where(Invoice.status == status_filter)
    q = q.order_by(Invoice.created_at.desc())
    result = await db.execute(q)
    return result.scalars().all()


@router.post("/invoices/", response_model=InvoiceResponse, status_code=status.HTTP_201_CREATED)
async def create_invoice(
    payload: InvoiceCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Auto-generate invoice number when not supplied
    if not payload.invoice_number:
        count_result = await db.execute(
            select(func.count(Invoice.id)).where(Invoice.tenant_id == current_user.tenant_id)
        )
        count = count_result.scalar() or 0
        inv_number = f"INV-{count + 1:04d}"
    else:
        inv_number = payload.invoice_number

    # Compute totals from line items
    items = payload.line_items or []
    subtotal  = round(sum(float(i.quantity) * float(i.unit_price) for i in items), 2)
    tax_rate  = float(payload.tax_rate or 0.0)
    total     = round(subtotal * (1 + tax_rate / 100), 2)

    invoice = Invoice(
        tenant_id=current_user.tenant_id,
        created_by=current_user.id,
        invoice_number=inv_number,
        client_id=payload.client_id or None,
        client_name=payload.client_name or "Unknown",
        status=payload.status or InvoiceStatus.draft,
        issue_date=payload.issue_date or date.today(),
        due_date=payload.due_date,
        subtotal=subtotal,
        tax_rate=tax_rate,
        total=total,
        currency=payload.currency or "USD",
        notes=payload.notes,
    )
    db.add(invoice)
    await db.flush()  # obtain invoice.id before inserting line items

    for item in items:
        line = LineItem(
            invoice_id=invoice.id,
            tenant_id=current_user.tenant_id,
            created_by=current_user.id,
            description=item.description,
            quantity=float(item.quantity),
            unit_price=float(item.unit_price),
            amount=round(float(item.quantity) * float(item.unit_price), 2),
        )
        db.add(line)

    await db.commit()

    # Reload with eager line_items
    result = await db.execute(
        select(Invoice)
        .options(selectinload(Invoice.line_items))
        .where(Invoice.id == invoice.id)
    )
    return result.scalar_one()


@router.get("/invoices/{invoice_id}", response_model=InvoiceResponse)
async def get_invoice(
    invoice_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Invoice)
        .options(selectinload(Invoice.line_items))
        .where(Invoice.id == invoice_id, Invoice.tenant_id == current_user.tenant_id)
    )
    invoice = result.scalar_one_or_none()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return invoice


@router.patch("/invoices/{invoice_id}", response_model=InvoiceResponse)
async def update_invoice(
    invoice_id: str,
    payload: InvoiceUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Invoice)
        .options(selectinload(Invoice.line_items))
        .where(Invoice.id == invoice_id, Invoice.tenant_id == current_user.tenant_id)
    )
    invoice = result.scalar_one_or_none()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    for f, v in payload.model_dump(exclude_unset=True).items():
        setattr(invoice, f, v)
    await db.commit()
    await db.refresh(invoice)
    return invoice


@router.delete("/invoices/{invoice_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_invoice(
    invoice_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Invoice).where(Invoice.id == invoice_id, Invoice.tenant_id == current_user.tenant_id)
    )
    invoice = result.scalar_one_or_none()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    await db.delete(invoice)
    await db.commit()


@router.patch("/invoices/{invoice_id}/status", response_model=InvoiceResponse)
async def update_invoice_status(
    invoice_id: str,
    payload: StatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Invoice)
        .options(selectinload(Invoice.line_items))
        .where(Invoice.id == invoice_id, Invoice.tenant_id == current_user.tenant_id)
    )
    invoice = result.scalar_one_or_none()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    invoice.status = payload.status
    if payload.status == InvoiceStatus.paid and not invoice.paid_at:
        invoice.paid_at = utcnow()
    await db.commit()
    await db.refresh(invoice)
    return invoice


@router.post("/invoices/{invoice_id}/mark-paid", response_model=InvoiceResponse)
async def mark_invoice_paid(
    invoice_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Invoice)
        .options(selectinload(Invoice.line_items))
        .where(Invoice.id == invoice_id, Invoice.tenant_id == current_user.tenant_id)
    )
    invoice = result.scalar_one_or_none()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    invoice.status  = InvoiceStatus.paid
    invoice.paid_at = utcnow()
    await db.commit()
    await db.refresh(invoice)
    return invoice


@router.get("/stats")
async def get_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    rows = await db.execute(
        select(
            Invoice.status,
            func.count(Invoice.id).label("count"),
            func.coalesce(func.sum(Invoice.total), 0).label("revenue"),
        )
        .where(Invoice.tenant_id == current_user.tenant_id)
        .group_by(Invoice.status)
    )
    by_status: dict = {}
    total_revenue = 0.0
    total_count   = 0
    for row in rows:
        by_status[str(row.status)] = {"count": row.count, "revenue": float(row.revenue)}
        total_count   += row.count
        total_revenue += float(row.revenue)

    paid_revenue = by_status.get("paid", {}).get("revenue", 0.0)

    return {
        "total_invoices": total_count,
        "total_revenue":  round(total_revenue, 2),
        "paid_revenue":   round(paid_revenue, 2),
        "by_status":      by_status,
    }
