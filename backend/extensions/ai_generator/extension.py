"""AI Generator Extension — generates SaaS Builder extensions via Claude."""

from __future__ import annotations

from saas_builder.core import ExtensionBase, event_bus


class AiGeneratorExtension(ExtensionBase):
    name = "ai_generator"
    version = "1.0.0"
    description = "AI-powered extension generator using Claude. Describe what you want, get production-ready code."
    author = "SaaS Factory"
    api_prefix = "/ai"
    permissions = ["ai_generator.use"]
    admin_menu = [{"label": "AI Builder", "icon": "sparkles", "route": "/dashboard/ai"}]

    def on_activate(self, app) -> None:
        from .routes import router
        app.include_router(router, prefix="/api/v1/ai", tags=["ai-generator"])
