"""Form Builder Extension."""
from __future__ import annotations
from saas_builder.core import ExtensionBase


class FormBuilderExtension description = "Build embeddable forms, generate embed code, and track submissions."
    author      = "SaaS Factory"
    dependencies: list[str] = []

    api_prefix  = "/form-builder"
    permissions = ["form_builder.read", "form_builder.write"]
    admin_menu  = [{"label": "Form Builder", "icon": "layout", "route": "/admin/form-builder"}]

    def default_config(self) -> dict:
        return {"max_forms_per_tenant": 50, "max_submissions_per_form": 10000}

    def on_install(self) -> None:
        from . import models  # noqa: F401

    def on_activate(self, app) -> None:
        from .routes import router
        app.include_router(router, prefix=f"/api/v1{self.api_prefix}")

    def on_deactivate(self, app) -> None:
        pass
