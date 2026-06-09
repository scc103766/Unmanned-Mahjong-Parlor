from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: Optional[str] = None
    phone: Optional[str] = None
    openid: Optional[str] = None
    unionid: Optional[str] = None
    nickname: Optional[str] = None
    avatar_url: Optional[str] = None
    status: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    roles: list[str] = Field(default_factory=list)
    store_ids: list[str] = Field(default_factory=list)


class RoleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    code: str
    name: str
    scope: str


class RoleAssignmentRequest(BaseModel):
    role_codes: list[str] = Field(default_factory=list)


class StoreScopeAssignmentRequest(BaseModel):
    store_ids: list[str] = Field(default_factory=list)
