"""Invoicing & Billing Extension."""
from __future__ import annotations
from saas_builder.core import ExtensionBase


class InvoicingExtension(ExtensionBase):
    name        = "invoicing"
    version     = "1.0.0"
    description = "Full invoicing and billing module with clients, invoices, and line items."
    author      = "SaaS Factory"
    dependencies: list[str] = []
    api_prefix  = "/invoicing"
    permissions = ["invoicing.read", "invoicing.write"]
    admin_menu  = [{"label": "Invoicing", "icon": "file-invoice-dollar", "route": "/admin/invoicing"}]

    def default_config(self) -> dict:
        return {
            "default_currency": "USD",
            "default_tax_rate": 0.0,
            "invoice_number_prefix": "INV",
        }

    def on_install(self) -> None:
        from . import models  # noqa: F401

    def on_activate(self, app) -> None:
        from .routes import router
        app.include_router(router, prefix=f"/api/v1{self.api_prefix}")

    def on_deactivate(self, app) -> None:
        pass
