"""Settings — API routes."""
from __future__ import annotations
import uuid
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession
from api.auth import get_current_user
from api.database import get_db
from api.models import User
from .models import WorkspaceSetting
from .schemas import SettingResponse, SettingUpsert

router = APIRouter(tags=["settings"])


@router.get("/", response_model=list[SettingResponse])
async def list_settings(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(WorkspaceSetting).where(WorkspaceSetting.tenant_id == current_user.tenant_id).order_by(WorkspaceSetting.key)
    )
    rows = result.scalars().all()
    return [SettingResponse(id=r.id, key=r.key, value=r.value, updated_at=str(r.updated_at)) for r in rows]


@router.put("/{key}")
async def upsert_setting(
    key: str,
    body: SettingUpsert,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    existing = await db.execute(
        select(WorkspaceSetting).where(
            WorkspaceSetting.tenant_id == current_user.tenant_id,
            WorkspaceSetting.key == key,
        )
    )
    row = existing.scalar_one_or_none()
    if row:
        row.value = body.value
    else:
        row = WorkspaceSetting(id=str(uuid.uuid4()), tenant_id=current_user.tenant_id, key=key, value=body.value)
        db.add(row)
    await db.commit()
    await db.refresh(row)
    return SettingResponse(id=row.id, key=row.key, value=row.value, updated_at=str(row.updated_at))


@router.delete("/{key}")
async def delete_setting(
    key: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(WorkspaceSetting).where(
            WorkspaceSetting.tenant_id == current_user.tenant_id,
            WorkspaceSetting.key == key,
        )
    )
    row = result.scalar_one_or_none()
    if row:
        await db.delete(row)
        await db.commit()
    return {"success": True, "deleted": key}
