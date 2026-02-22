"""Roles Extension — role-based access control."""
from __future__ import annotations
from saas_builder.core import ExtensionBase


class RolesExtension(ExtensionBase):
    name        = "roles"
    version     = "1.0.0"
    description = "Role-based access control: create roles, assign permissions, and control feature access."
    author      = "SaaS Factory"
    dependencies: list[str] = []

    api_prefix  = "/roles"
    permissions = ["roles.read", "roles.write", "roles.admin"]
    admin_menu  = [{"label": "Roles", "icon": "users", "route": "/admin/roles"}]

    def default_config(self) -> dict:
        return {"default_role": "member"}

    def on_install(self) -> None:
        from . import models  # noqa: F401

    def on_activate(self, app) -> None:
        from .routes import router
        app.include_router(router, prefix=f"/api/v1{self.api_prefix}")

    def on_deactivate(self, app) -> None:
        pass
