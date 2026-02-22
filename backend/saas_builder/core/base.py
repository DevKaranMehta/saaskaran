"""ExtensionBase — the contract every extension must follow."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from fastapi import FastAPI


class ExtensionBase(ABC):
    # ── Required metadata ────────────────────────────────────────
    name: str = ""
    version: str = "1.0.0"
    description: str = ""
    author: str = "SaaS Factory"
    dependencies: list[str] = []

    # ── Optional platform config ─────────────────────────────────
    api_prefix: str = ""
    permissions: list[str] = []
    admin_menu: list[dict[str, str]] = []
    models: list[Any] = []

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        if not cls.name:
            raise TypeError(f"{cls.__name__} must define a non-empty `name`")

    # ── Lifecycle hooks ──────────────────────────────────────────

    def default_config(self) -> dict[str, Any]:
        """Return default configuration values for this extension."""
        return {}

    def on_install(self) -> None:
        """Called once when extension is first installed.
        Create DB tables, seed initial data, etc.
        """

    def on_activate(self, app: "FastAPI") -> None:
        """Called every time the extension is enabled.
        Mount routes, subscribe to events, register middleware.
        """

    def on_deactivate(self, app: "FastAPI") -> None:
        """Called every time the extension is disabled.
        Unmount routes, unsubscribe from events.
        """

    def on_uninstall(self) -> None:
        """Called once when extension is permanently removed.
        Drop tables, clean up all data.
        """

    def on_tenant_created(self, tenant_id: str, schema: str) -> None:
        """Called when a new tenant is provisioned.
        Seed per-tenant data, create tenant-specific tables.
        """

    def on_tenant_deleted(self, tenant_id: str) -> None:
        """Called when a tenant is removed."""

    # ── Info helpers ─────────────────────────────────────────────

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "author": self.author,
            "dependencies": self.dependencies,
            "api_prefix": self.api_prefix,
            "permissions": self.permissions,
            "admin_menu": self.admin_menu,
        }

    def __repr__(self) -> str:
        return f"<Extension {self.name} v{self.version}>"
