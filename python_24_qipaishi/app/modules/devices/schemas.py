from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class DeviceCreateRequest(BaseModel):
    store_id: str = Field(min_length=1, max_length=36)
    room_id: Optional[str] = Field(default=None, max_length=36)
    name: str = Field(min_length=1, max_length=120)
    device_type: str = Field(min_length=1, max_length=32)
    provider: str = Field(default="mock", min_length=1, max_length=32)
    external_id: str = Field(min_length=1, max_length=128)
    status: str = Field(default="active", max_length=32)
    capabilities: dict[str, object] = Field(default_factory=dict)


class DeviceOrderCommandRequest(BaseModel):
    idempotency_key: Optional[str] = Field(default=None, max_length=128)


class DeviceAdminCommandRequest(BaseModel):
    idempotency_key: Optional[str] = Field(default=None, max_length=128)


class DeviceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    store_id: str
    room_id: Optional[str] = None
    name: str
    device_type: str
    provider: str
    external_id: str
    status: str
    capabilities: dict[str, object] = Field(default_factory=dict)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class DeviceCommandResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    device_id: str
    actor_id: Optional[str] = None
    command: str
    biz_type: str
    biz_id: str
    status: str
    idempotency_key: Optional[str] = None
    request_payload: dict[str, object] = Field(default_factory=dict)
    response_payload: dict[str, object] = Field(default_factory=dict)
    failure_reason: Optional[str] = None
    retry_count: int
    executed_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
