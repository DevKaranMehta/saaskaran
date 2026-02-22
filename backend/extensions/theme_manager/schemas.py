"""Theme Manager — Pydantic schemas."""
from __future__ import annotations
from typing import Optional
from pydantic import BaseModel


class ThemeUpdate(BaseModel):
    theme_name: Optional[str] = None
    primary_color: Optional[str] = None
    logo_url: Optional[str] = None
    config: Optional[dict] = None


class ThemeResponse(BaseModel):
    id: str
    theme_name: str
    primary_color: str
    logo_url: Optional[str]
    config: dict

    class Config:
        from_attributes = True
