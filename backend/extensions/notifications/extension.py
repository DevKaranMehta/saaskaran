"""Notifications Extension — in-app notifications."""
from __future__ import annotations
from saas_builder.core import ExtensionBase


class NotificationsExtension(ExtensionBase):
    name        = "notifications"
    version     = "1.0.0"
    description = "In-app notification system: send, read, and manage notifications per user."
    author      = "SaaS Factory"
    dependencies: list[str] = []

    api_prefix  = "/notifications"
    permissions = ["notifications.read", "notifications.write"]
    admin_menu  = [{"label": "Notifications", "icon": "bell", "route": "/admin/notifications"}]

    def default_config(self) -> dict:
        return {"max_unread": 100}

    def on_install(self) -> None:
        from . import models  # noqa: F401

    def on_activate(self, app) -> None:
        from .routes import router
        app.include_router(router, prefix=f"/api/v1{self.api_prefix}")

    def on_deactivate(self, app) -> None:
        pass
