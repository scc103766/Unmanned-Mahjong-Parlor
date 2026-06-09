from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field


class MerchantDashboardResponse(BaseModel):
    tenant_id: str
    store_id: Optional[str] = None
    start_at: datetime
    end_at: datetime
    order_count: int
    paid_order_count: int
    in_use_order_count: int
    completed_order_count: int
    cancelled_order_count: int
    gross_revenue: Decimal
    refund_amount: Decimal
    net_revenue: Decimal
    wallet_recharge_amount: Decimal
    member_count: int
    room_count: int
    active_room_count: int
    dirty_room_count: int
    usage_hours: Decimal
    room_utilization_rate: Decimal
    cleaning_pending_count: int
    cleaning_overdue_count: int
    cleaning_completed_count: int
    cleaning_complained_count: int
    device_failure_count: int


class RoomUsageResponse(BaseModel):
    room_id: str
    room_name: str
    order_count: int
    usage_hours: Decimal
    utilization_rate: Decimal


class RoomUsageListResponse(BaseModel):
    tenant_id: str
    store_id: Optional[str] = None
    start_at: datetime
    end_at: datetime
    rooms: list[RoomUsageResponse] = Field(default_factory=list)


class CleaningAnalyticsResponse(BaseModel):
    tenant_id: str
    store_id: Optional[str] = None
    start_at: datetime
    end_at: datetime
    pending_count: int
    accepted_count: int
    in_progress_count: int
    pending_review_count: int
    completed_count: int
    rejected_count: int
    canceled_count: int
    complained_count: int
    settled_count: int
    overdue_count: int
    settlement_amount: Decimal
