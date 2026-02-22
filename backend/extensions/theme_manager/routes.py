"""Theme Manager — API routes."""
from __future__ import annotations
import uuid
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from api.auth import get_current_user
from api.database import get_db
from api.models import User
from .models import ThemeConfig
from .schemas import ThemeResponse, ThemeUpdate

router = APIRouter(tags=["themes"])

THEME_PRESETS = ["dark", "light", "ocean", "forest", "sunset"]


@router.get("/presets")
async def list_presets(current_user: User = Depends(get_current_user)):
    return {"presets": THEME_PRESETS}


@router.get("/config", response_model=ThemeResponse | None)
async def get_theme(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(ThemeConfig).where(ThemeConfig.tenant_id == current_user.tenant_id))
    cfg = result.scalar_one_or_none()
    if not cfg:
        return None
    return ThemeResponse(id=cfg.id, theme_name=cfg.theme_name, primary_color=cfg.primary_color, logo_url=cfg.logo_url, config=cfg.config or {})


@router.put("/config", response_model=ThemeResponse)
async def upsert_theme(body: ThemeUpdate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(ThemeConfig).where(ThemeConfig.tenant_id == current_user.tenant_id))
    cfg = result.scalar_one_or_none()
    if cfg:
        for field, value in body.model_dump(exclude_none=True).items():
            setattr(cfg, field, value)
    else:
        data = body.model_dump(exclude_none=True)
        cfg = ThemeConfig(id=str(uuid.uuid4()), tenant_id=current_user.tenant_id, **data)
        db.add(cfg)
    await db.commit()
    await db.refresh(cfg)
    return ThemeResponse(id=cfg.id, theme_name=cfg.theme_name, primary_color=cfg.primary_color, logo_url=cfg.logo_url, config=cfg.config or {})
