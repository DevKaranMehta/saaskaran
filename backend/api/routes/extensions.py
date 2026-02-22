"""Extension management routes."""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth import get_current_user
from ..database import get_db, create_tables
from ..models import TenantExtension, User

router = APIRouter(prefix="/api/v1/extensions", tags=["extensions"])


@router.get("/")
async def list_extensions(
    request: Request,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """List all registered extensions with activation status for this tenant."""
    registry = request.app.state.ext_registry

    # Get all active extension names for this tenant
    result = await db.execute(
        select(TenantExtension.extension_name, TenantExtension.is_active)
        .where(TenantExtension.tenant_id == user.tenant_id)
    )
    tenant_status = {row.extension_name: row.is_active for row in result}

    all_exts = registry.all()
    return {
        "extensions": [
            {**ext.to_dict(), "installed": ext.name in tenant_status, "active": tenant_status.get(ext.name, False)}
            for ext in all_exts.values()
        ]
    }


@router.post("/{name}/install")
async def install_extension(
    name: str,
    request: Request,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    manager = request.app.state.ext_manager
    result = await manager.install(name, user.tenant_id, db)
    return result


@router.post("/{name}/activate")
async def activate_extension(
    name: str,
    request: Request,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    manager = request.app.state.ext_manager
    result = await manager.activate(name, user.tenant_id, db)
    return result


@router.post("/internal/reload")
async def reload_extensions(request: Request):
    """Hot-reload: discover new extensions written to disk, create their DB tables, mount routes.
    No auth required — internal use only (called by AI after writing extension files).
    """
    registry = request.app.state.ext_registry
    manager  = request.app.state.ext_manager

    extensions_path = Path(__file__).parent.parent.parent / "extensions"

    # Force Python to re-import modules for any already-seen extension folders
    # (in case files were overwritten)
    for key in list(sys.modules.keys()):
        if key.startswith("extensions."):
            del sys.modules[key]

    before = set(registry.names())
    registry.discover(extensions_path)
    after  = set(registry.names())
    new    = sorted(after - before)

    # Mount routes for newly discovered extensions
    manager.mount_all()

    # Create any new DB tables the extensions define
    await create_tables()

    return {
        "success": True,
        "total": len(after),
        "new_extensions": new,
        "all_extensions": sorted(after),
    }


@router.get("/{name}/ui-spec")
async def get_ui_spec(
    name: str,
    user: Annotated[User, Depends(get_current_user)],
):
    """Return the ui_spec.json for an extension (powers the generic UI renderer)."""
    spec_path = Path(__file__).parent.parent.parent / "extensions" / name / "ui_spec.json"
    if not spec_path.exists():
        raise HTTPException(status_code=404, detail="No UI spec found for this extension")
    return json.loads(spec_path.read_text())


@router.post("/{name}/deactivate")
async def deactivate_extension(
    name: str,
    request: Request,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    manager = request.app.state.ext_manager
    result = await manager.deactivate(name, user.tenant_id, db)
    return result


@router.delete("/{name}")
async def delete_extension(
    name: str,
    request: Request,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Permanently delete an extension: deactivate, remove DB record, delete files."""
    from sqlalchemy import delete as sql_delete

    registry = request.app.state.ext_registry
    manager  = request.app.state.ext_manager

    # Deactivate first if active
    if name in registry.names():
        try:
            await manager.deactivate(name, user.tenant_id, db)
        except Exception:
            pass

    # Remove from DB
    await db.execute(
        sql_delete(TenantExtension).where(
            TenantExtension.extension_name == name,
            TenantExtension.tenant_id == user.tenant_id,
        )
    )
    await db.commit()

    # Remove from registry
    registry._extensions.pop(name, None)

    # Delete files from disk
    ext_path = Path(__file__).parent.parent.parent / "extensions" / name
    if ext_path.exists():
        shutil.rmtree(ext_path)

    # Clean up Python module cache
    for key in list(sys.modules.keys()):
        if key.startswith(f"extensions.{name}"):
            del sys.modules[key]

    return {"success": True, "deleted": name}
