"""Form Builder — Pydantic schemas."""
from __future__ import annotations
import uuid
from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, Field


class FieldConfig(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: str = Field(..., description="text|textarea|email|number|select|checkbox|date|phone|url")
    label: str = Field(..., min_length=1, max_length=255)
    placeholder: Optional[str] = None
    required: bool = False
    options: list[str] = Field(default_factory=list)
    order: int = 0


class FormCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    fields: list[FieldConfig] = Field(default_factory=list)
    is_active: bool = True
    submit_button_text: str = Field(default="Submit", max_length=100)
    success_message: str = Field(default="Thank you for your submission!", max_length=500)


class FormUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    fields: Optional[list[FieldConfig]] = None
    is_active: Optional[bool] = None
    submit_button_text: Optional[str] = Field(None, max_length=100)
    success_message: Optional[str] = Field(None, max_length=500)


class FormResponse(BaseModel):
    id: str
    tenant_id: str
    created_by: str
    name: str
    description: Optional[str]
    fields: list[Any]
    is_active: bool
    submit_button_text: str
    success_message: str
    embed_token: str
    submission_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PublicFormResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    fields: list[Any]
    submit_button_text: str
    success_message: str

    class Config:
        from_attributes = True


class FormSubmissionCreate(BaseModel):
    data: dict[str, Any]


class FormSubmissionResponse(BaseModel):
    id: str
    tenant_id: str
    form_id: str
    created_by: str
    data: dict[str, Any]
    ip_address: Optional[str]
    user_agent: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class EmbedCodeResponse(BaseModel):
    form_id: str
    embed_token: str
    embed_code: str
