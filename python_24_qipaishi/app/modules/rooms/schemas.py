from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class RoomCreateRequest(BaseModel):
    store_id: str = Field(min_length=1, max_length=36)
    name: str = Field(min_length=1, max_length=120)
    room_type: Optional[str] = Field(default=None, max_length=64)
    capacity: int = Field(default=4, ge=1)
    tags: list[str] = Field(default_factory=list)
    images: list[str] = Field(default_factory=list)
    status: str = Field(default="active", max_length=32)
    cleaning_status: str = Field(default="clean", max_length=32)
    sort_order: int = 0


class RoomUpdateRequest(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=120)
    room_type: Optional[str] = Field(default=None, max_length=64)
    capacity: Optional[int] = Field(default=None, ge=1)
    tags: Optional[list[str]] = None
    images: Optional[list[str]] = None
    status: Optional[str] = Field(default=None, max_length=32)
    cleaning_status: Optional[str] = Field(default=None, max_length=32)
    sort_order: Optional[int] = None


class RoomResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    store_id: str
    name: str
    room_type: Optional[str] = None
    capacity: int
    tags: list[str] = Field(default_factory=list)
    images: list[str] = Field(default_factory=list)
    status: str
    cleaning_status: str
    sort_order: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class RoomPriceRuleCreateRequest(BaseModel):
    name: str = Field(default="default", min_length=1, max_length=120)
    base_price: Decimal = Field(gt=Decimal("0"))
    weekday_prices: dict[str, object] = Field(default_factory=dict)
    night_price: Optional[Decimal] = Field(default=None, gt=Decimal("0"))
    min_hours: int = Field(default=1, ge=1)
    advance_booking_days: int = Field(default=14, ge=0)
    status: str = Field(default="active", max_length=32)


class RoomPriceRuleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    room_id: str
    name: str
    base_price: Decimal
    weekday_prices: dict[str, object] = Field(default_factory=dict)
    night_price: Optional[Decimal] = None
    min_hours: int
    advance_booking_days: int
    status: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class RoomBlockedSlotCreateRequest(BaseModel):
    start_at: datetime
    end_at: datetime
    reason: Optional[str] = Field(default=None, max_length=256)
    status: str = Field(default="active", max_length=32)

    @field_validator("end_at")
    @classmethod
    def validate_time_range(cls, end_at: datetime, info) -> datetime:  # type: ignore[no-untyped-def]
        start_at = info.data.get("start_at")
        if start_at is not None and end_at <= start_at:
            raise ValueError("end_at must be later than start_at")
        return end_at


class RoomBlockedSlotResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    room_id: str
    start_at: datetime
    end_at: datetime
    reason: Optional[str] = None
    status: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class RoomDetailResponse(RoomResponse):
    price_rules: list[RoomPriceRuleResponse] = Field(default_factory=list)
    blocked_slots: list[RoomBlockedSlotResponse] = Field(default_factory=list)
