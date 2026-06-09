from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class CouponTemplateCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    coupon_type: str = Field(default="amount", max_length=32)
    value: Decimal = Field(gt=Decimal("0"))
    threshold: Decimal = Field(default=Decimal("0.00"), ge=Decimal("0"))
    total_count: int = Field(default=0, ge=0)
    per_user_limit: int = Field(default=1, ge=1)
    valid_from: Optional[datetime] = None
    valid_to: Optional[datetime] = None
    status: str = Field(default="active", max_length=32)


class CouponClaimRequest(BaseModel):
    template_id: str = Field(min_length=1, max_length=36)


class CouponIssueRequest(BaseModel):
    template_id: str = Field(min_length=1, max_length=36)
    user_id: str = Field(min_length=1, max_length=36)
    enforce_user_limit: bool = True


class CouponOrderRequest(BaseModel):
    order_id: str = Field(min_length=1, max_length=36)


class CouponTemplateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    name: str
    coupon_type: str
    value: Decimal
    threshold: Decimal
    total_count: int
    claimed_count: int
    per_user_limit: int
    valid_from: Optional[datetime] = None
    valid_to: Optional[datetime] = None
    status: str


class CouponResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    template_id: str
    user_id: str
    status: str
    value: Decimal
    threshold: Decimal
    locked_order_id: Optional[str] = None
    used_order_id: Optional[str] = None
    valid_from: Optional[datetime] = None
    valid_to: Optional[datetime] = None
