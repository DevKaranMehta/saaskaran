"""Blog CMS — FastAPI routes."""
from __future__ import annotations
import re
import uuid
from datetime import UTC, datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth     import get_current_user
from api.database import get_db
from api.models   import User

from .models  import Category, Post
from .schemas import (
    CategoryCreate, CategoryResponse, CategoryUpdate,
    PostCreate, PostResponse, PostUpdate,
    VALID_STATUSES,
)

router = APIRouter(tags=["blog_cms"])


# ── Helpers ───────────────────────────────────────────────────────────────────

def _slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    text = re.sub(r"^-+|-+$", "", text)
    if not text:
        text = str(uuid.uuid4())[:8]
    return text


# ── Categories ────────────────────────────────────────────────────────────────

@router.get("/categories/", response_model=list[CategoryResponse])
async def list_categories(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Category)
        .where(Category.tenant_id == current_user.tenant_id)
        .order_by(Category.name.asc())
    )
    return result.scalars().all()


@router.post("/categories/", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
    payload: CategoryCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    slug = payload.slug.strip() if payload.slug else _slugify(payload.name)
    category = Category(
        tenant_id   = current_user.tenant_id,
        created_by  = current_user.id,
        name        = payload.name.strip(),
        slug        = slug,
        description = payload.description,
    )
    db.add(category)
    await db.commit()
    await db.refresh(category)
    return category


@router.get("/categories/{item_id}", response_model=CategoryResponse)
async def get_category(
    item_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Category).where(
            Category.id == item_id,
            Category.tenant_id == current_user.tenant_id,
        )
    )
    category = result.scalar_one_or_none()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return category


@router.patch("/categories/{item_id}", response_model=CategoryResponse)
async def update_category(
    item_id: str,
    payload: CategoryUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Category).where(
            Category.id == item_id,
            Category.tenant_id == current_user.tenant_id,
        )
    )
    category = result.scalar_one_or_none()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    data = payload.model_dump(exclude_unset=True)
    if "name" in data and "slug" not in data:
        data["slug"] = _slugify(data["name"])
    for field, value in data.items():
        setattr(category, field, value)
    await db.commit()
    await db.refresh(category)
    return category


@router.delete("/categories/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
    item_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Category).where(
            Category.id == item_id,
            Category.tenant_id == current_user.tenant_id,
        )
    )
    category = result.scalar_one_or_none()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    await db.delete(category)
    await db.commit()


# ── Posts ─────────────────────────────────────────────────────────────────────

@router.get("/", response_model=list[PostResponse])
async def list_posts(
    status_filter: str | None = Query(None, alias="status"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = select(Post).where(Post.tenant_id == current_user.tenant_id)
    if status_filter and status_filter in VALID_STATUSES:
        q = q.where(Post.status == status_filter)
    q = q.order_by(Post.created_at.desc())
    result = await db.execute(q)
    return result.scalars().all()


@router.post("/", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
async def create_post(
    payload: PostCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    raw_status = (payload.status or "draft").strip().lower()
    if raw_status not in VALID_STATUSES:
        raw_status = "draft"

    slug = payload.slug.strip() if payload.slug else _slugify(payload.title)

    pub_at = payload.published_at
    if raw_status == "published" and pub_at is None:
        pub_at = datetime.now(UTC)

    post = Post(
        tenant_id          = current_user.tenant_id,
        created_by         = current_user.id,
        category_id        = payload.category_id,
        title              = payload.title.strip(),
        slug               = slug,
        content            = payload.content,
        excerpt            = payload.excerpt,
        status             = raw_status,
        published_at       = pub_at,
        featured_image_url = payload.featured_image_url,
        tags               = payload.tags,
    )
    db.add(post)
    await db.commit()
    await db.refresh(post)
    return post


@router.get("/{item_id}", response_model=PostResponse)
async def get_post(
    item_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Post).where(
            Post.id == item_id,
            Post.tenant_id == current_user.tenant_id,
        )
    )
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return post


@router.patch("/{item_id}", response_model=PostResponse)
async def update_post(
    item_id: str,
    payload: PostUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Post).where(
            Post.id == item_id,
            Post.tenant_id == current_user.tenant_id,
        )
    )
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    data = payload.model_dump(exclude_unset=True)

    if "status" in data:
        raw_status = data["status"].strip().lower()
        data["status"] = raw_status if raw_status in VALID_STATUSES else "draft"
        if data["status"] == "published" and post.published_at is None and "published_at" not in data:
            data["published_at"] = datetime.now(UTC)

    if "title" in data and "slug" not in data:
        data["slug"] = _slugify(data["title"])

    for field, value in data.items():
        setattr(post, field, value)

    await db.commit()
    await db.refresh(post)
    return post


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(
    item_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Post).where(
            Post.id == item_id,
            Post.tenant_id == current_user.tenant_id,
        )
    )
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    await db.delete(post)
    await db.commit()
