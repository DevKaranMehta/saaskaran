"""Theme Manager Extension — workspace theme customization."""
from __future__ import annotations
from saas_builder.core import ExtensionBase


class ThemeManagerExtension(ExtensionBase):
    name        = "theme_manager"
    version     = "1.0.0"
    description = "Customize your workspace theme: colors, fonts, logo, and dark/light mode."
    author      = "SaaS Factory"
    dependencies: list[str] = []

    api_prefix  = "/themes"
    permissions = ["themes.read", "themes.write"]
    admin_menu  = [{"label": "Themes", "icon": "palette", "route": "/admin/themes"}]

    def default_config(self) -> dict:
        return {"default_theme": "dark", "allow_custom_css": False}

    def on_install(self) -> None:
        from . import models  # noqa: F401

    def on_activate(self, app) -> None:
        from .routes import router
        app.include_router(router, prefix=f"/api/v1{self.api_prefix}")

    def on_deactivate(self, app) -> None:
        pass
