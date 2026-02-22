"""Auth Extension — platform authentication stub."""
from __future__ import annotations
from saas_builder.core import ExtensionBase


class AuthExtension(ExtensionBase):
    name        = "auth"
    version     = "1.0.0"
    description = "User authentication, JWT tokens, and session management. Built into the platform core."
    author      = "SaaS Factory"
    dependencies: list[str] = []

    api_prefix  = "/auth-ext"
    permissions = ["auth.read"]
    admin_menu  = []

    def default_config(self) -> dict:
        return {"session_duration_days": 7, "allow_registration": True}

    def on_install(self) -> None:
        pass

    def on_activate(self, app) -> None:
        pass

    def on_deactivate(self, app) -> None:
        pass
