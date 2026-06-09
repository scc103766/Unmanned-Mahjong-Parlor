from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class TenantCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    status: str = Field(default="active", max_length=32)
    plan: Optional[str] = Field(default=None, max_length=64)
    settings: dict[str, object] = Field(default_factory=dict)


class TenantUpdateRequest(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=120)
    status: Optional[str] = Field(default=None, max_length=32)
    plan: Optional[str] = Field(default=None, max_length=64)
    settings: Optional[dict[str, object]] = None


class TenantResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    status: str
    plan: Optional[str] = None
    settings: dict[str, object] = Field(default_factory=dict)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class TenantAppCreateRequest(BaseModel):
    client_type: str = Field(default="h5", min_length=1, max_length=32)
    app_id: str = Field(min_length=1, max_length=128)
    mch_id: Optional[str] = Field(default=None, max_length=128)
    secret_ref: Optional[str] = Field(default=None, max_length=256)
    status: str = Field(default="active", max_length=32)


class TenantAppResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    client_type: str
    app_id: str
    mch_id: Optional[str] = None
    secret_ref: Optional[str] = None
    status: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
