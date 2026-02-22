"""Appointment Booking — FastAPI routes."""
from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth     import get_current_user
from api.database import get_db
from api.models   import User

from .models  import Service, Appointment
from .schemas import (
    ServiceCreate, ServiceResponse, ServiceUpdate,
    AppointmentCreate, AppointmentResponse, AppointmentUpdate,
)

router = APIRouter(tags=["appointment_booking"])


# ── Services ──────────────────────────────────────────────────────────────────

@router.get("/services", response_model=list[ServiceResponse])
async def list_services(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Service)
        .where(Service.tenant_id == current_user.tenant_id)
        .order_by(Service.name)
    )
    return result.scalars().all()


@router.post("/services", response_model=ServiceResponse, status_code=status.HTTP_201_CREATED)
async def create_service(
    payload: ServiceCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = Service(
        tenant_id        = current_user.tenant_id,
        created_by       = current_user.id,
        name             = payload.name,
        description      = payload.description,
        duration_minutes = payload.duration_minutes,
        price            = payload.price,
        is_active        = payload.is_active,
    )
    db.add(service)
    await db.commit()
    await db.refresh(service)
    return service


@router.get("/services/{item_id}", response_model=ServiceResponse)
async def get_service(
    item_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Service).where(Service.id == item_id, Service.tenant_id == current_user.tenant_id)
    )
    service = result.scalar_one_or_none()
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    return service


@router.patch("/services/{item_id}", response_model=ServiceResponse)
async def update_service(
    item_id: str,
    payload: ServiceUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Service).where(Service.id == item_id, Service.tenant_id == current_user.tenant_id)
    )
    service = result.scalar_one_or_none()
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(service, field, value)
    await db.commit()
    await db.refresh(service)
    return service


@router.delete("/services/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_service(
    item_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Service).where(Service.id == item_id, Service.tenant_id == current_user.tenant_id)
    )
    service = result.scalar_one_or_none()
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    await db.delete(service)
    await db.commit()


# ── Appointments ───────────────────────────────────────────────────────────────

@router.get("/appointments", response_model=list[AppointmentResponse])
async def list_appointments(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Appointment)
        .where(Appointment.tenant_id == current_user.tenant_id)
        .order_by(Appointment.start_time.desc())
    )
    return result.scalars().all()


@router.post("/appointments", response_model=AppointmentResponse, status_code=status.HTTP_201_CREATED)
async def create_appointment(
    payload: AppointmentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Verify the service belongs to this tenant
    svc_result = await db.execute(
        select(Service).where(
            Service.id == payload.service_id,
            Service.tenant_id == current_user.tenant_id,
        )
    )
    service = svc_result.scalar_one_or_none()
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    if not service.is_active:
        raise HTTPException(status_code=400, detail="Service is not active")
    if payload.end_time <= payload.start_time:
        raise HTTPException(status_code=400, detail="end_time must be after start_time")

    appointment = Appointment(
        tenant_id    = current_user.tenant_id,
        created_by   = current_user.id,
        service_id   = payload.service_id,
        client_name  = payload.client_name,
        client_email = payload.client_email,
        start_time   = payload.start_time,
        end_time     = payload.end_time,
        notes        = payload.notes,
    )
    db.add(appointment)
    await db.commit()
    await db.refresh(appointment)
    return appointment


@router.get("/appointments/{item_id}", response_model=AppointmentResponse)
async def get_appointment(
    item_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Appointment).where(
            Appointment.id == item_id,
            Appointment.tenant_id == current_user.tenant_id,
        )
    )
    appointment = result.scalar_one_or_none()
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    return appointment


@router.patch("/appointments/{item_id}", response_model=AppointmentResponse)
async def update_appointment(
    item_id: str,
    payload: AppointmentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Appointment).where(
            Appointment.id == item_id,
            Appointment.tenant_id == current_user.tenant_id,
        )
    )
    appointment = result.scalar_one_or_none()
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    updates = payload.model_dump(exclude_unset=True)
    start = updates.get("start_time", appointment.start_time)
    end   = updates.get("end_time",   appointment.end_time)
    if end <= start:
        raise HTTPException(status_code=400, detail="end_time must be after start_time")

    for field, value in updates.items():
        setattr(appointment, field, value)
    await db.commit()
    await db.refresh(appointment)
    return appointment


@router.delete("/appointments/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_appointment(
    item_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Appointment).where(
            Appointment.id == item_id,
            Appointment.tenant_id == current_user.tenant_id,
        )
    )
    appointment = result.scalar_one_or_none()
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    await db.delete(appointment)
    await db.commit()
