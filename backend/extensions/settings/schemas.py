"""Settings — Pydantic schemas."""
from __future__ import annotations
from pydantic import BaseModel


class SettingUpsert(BaseModel):
    key: str
    value: str | None = None


class SettingResponse(BaseModel):
    id: str
    key: str
    value: str | None
    updated_at: str

    class Config:
        from_attributes = True
