"""Blog CMS — SQLAlchemy models."""
from __future__ import annotations
import uuid
from datetime import UTC, datetime
from sqlalchemy import String, Text, JSON, Boolean, Float
from sqlalchemy import DateTime as SADateTime
from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from api.database import Base


def utcnow() -> datetime:
    return datetime.now(UTC)


class Category(Base):
    __tablename__ = "ext_blog_categories"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    tenant_id:   Mapped[str]       = mapped_column(UUID(as_uuid=False), nullable=False, index=True)
    name:        Mapped[str]       = mapped_column(String(255), nullable=False)
    slug:        Mapped[str]       = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by:  Mapped[str]       = mapped_column(UUID(as_uuid=False), nullable=False)
    created_at:  Mapped[datetime]  = mapped_column(SADateTime(timezone=True), default=utcnow, nullable=False)
    updated_at:  Mapped[datetime]  = mapped_column(SADateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    posts: Mapped[list["Post"]] = relationship(
        "Post", back_populates="category", cascade="all, delete-orphan", lazy="selectin"
    )


class Post(Base):
    __tablename__ = "ext_blog_posts"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    tenant_id:         Mapped[str]        = mapped_column(UUID(as_uuid=False), nullable=False, index=True)
    category_id:       Mapped[str | None] = mapped_column(
        UUID(as_uuid=False), ForeignKey("ext_blog_categories.id", ondelete="SET NULL"),
        nullable=True, index=True
    )
    title:             Mapped[str]        = mapped_column(String(255), nullable=False)
    slug:              Mapped[str]        = mapped_column(String(255), nullable=False, index=True)
    content:           Mapped[str | None] = mapped_column(Text, nullable=True)
    excerpt:           Mapped[str | None] = mapped_column(Text, nullable=True)
    status:            Mapped[str]        = mapped_column(String(50), default="draft", nullable=False, index=True)
    published_at:      Mapped[datetime | None] = mapped_column(SADateTime(timezone=True), nullable=True)
    featured_image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    tags:              Mapped[list]       = mapped_column(JSON, default=list, nullable=False)
    view_count:        Mapped[int]        = mapped_column(default=0, nullable=False)
    created_by:        Mapped[str]        = mapped_column(UUID(as_uuid=False), nullable=False)
    created_at:        Mapped[datetime]   = mapped_column(SADateTime(timezone=True), default=utcnow, nullable=False)
    updated_at:        Mapped[datetime]   = mapped_column(SADateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    category: Mapped["Category | None"] = relationship("Category", back_populates="posts", lazy="selectin")
