from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class PricingQuoteRequest(BaseModel):
    room_id: str = Field(min_length=1, max_length=36)
    start_at: datetime
    end_at: datetime


class PricingQuoteResponse(BaseModel):
    room_id: str
    price_rule_id: str
    currency: str = "CNY"
    start_at: datetime
    end_at: datetime
    duration_hours: Decimal
    billable_hours: Decimal
    unit_price: Decimal
    subtotal_amount: Decimal
    total_amount: Decimal
    details: list[dict[str, object]] = Field(default_factory=list)
