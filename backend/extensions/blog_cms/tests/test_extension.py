"""Blog CMS extension tests."""
import pytest


def test_extension_name():
    from extensions.blog_cms.extension import BlogCmsExtension
    ext = BlogCmsExtension()
    assert ext.name == "blog_cms"
    assert ext.api_prefix == "/blog-cms"


def test_model_tablenames():
    from extensions.blog_cms.models import Category, Post
    assert Category.__tablename__ == "ext_blog_categories"
    assert Post.__tablename__ == "ext_blog_posts"


def test_valid_statuses():
    from extensions.blog_cms.schemas import VALID_STATUSES
    assert "draft" in VALID_STATUSES
    assert "published" in VALID_STATUSES
    assert "archived" in VALID_STATUSES


def test_status_is_string_column():
    from extensions.blog_cms.models import Post
    from sqlalchemy import String
    col = Post.__table__.c["status"]
    assert isinstance(col.type, String), "status must be String(50), not a PG Enum"
