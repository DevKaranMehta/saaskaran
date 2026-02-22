"""ExtensionManager — handles install/activate/deactivate lifecycle per tenant."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert

from .base import ExtensionBase
from .event_bus import event_bus
from .registry import ExtensionRegistry

if TYPE_CHECKING:
    from fastapi import FastAPI
    from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class ExtensionManager:
    """Manages the full lifecycle of extensions across tenants."""

    def __init__(self, app: "FastAPI", registry: ExtensionRegistry | None = None) -> None:
        self.app = app
        self.registry = registry or ExtensionRegistry()
        self._mounted: set[str] = set()

    # ── Route mounting ───────────────────────────────────────────

    def mount_all(self) -> None:
        """Mount API routes for every registered extension (called once at startup)."""
        for name, ext in self.registry.all().items():
            self._mount(ext)
        logger.info("Mounted routes for %d extensions", len(self._mounted))

    def _mount(self, ext: ExtensionBase) -> None:
        """Mount routes for a single extension (idempotent)."""
        if ext.name in self._mounted:
            return
        try:
            ext.on_activate(self.app)
            self._mounted.add(ext.name)
            logger.debug("Mounted extension: %s", ext.name)
        except Exception:
            logger.exception("Failed to mount extension: %s", ext.name)

    # ── Tenant lifecycle ─────────────────────────────────────────

    async def install(self, name: str, tenant_id: str, db: "AsyncSession") -> dict[str, Any]:
        from api.models import TenantExtension

        ext = self.registry.get(name)
        if not ext:
            return {"success": False, "error": f"Extension '{name}' not found"}

        for dep in ext.dependencies:
            if not self.registry.get(dep):
                return {"success": False, "error": f"Missing dependency: {dep}"}

        try:
            ext.on_install()

            # Upsert: install if not already installed
            stmt = insert(TenantExtension).values(
                tenant_id=tenant_id,
                extension_name=name,
                is_active=False,
            ).on_conflict_do_nothing()
            await db.execute(stmt)
            await db.commit()

            await event_bus.publish("extension.installed", {"extension": name, "tenant_id": tenant_id})
            logger.info("Installed extension '%s' for tenant %s", name, tenant_id)
            return {"success": True}
        except Exception as e:
            await db.rollback()
            logger.exception("Failed to install extension '%s'", name)
            return {"success": False, "error": str(e)}

    async def activate(self, name: str, tenant_id: str, db: "AsyncSession") -> dict[str, Any]:
        from api.models import TenantExtension
        from datetime import UTC, datetime

        ext = self.registry.get(name)
        if not ext:
            return {"success": False, "error": f"Extension '{name}' not found"}

        try:
            # Ensure installed first (upsert)
            stmt = insert(TenantExtension).values(
                tenant_id=tenant_id,
                extension_name=name,
                is_active=True,
                activated_at=datetime.now(UTC),
            ).on_conflict_do_update(
                index_elements=["tenant_id", "extension_name"],
                set_={"is_active": True, "activated_at": datetime.now(UTC)},
            )
            await db.execute(stmt)
            await db.commit()

            await event_bus.publish("extension.activated", {"extension": name, "tenant_id": tenant_id})
            return {"success": True}
        except Exception as e:
            await db.rollback()
            logger.exception("Failed to activate extension '%s'", name)
            return {"success": False, "error": str(e)}

    async def deactivate(self, name: str, tenant_id: str, db: "AsyncSession") -> dict[str, Any]:
        from api.models import TenantExtension

        ext = self.registry.get(name)
        if not ext:
            return {"success": False, "error": f"Extension '{name}' not found"}

        try:
            stmt = (
                update(TenantExtension)
                .where(
                    TenantExtension.tenant_id == tenant_id,
                    TenantExtension.extension_name == name,
                )
                .values(is_active=False)
            )
            await db.execute(stmt)
            await db.commit()

            await event_bus.publish("extension.deactivated", {"extension": name, "tenant_id": tenant_id})
            return {"success": True}
        except Exception as e:
            await db.rollback()
            return {"success": False, "error": str(e)}

    async def notify_tenant_created(self, tenant_id: str, schema: str) -> None:
        """Notify all active extensions that a new tenant was created."""
        for ext in self.registry.all().values():
            try:
                ext.on_tenant_created(tenant_id, schema)
            except Exception:
                logger.exception("Extension '%s' failed on tenant_created", ext.name)
        await event_bus.publish("tenant.created", {"tenant_id": tenant_id, "schema": schema})
