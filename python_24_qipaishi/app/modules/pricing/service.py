from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal

from fastapi import status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError
from app.modules.pricing.schemas import PricingQuoteResponse
from app.modules.rooms.models import RoomPriceRule

MONEY = Decimal("0.01")
HOURS = Decimal("0.01")


def normalize_amount(value: Decimal) -> Decimal:
    return value.quantize(MONEY, rounding=ROUND_HALF_UP)


def calculate_hours(start_at: datetime, end_at: datetime) -> Decimal:
    if end_at <= start_at:
        raise AppError("INVALID_TIME_RANGE", "end_at must be later than start_at.")
    seconds = Decimal(str((end_at - start_at).total_seconds()))
    return (seconds / Decimal("3600")).quantize(HOURS, rounding=ROUND_HALF_UP)


def weekday_price(rule: RoomPriceRule, start_at: datetime) -> Decimal:
    weekday_key = str(start_at.weekday())
    value = rule.weekday_prices.get(weekday_key) if rule.weekday_prices else None
    if value is None:
        return Decimal(rule.base_price)
    return Decimal(str(value))


def build_quote(
    *,
    room_id: str,
    rule: RoomPriceRule,
    start_at: datetime,
    end_at: datetime,
) -> PricingQuoteResponse:
    duration_hours = calculate_hours(start_at, end_at)
    billable_hours = max(duration_hours, Decimal(rule.min_hours))
    unit_price = normalize_amount(weekday_price(rule, start_at))
    subtotal = normalize_amount(unit_price * billable_hours)
    return PricingQuoteResponse(
        room_id=room_id,
        price_rule_id=rule.id,
        start_at=start_at,
        end_at=end_at,
        duration_hours=duration_hours,
        billable_hours=billable_hours,
        unit_price=unit_price,
        subtotal_amount=subtotal,
        total_amount=subtotal,
        details=[
            {
                "type": "room_hours",
                "price_rule": rule.name,
                "duration_hours": str(duration_hours),
                "billable_hours": str(billable_hours),
                "unit_price": str(unit_price),
                "amount": str(subtotal),
            }
        ],
    )


async def quote_room(
    session: AsyncSession,
    *,
    tenant_id: str,
    room_id: str,
    start_at: datetime,
    end_at: datetime,
) -> PricingQuoteResponse:
    rule = await session.scalar(
        select(RoomPriceRule)
        .where(
            RoomPriceRule.tenant_id == tenant_id,
            RoomPriceRule.room_id == room_id,
            RoomPriceRule.status == "active",
        )
        .order_by(RoomPriceRule.created_at.desc())
    )
    if rule is None:
        raise AppError(
            "PRICE_RULE_NOT_FOUND",
            "Active room price rule was not found.",
            status.HTTP_404_NOT_FOUND,
        )
    return build_quote(room_id=room_id, rule=rule, start_at=start_at, end_at=end_at)
