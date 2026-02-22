"""Blog CMS — Pydantic schemas."""
from __future__ import annotations
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


# ── Category ──────────────────────────────────────────────────────────────────

class CategoryCreate(BaseModel):
    name:        str           = Field(..., min_length=1, max_length=255)
    slug:        Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None


class CategoryUpdate(BaseModel):
    name:        Optional[str] = Field(None, min_length=1, max_length=255)
    slug:        Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None


class CategoryResponse(BaseModel):
    id:          str
    tenant_id:   str
    name:        str
    slug:        str
    description: Optional[str]
    created_by:  str
    created_at:  datetime
    updated_at:  datetime

    class Config:
        from_attributes = True


# ── Post ──────────────────────────────────────────────────────────────────────

VALID_STATUSES = {"draft", "published", "archived"}


class PostCreate(BaseModel):
    title:              str            = Field(..., min_length=1, max_length=255)
    slug:               Optional[str]  = Field(None, max_length=255)
    category_id:        Optional[str]  = None
    content:            Optional[str]  = None
    excerpt:            Optional[str]  = None
    status:             str            = "draft"
    published_at:       Optional[datetime] = None
    featured_image_url: Optional[str]  = Field(None, max_length=500)
    tags:               list[str]      = Field(default_factory=list)


class PostUpdate(BaseModel):
    title:              Optional[str]  = Field(None, min_length=1, max_length=255)
    slug:               Optional[str]  = Field(None, max_length=255)
    category_id:        Optional[str]  = None
    content:            Optional[str]  = None
    excerpt:            Optional[str]  = None
    status:             Optional[str]  = None
    published_at:       Optional[datetime] = None
    featured_image_url: Optional[str]  = Field(None, max_length=500)
    tags:               Optional[list[str]] = None


class PostResponse(BaseModel):
    id:                 str
    tenant_id:          str
    category_id:        Optional[str]
    title:              str
    slug:               str
    content:            Optional[str]
    excerpt:            Optional[str]
    status:             str
    published_at:       Optional[datetime]
    featured_image_url: Optional[str]
    tags:               list[str]
    view_count:         int
    created_by:         str
    created_at:         datetime
    updated_at:         datetime

    class Config:
        from_attributes = True
