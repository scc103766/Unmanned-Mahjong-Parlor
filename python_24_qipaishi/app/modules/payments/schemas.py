from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class WechatPrepayRequest(BaseModel):
    order_id: str = Field(min_length=1, max_length=36)
    idempotency_key: Optional[str] = Field(default=None, max_length=128)
    coupon_id: Optional[str] = Field(default=None, max_length=36)
    group_buy_code_id: Optional[str] = Field(default=None, max_length=36)
    wallet_amount: Decimal = Field(default=Decimal("0.00"), ge=Decimal("0"))


class MockWechatCallbackRequest(BaseModel):
    payment_id: str = Field(min_length=1, max_length=36)
    transaction_id: str = Field(min_length=1, max_length=128)
    provider_event_id: str = Field(min_length=1, max_length=128)
    timestamp: Optional[int] = Field(default=None, ge=0)
    nonce: Optional[str] = Field(default=None, max_length=64)
    signature: Optional[str] = Field(default=None, max_length=128)


class MockRefundCallbackRequest(BaseModel):
    refund_id: str = Field(min_length=1, max_length=36)
    provider_refund_id: str = Field(min_length=1, max_length=128)
    provider_event_id: str = Field(min_length=1, max_length=128)
    timestamp: Optional[int] = Field(default=None, ge=0)
    nonce: Optional[str] = Field(default=None, max_length=64)
    signature: Optional[str] = Field(default=None, max_length=128)


class RefundCreateRequest(BaseModel):
    amount: Decimal = Field(ge=Decimal("0"))
    idempotency_key: Optional[str] = Field(default=None, max_length=128)
    reason: Optional[str] = Field(default=None, max_length=256)


class PaymentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    order_id: str
    channel: str
    amount: Decimal
    status: str
    transaction_id: Optional[str] = None
    idempotency_key: Optional[str] = None
    provider_payload: dict[str, object] = Field(default_factory=dict)
    paid_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class PaymentEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    payment_id: Optional[str] = None
    channel: str
    event_type: str
    provider_event_id: str
    status: str
    payload: dict[str, object] = Field(default_factory=dict)
    processed_at: datetime


class RefundResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    payment_id: str
    order_id: str
    refund_no: str
    amount: Decimal
    reason: Optional[str] = None
    status: str
    provider_refund_id: Optional[str] = None
    idempotency_key: Optional[str] = None
    provider_payload: dict[str, object] = Field(default_factory=dict)
    refunded_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
