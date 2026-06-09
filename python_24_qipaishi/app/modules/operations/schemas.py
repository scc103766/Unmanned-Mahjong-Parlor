from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class OperationExceptionResponse(BaseModel):
    id: str
    tenant_id: Optional[str] = None
    store_id: Optional[str] = None
    source: str
    severity: str
    entity_type: str
    entity_id: str
    status: str
    message: str
    occurred_at: datetime
    payload: dict[str, object] = Field(default_factory=dict)


class OperationExceptionListResponse(BaseModel):
    exceptions: list[OperationExceptionResponse] = Field(default_factory=list)


class AuditLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: Optional[str] = None
    actor_id: Optional[str] = None
    action: str
    target_type: str
    target_id: Optional[str] = None
    request_id: Optional[str] = None
    ip_address: Optional[str] = None
    payload: dict[str, object] = Field(default_factory=dict)
    created_at: datetime


class AuditLogListResponse(BaseModel):
    logs: list[AuditLogResponse] = Field(default_factory=list)


class ManualCompensationRequest(BaseModel):
    tenant_id: Optional[str] = Field(default=None, max_length=36)
    user_id: str = Field(min_length=1, max_length=36)
    cash_amount: Decimal = Field(default=Decimal("0.00"), ge=Decimal("0"))
    gift_amount: Decimal = Field(default=Decimal("0.00"), ge=Decimal("0"))
    coupon_template_id: Optional[str] = Field(default=None, max_length=36)
    reason: str = Field(min_length=1, max_length=256)


class ManualCompensationResponse(BaseModel):
    user_id: str
    cash_amount: Decimal
    gift_amount: Decimal
    coupon_id: Optional[str] = None
    wallet_account_id: Optional[str] = None
