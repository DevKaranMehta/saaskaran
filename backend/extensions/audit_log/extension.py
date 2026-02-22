"""Audit Log Extension — track all workspace actions."""
from __future__ import annotations
from saas_builder.core import ExtensionBase


class AuditLogExtension(ExtensionBase):
    name        = "audit_log"
    version     = "1.0.0"
    description = "Full audit trail: log every action, resource change, and user event in your workspace."
    author      = "SaaS Factory"
    dependencies: list[str] = []

    api_prefix  = "/audit-log"
    permissions = ["audit_log.read", "audit_log.write"]
    admin_menu  = [{"label": "Audit Log", "icon": "activity", "route": "/admin/audit-log"}]

    def default_config(self) -> dict:
        return {"retention_days": 90}

    def on_install(self) -> None:
        from . import models  # noqa: F401

    def on_activate(self, app) -> None:
        from .routes import router
        app.include_router(router, prefix=f"/api/v1{self.api_prefix}")

    def on_deactivate(self, app) -> None:
        pass
