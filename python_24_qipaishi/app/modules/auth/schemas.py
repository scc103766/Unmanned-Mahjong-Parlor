from typing import Optional

from pydantic import BaseModel, Field


class PrincipalResponse(BaseModel):
    user_id: str
    tenant_id: Optional[str] = None
    phone: Optional[str] = None
    nickname: Optional[str] = None
    roles: list[str] = Field(default_factory=list)
    store_ids: list[str] = Field(default_factory=list)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: PrincipalResponse


class WechatLoginRequest(BaseModel):
    client_type: str = Field(default="h5", min_length=1, max_length=32)
    app_id: str = Field(min_length=1, max_length=128)
    code: str = Field(min_length=1, max_length=256)
    phone: Optional[str] = Field(default=None, max_length=32)
    nickname: Optional[str] = Field(default=None, max_length=128)
    avatar_url: Optional[str] = Field(default=None, max_length=512)


class DevBootstrapRequest(BaseModel):
    tenant_name: str = Field(default="示例棋牌室", min_length=1, max_length=120)
    client_type: str = Field(default="h5", min_length=1, max_length=32)
    app_id: str = Field(default="dev-h5", min_length=1, max_length=128)
    phone: Optional[str] = Field(default="18800000000", max_length=32)
    nickname: Optional[str] = Field(default="开发管理员", max_length=128)
