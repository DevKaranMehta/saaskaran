"""Billing Extension — subscription plans and payments."""
from __future__ import annotations
from saas_builder.core import ExtensionBase


class BillingExtension(ExtensionBase):
    name        = "billing"
    version     = "1.0.0"
    description = "Subscription plans, tenant subscriptions, and payment tracking."
    author      = "SaaS Factory"
    dependencies: list[str] = []

    api_prefix  = "/billing"
    permissions = ["billing.read", "billing.write", "billing.admin"]
    admin_menu  = [{"label": "Billing", "icon": "credit-card", "route": "/admin/billing"}]

    def default_config(self) -> dict:
        return {"currency": "USD", "trial_days": 14}

    def on_install(self) -> None:
        from . import models  # noqa: F401

    def on_activate(self, app) -> None:
        from .routes import router
        app.include_router(router, prefix=f"/api/v1{self.api_prefix}")

    def on_deactivate(self, app) -> None:
        pass
