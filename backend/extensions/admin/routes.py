"""Admin — API routes."""
from __future__ import annotations
from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from api.auth import get_current_user
from api.database import get_db
from api.models import Tenant, TenantExtension, User

router = APIRouter(tags=["admin"])


@router.get("/stats")
async def workspace_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return admin stats for the current workspace."""
    user_count = await db.scalar(
        select(func.count()).select_from(User).where(User.tenant_id == current_user.tenant_id, User.is_active == True)
    )
    ext_count = await db.scalar(
        select(func.count()).select_from(TenantExtension).where(
            TenantExtension.tenant_id == current_user.tenant_id,
            TenantExtension.is_active == True,
        )
    )
    tenant_result = await db.execute(select(Tenant).where(Tenant.id == current_user.tenant_id))
    tenant = tenant_result.scalar_one_or_none()
    return {
        "workspace": {"name": tenant.name if tenant else "", "slug": tenant.slug if tenant else "", "id": current_user.tenant_id},
        "users": user_count or 0,
        "active_extensions": ext_count or 0,
    }


@router.get("/users")
async def list_users(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all users in this workspace."""
    result = await db.execute(
        select(User).where(User.tenant_id == current_user.tenant_id, User.is_active == True).order_by(User.name)
    )
    users = result.scalars().all()
    return [{"id": u.id, "name": u.name, "email": u.email, "role": u.role} for u in users]
