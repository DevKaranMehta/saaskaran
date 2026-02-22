"""Marketplace Extension — browse and share extensions."""
from __future__ import annotations
from saas_builder.core import ExtensionBase


class MarketplaceExtension(ExtensionBase):
    name        = "marketplace"
    version     = "1.0.0"
    description = "Browse, install, and publish extensions to the SaaS Factory marketplace."
    author      = "SaaS Factory"
    dependencies: list[str] = []

    api_prefix  = "/marketplace"
    permissions = ["marketplace.read", "marketplace.publish"]
    admin_menu  = [{"label": "Marketplace", "icon": "store", "route": "/admin/marketplace"}]

    def default_config(self) -> dict:
        return {"allow_publish": True}

    def on_install(self) -> None:
        from . import models  # noqa: F401

    def on_activate(self, app) -> None:
        from .routes import router
        app.include_router(router, prefix=f"/api/v1{self.api_prefix}")

    def on_deactivate(self, app) -> None:
        pass
