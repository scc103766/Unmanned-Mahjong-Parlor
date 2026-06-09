from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class CleaningTaskCompleteRequest(BaseModel):
    image_urls: list[str] = Field(default_factory=list, max_length=8)
    remark: Optional[str] = Field(default=None, max_length=256)


class CleaningTaskReviewRequest(BaseModel):
    approved: bool = True
    note: Optional[str] = Field(default=None, max_length=256)


class CleaningTaskComplainRequest(BaseModel):
    reason: str = Field(min_length=1, max_length=256)


class CleaningTaskCancelRequest(BaseModel):
    reason: Optional[str] = Field(default=None, max_length=256)


class CleaningTaskReassignRequest(BaseModel):
    note: Optional[str] = Field(default=None, max_length=256)


class CleaningTaskSettleRequest(BaseModel):
    amount: Decimal = Field(default=Decimal("0.00"), ge=Decimal("0"))
    note: Optional[str] = Field(default=None, max_length=256)


class CleaningSummaryResponse(BaseModel):
    pending_count: int
    overdue_count: int
    in_progress_count: int
    complained_count: int
    overdue_task_ids: list[str] = Field(default_factory=list)


class CleaningTaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    store_id: str
    room_id: str
    order_id: str
    cleaner_id: Optional[str] = None
    status: str
    scheduled_start_at: Optional[datetime] = None
    scheduled_end_at: Optional[datetime] = None
    accepted_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    reviewed_at: Optional[datetime] = None
    settled_at: Optional[datetime] = None
    canceled_at: Optional[datetime] = None
    review_note: Optional[str] = None
    cancel_reason: Optional[str] = None
    complaint_reason: Optional[str] = None
    complained_at: Optional[datetime] = None
    settlement_amount: Decimal
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class CleaningProofResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    task_id: str
    uploaded_by: str
    image_urls: list[str] = Field(default_factory=list)
    remark: Optional[str] = None
    created_at: Optional[datetime] = None
