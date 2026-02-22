"""Blog CMS Extension."""
from __future__ import annotations
from saas_builder.core import ExtensionBase


class BlogCmsExtension(ExtensionBase):
    name        = "blog_cms"
    version     = "1.0.0"
    description = "Full blog CMS with categories, posts, and tag management."
    author      = "SaaS Factory"
    dependencies: list[str] = []

    api_prefix  = "/blog-cms"
    permissions = ["blog_cms.read", "blog_cms.write"]
    admin_menu  = [{"label": "Blog CMS", "icon": "book-open", "route": "/admin/blog-cms"}]

    def default_config(self) -> dict:
        return {"max_posts_per_tenant": 10000}

    def on_install(self) -> None:
        from . import models  # noqa: F401

    def on_activate(self, app) -> None:
        from .routes import router
        app.include_router(router, prefix=f"/api/v1{self.api_prefix}")

    def on_deactivate(self, app) -> None:
        pass
