"""Live Chat Extension."""
from __future__ import annotations
from saas_builder.core import ExtensionBase


class LiveChatExtension(ExtensionBase):
    name = "live_chat"
    version = "1.0.0"
    description = "Embeddable live chat widget — receive visitor chats, reply from dashboard, track unread counts."
    author = "SaaS Factory"
    dependencies: list[str] = []

    api_prefix = "/live-chat"
    permissions = ["live_chat.read", "live_chat.write", "live_chat.admin"]

    def default_config(self) -> dict:
        return {
            "widget_color": "#6366f1",
            "widget_position": "bottom-right",
            "greeting": "Hi! How can we help you today?",
        }

    def on_install(self) -> None:
        from . import models  # noqa: F401

    def on_activate(self, app) -> None:
        from .routes import router
        app.include_router(router, prefix=f"/api/v1{self.api_prefix}")

    def on_deactivate(self, app) -> None:
        pass
