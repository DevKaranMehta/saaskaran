"""Auth routes: register, login, me."""

from __future__ import annotations

import asyncio
import logging
from typing import Annotated

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth import create_access_token, get_current_user, hash_password, verify_password
from ..database import get_db
from ..models import Tenant, User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

AI_LAYER_URL = "http://127.0.0.1:8010"


async def _register_subdomain(tenant_id: str, slug: str) -> None:
    """Fire-and-forget: ask AI Layer to register a Traefik subdomain for this tenant."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.post(
                f"{AI_LAYER_URL}/envs",
                json={"tenant_id": tenant_id, "slug": slug},
            )
            if resp.status_code in (200, 201):
                data = resp.json()
                env = data.get("environment", {})
                logger.info(
                    "Subdomain registered: %s (env_id=%s)",
                    env.get("subdomain_url"), env.get("env_id"),
                )
            else:
                logger.warning("Subdomain registration returned %s: %s", resp.status_code, resp.text[:200])
    except Exception as exc:
        # Non-fatal — registration can be retried or done manually
        logger.warning("Could not register subdomain for tenant %s: %s", tenant_id, exc)


class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    tenant_name: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(body: RegisterRequest, db: Annotated[AsyncSession, Depends(get_db)]):
    # Check email not taken
    existing = await db.execute(select(User).where(User.email == body.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    # Create tenant
    slug = body.tenant_name.lower().replace(" ", "-")[:50]
    tenant = Tenant(name=body.tenant_name, slug=slug)
    db.add(tenant)
    await db.flush()

    # Create user
    user = User(
        tenant_id=tenant.id,
        email=body.email,
        name=body.name,
        hashed_password=hash_password(body.password),
        role="owner",
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    token = create_access_token(user.id, tenant.id, user.role)

    # Register subdomain in background — non-blocking, non-fatal
    asyncio.create_task(_register_subdomain(tenant.id, slug))

    return TokenResponse(
        access_token=token,
        user={
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role,
            "subdomain": f"https://{slug}.factory.supportbox.cloud",
        },
    )


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(User).where(User.email == body.email, User.is_active == True))
    user = result.scalar_one_or_none()

    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Fetch tenant slug for subdomain URL
    tenant_result = await db.execute(select(Tenant).where(Tenant.id == user.tenant_id))
    tenant = tenant_result.scalar_one_or_none()
    slug = tenant.slug if tenant else ""

    token = create_access_token(user.id, user.tenant_id, user.role)
    return TokenResponse(
        access_token=token,
        user={
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role,
            "tenant_slug": slug,
            "subdomain": f"https://{slug}.factory.supportbox.cloud" if slug else "",
        },
    )


@router.get("/me")
async def me(user: Annotated[User, Depends(get_current_user)], db: Annotated[AsyncSession, Depends(get_db)]):
    tenant_result = await db.execute(select(Tenant).where(Tenant.id == user.tenant_id))
    tenant = tenant_result.scalar_one_or_none()
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "role": user.role,
        "tenant_id": user.tenant_id,
        "tenant_name": tenant.name if tenant else "",
        "tenant_slug": tenant.slug if tenant else "",
        "subdomain": f"https://{tenant.slug}.factory.supportbox.cloud" if tenant else "",
    }


@router.get("/workspace/{slug}")
async def workspace_info(slug: str, db: Annotated[AsyncSession, Depends(get_db)]):
    """Public endpoint — returns workspace branding for the subdomain login page."""
    result = await db.execute(select(Tenant).where(Tenant.slug == slug, Tenant.is_active == True))
    tenant = result.scalar_one_or_none()
    if not tenant:
        raise HTTPException(status_code=404, detail="Workspace not found")
    return {"name": tenant.name, "slug": tenant.slug, "exists": True}
