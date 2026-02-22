"""Marketplace — Pydantic schemas."""
from __future__ import annotations
from typing import Optional
from pydantic import BaseModel


class ListingCreate(BaseModel):
    name: str
    display_name: str
    description: Optional[str] = None
    version: str = "1.0.0"
    author: str
    price: float = 0.0
    tags: list[str] = []


class ListingResponse(BaseModel):
    id: str
    name: str
    display_name: str
    description: Optional[str]
    version: str
    author: str
    price: float
    tags: list
    download_count: int
    is_approved: bool

    class Config:
        from_attributes = True
