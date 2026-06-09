from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field


class MemberSummaryResponse(BaseModel):
    user_id: str
    tenant_id: str
    phone: Optional[str] = None
    nickname: Optional[str] = None
    status: str
    cash_balance: Decimal
    gift_balance: Decimal
    order_count: int
    completed_order_count: int
    total_spend: Decimal
    coupon_count: int
    available_coupon_count: int
    created_at: Optional[datetime] = None


class MemberListResponse(BaseModel):
    members: list[MemberSummaryResponse] = Field(default_factory=list)


class MemberDetailResponse(MemberSummaryResponse):
    recent_order_ids: list[str] = Field(default_factory=list)
    recent_ledger_ids: list[str] = Field(default_factory=list)
