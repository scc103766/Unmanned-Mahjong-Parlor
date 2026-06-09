from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class WithdrawalCreateRequest(BaseModel):
    amount: Decimal = Field(gt=Decimal("0"))
    remark: Optional[str] = Field(default=None, max_length=256)
    payout_payload: dict[str, object] = Field(default_factory=dict)


class WithdrawalReviewRequest(BaseModel):
    note: Optional[str] = Field(default=None, max_length=256)


class WithdrawalRejectRequest(BaseModel):
    reason: str = Field(min_length=1, max_length=256)


class WithdrawalPaidRequest(BaseModel):
    payout_ref: str = Field(min_length=1, max_length=128)
    note: Optional[str] = Field(default=None, max_length=256)


class WithdrawalResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    user_id: str
    requested_by: str
    amount: Decimal
    status: str
    remark: Optional[str] = None
    review_note: Optional[str] = None
    reject_reason: Optional[str] = None
    payout_ref: Optional[str] = None
    payout_payload: dict[str, object] = Field(default_factory=dict)
    requested_at: datetime
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    paid_by: Optional[str] = None
    paid_at: Optional[datetime] = None
    rejected_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
