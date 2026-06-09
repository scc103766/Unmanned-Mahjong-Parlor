from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class TimeRangeRequest(BaseModel):
    start_at: datetime
    end_at: datetime

    @field_validator("end_at")
    @classmethod
    def validate_time_range(cls, end_at: datetime, info) -> datetime:  # type: ignore[no-untyped-def]
        start_at = info.data.get("start_at")
        if start_at is not None and end_at <= start_at:
            raise ValueError("end_at must be later than start_at")
        return end_at


class PreorderRequest(TimeRangeRequest):
    room_id: str = Field(min_length=1, max_length=36)


class OrderCreateRequest(PreorderRequest):
    pass


class OrderCancelRequest(BaseModel):
    reason: Optional[str] = Field(default=None, max_length=256)


class OrderRenewQuoteRequest(BaseModel):
    new_end_at: datetime


class OrderRenewRequest(OrderRenewQuoteRequest):
    pass


class OrderChangeRoomQuoteRequest(BaseModel):
    new_room_id: str = Field(min_length=1, max_length=36)


class OrderChangeRoomRequest(OrderChangeRoomQuoteRequest):
    pass


class OrderRescheduleQuoteRequest(TimeRangeRequest):
    pass


class OrderRescheduleRequest(OrderRescheduleQuoteRequest):
    pass


class OrderExpirePendingResponse(BaseModel):
    expired_order_ids: list[str] = Field(default_factory=list)


class OrderItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    order_id: str
    item_type: str
    description: Optional[str] = None
    quantity: Decimal
    unit_price: Decimal
    amount: Decimal


class OrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    store_id: str
    room_id: str
    user_id: str
    order_no: str
    start_at: datetime
    end_at: datetime
    status: str
    total_amount: Decimal
    payable_amount: Decimal
    pricing_snapshot: dict[str, object] = Field(default_factory=dict)
    expires_at: Optional[datetime] = None
    paid_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    cancel_reason: Optional[str] = None
    items: list[OrderItemResponse] = Field(default_factory=list)


class RoomTimeLockResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    room_id: str
    order_id: str
    start_at: datetime
    end_at: datetime
    status: str
    expires_at: Optional[datetime] = None


class OrderRenewQuoteResponse(BaseModel):
    order_id: str
    room_id: str
    current_end_at: datetime
    new_end_at: datetime
    additional_hours: Decimal
    additional_amount: Decimal
    pricing_quote: dict[str, object]


class OrderChangeRoomQuoteResponse(BaseModel):
    order_id: str
    current_room_id: str
    new_room_id: str
    start_at: datetime
    end_at: datetime
    original_amount: Decimal
    new_amount: Decimal
    delta_amount: Decimal
    pricing_quote: dict[str, object]


class OrderRescheduleQuoteResponse(BaseModel):
    order_id: str
    room_id: str
    original_start_at: datetime
    original_end_at: datetime
    new_start_at: datetime
    new_end_at: datetime
    original_amount: Decimal
    new_amount: Decimal
    delta_amount: Decimal
    pricing_quote: dict[str, object]
