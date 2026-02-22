"""Settings Extension — workspace configuration."""
from __future__ import annotations
from saas_builder.core import ExtensionBase


class SettingsExtension(ExtensionBase):
    name        = "settings"
    version     = "1.0.0"
    description = "Workspace settings: name, timezone, logo, and custom configuration key-value pairs."
    author      = "SaaS Factory"
    dependencies: list[str] = []

    api_prefix  = "/settings"
    permissions = ["settings.read", "settings.write"]
    admin_menu  = [{"label": "Settings", "icon": "settings", "route": "/admin/settings"}]

    def default_config(self) -> dict:
        return {"allow_user_settings": True}

    def on_install(self) -> None:
        from . import models  # noqa: F401

    def on_activate(self, app) -> None:
        from .routes import router
        app.include_router(router, prefix=f"/api/v1{self.api_prefix}")

    def on_deactivate(self, app) -> None:
        pass
