from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class GroupBuyCodeCreateRequest(BaseModel):
    store_id: str = Field(min_length=1, max_length=36)
    code: str = Field(min_length=1, max_length=64)
    amount: Decimal = Field(gt=Decimal("0"))
    valid_from: Optional[datetime] = None
    valid_to: Optional[datetime] = None


class GroupBuyVerifyRequest(BaseModel):
    store_id: str = Field(min_length=1, max_length=36)
    code: str = Field(min_length=1, max_length=64)


class GroupBuyOrderRequest(BaseModel):
    order_id: str = Field(min_length=1, max_length=36)


class GroupBuyCodeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    store_id: str
    code: str
    amount: Decimal
    status: str
    locked_order_id: Optional[str] = None
    verified_order_id: Optional[str] = None
    valid_from: Optional[datetime] = None
    valid_to: Optional[datetime] = None
