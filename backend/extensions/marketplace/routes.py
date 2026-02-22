"""Marketplace — API routes."""
from __future__ import annotations
import uuid
from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from api.auth import get_current_user
from api.database import get_db
from api.models import User
from .models import MarketplaceListing
from .schemas import ListingCreate, ListingResponse

router = APIRouter(tags=["marketplace"])


@router.get("/listings", response_model=list[ListingResponse])
async def list_marketplace(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Return all approved marketplace listings."""
    result = await db.execute(
        select(MarketplaceListing).where(MarketplaceListing.is_approved == True, MarketplaceListing.is_active == True).order_by(MarketplaceListing.download_count.desc())
    )
    items = result.scalars().all()
    return [ListingResponse(id=i.id, name=i.name, display_name=i.display_name, description=i.description, version=i.version, author=i.author, price=float(i.price), tags=i.tags or [], download_count=i.download_count, is_approved=i.is_approved) for i in items]


@router.get("/installed", response_model=list[dict])
async def installed_extensions(request: Request, current_user: User = Depends(get_current_user)):
    """Return the registry extensions as marketplace cards."""
    registry = request.app.state.ext_registry
    return [{"name": e.name, "display_name": e.name.replace("_", " ").title(), "description": e.description, "version": e.version, "author": e.author} for e in registry.all().values()]


@router.post("/listings", response_model=ListingResponse, status_code=201)
async def publish_listing(body: ListingCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    listing = MarketplaceListing(id=str(uuid.uuid4()), tenant_id=current_user.tenant_id, **body.model_dump())
    db.add(listing)
    await db.commit()
    await db.refresh(listing)
    return ListingResponse(id=listing.id, name=listing.name, display_name=listing.display_name, description=listing.description, version=listing.version, author=listing.author, price=float(listing.price), tags=listing.tags or [], download_count=listing.download_count, is_approved=listing.is_approved)
