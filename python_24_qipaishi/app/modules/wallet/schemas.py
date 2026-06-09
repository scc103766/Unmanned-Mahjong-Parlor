from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class WalletRechargeRequest(BaseModel):
    amount: Decimal = Field(gt=Decimal("0"))
    gift_amount: Decimal = Field(default=Decimal("0.00"), ge=Decimal("0"))
    remark: Optional[str] = Field(default=None, max_length=256)


class WalletAdjustmentRequest(BaseModel):
    user_id: str = Field(min_length=1, max_length=36)
    direction: str = Field(pattern="^(credit|debit)$")
    cash_amount: Decimal = Field(default=Decimal("0.00"), ge=Decimal("0"))
    gift_amount: Decimal = Field(default=Decimal("0.00"), ge=Decimal("0"))
    remark: Optional[str] = Field(default=None, max_length=256)


class WalletAccountResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    user_id: str
    cash_balance: Decimal
    gift_balance: Decimal
    status: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class WalletLedgerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    account_id: str
    user_id: str
    direction: str
    amount: Decimal
    cash_balance_after: Decimal
    gift_balance_after: Decimal
    biz_type: str
    biz_id: Optional[str] = None
    remark: Optional[str] = None
    created_at: Optional[datetime] = None
