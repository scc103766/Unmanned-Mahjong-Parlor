from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class StoreCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    address: Optional[str] = Field(default=None, max_length=256)
    longitude: Optional[float] = None
    latitude: Optional[float] = None
    notice: Optional[str] = Field(default=None, max_length=512)
    contact_phone: Optional[str] = Field(default=None, max_length=32)
    wifi_ssid: Optional[str] = Field(default=None, max_length=128)
    wifi_password: Optional[str] = Field(default=None, max_length=128)
    images: list[str] = Field(default_factory=list)
    business_settings: dict[str, object] = Field(default_factory=dict)
    cleaning_settings: dict[str, object] = Field(default_factory=dict)
    status: str = Field(default="active", max_length=32)
    sort_order: int = 0


class StoreUpdateRequest(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=120)
    address: Optional[str] = Field(default=None, max_length=256)
    longitude: Optional[float] = None
    latitude: Optional[float] = None
    notice: Optional[str] = Field(default=None, max_length=512)
    contact_phone: Optional[str] = Field(default=None, max_length=32)
    wifi_ssid: Optional[str] = Field(default=None, max_length=128)
    wifi_password: Optional[str] = Field(default=None, max_length=128)
    images: Optional[list[str]] = None
    business_settings: Optional[dict[str, object]] = None
    cleaning_settings: Optional[dict[str, object]] = None
    status: Optional[str] = Field(default=None, max_length=32)
    sort_order: Optional[int] = None


class StoreResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    name: str
    address: Optional[str] = None
    longitude: Optional[float] = None
    latitude: Optional[float] = None
    notice: Optional[str] = None
    contact_phone: Optional[str] = None
    wifi_ssid: Optional[str] = None
    wifi_password: Optional[str] = None
    images: list[str] = Field(default_factory=list)
    business_settings: dict[str, object] = Field(default_factory=dict)
    cleaning_settings: dict[str, object] = Field(default_factory=dict)
    status: str
    sort_order: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
