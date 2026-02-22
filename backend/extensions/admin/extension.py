"""Admin Extension — workspace admin panel."""
from __future__ import annotations
from saas_builder.core import ExtensionBase


class AdminExtension(ExtensionBase):
    name        = "admin"
    version     = "1.0.0"
    description = "Admin panel with workspace stats, user management, and extension oversight."
    author      = "SaaS Factory"
    dependencies: list[str] = []

    api_prefix  = "/admin"
    permissions = ["admin.read", "admin.write"]
    admin_menu  = [{"label": "Admin", "icon": "shield", "route": "/admin"}]

    def default_config(self) -> dict:
        return {}

    def on_install(self) -> None:
        pass

    def on_activate(self, app) -> None:
        from .routes import router
        app.include_router(router, prefix=f"/api/v1{self.api_prefix}")

    def on_deactivate(self, app) -> None:
        pass
