"""Roles — API routes."""
from __future__ import annotations
import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from api.auth import get_current_user
from api.database import get_db
from api.models import User
from .models import Role
from .schemas import RoleCreate, RoleResponse, RoleUpdate

router = APIRouter(tags=["roles"])


@router.get("/", response_model=list[RoleResponse])
async def list_roles(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Role).where(Role.tenant_id == current_user.tenant_id).order_by(Role.name))
    return [RoleResponse(id=r.id, name=r.name, description=r.description, permissions=r.permissions or [], is_default=r.is_default, created_at=str(r.created_at)) for r in result.scalars().all()]


@router.post("/", response_model=RoleResponse, status_code=201)
async def create_role(body: RoleCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    role = Role(id=str(uuid.uuid4()), tenant_id=current_user.tenant_id, **body.model_dump())
    db.add(role)
    await db.commit()
    await db.refresh(role)
    return RoleResponse(id=role.id, name=role.name, description=role.description, permissions=role.permissions or [], is_default=role.is_default, created_at=str(role.created_at))


@router.patch("/{role_id}", response_model=RoleResponse)
async def update_role(role_id: str, body: RoleUpdate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Role).where(Role.id == role_id, Role.tenant_id == current_user.tenant_id))
    role = result.scalar_one_or_none()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(role, field, value)
    await db.commit()
    await db.refresh(role)
    return RoleResponse(id=role.id, name=role.name, description=role.description, permissions=role.permissions or [], is_default=role.is_default, created_at=str(role.created_at))


@router.delete("/{role_id}")
async def delete_role(role_id: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Role).where(Role.id == role_id, Role.tenant_id == current_user.tenant_id))
    role = result.scalar_one_or_none()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    await db.delete(role)
    await db.commit()
    return {"success": True, "deleted": role_id}
