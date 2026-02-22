"""Customer Portal Extension — ticket management for customer support."""
from __future__ import annotations
from saas_builder.core import ExtensionBase


class CustomerPortalExtension(ExtensionBase):
    name        = "customer_portal"
    version     = "1.0.0"
    description = "Customer support ticket system with priorities, categories, replies, and stats."
    author      = "SaaS Factory"
    dependencies: list[str] = []
    api_prefix  = "/customer-portal"
    permissions = ["customer_portal.read", "customer_portal.write"]
    admin_menu  = [{"label": "Customer Portal", "icon": "ticket", "route": "/admin/customer-portal"}]

    def default_config(self) -> dict:
        return {"max_tickets_per_tenant": 10000}

    def on_install(self) -> None:
        from . import models  # noqa: F401

    def on_activate(self, app) -> None:
        from .routes import router
        app.include_router(router, prefix=f"/api/v1{self.api_prefix}")

    def on_deactivate(self, app) -> None:
        pass
