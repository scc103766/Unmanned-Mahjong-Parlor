from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.core.errors import AppError
from app.main import create_app
from app.modules.availability.service import ranges_overlap
from app.modules.orders.models import Order
from app.modules.orders.schemas import PreorderRequest
from app.modules.orders.service import ensure_changeable, ensure_renewable, normalize_datetime
from app.modules.pricing.service import build_quote, calculate_hours
from app.modules.rooms.models import RoomPriceRule


def test_m3_routes_are_registered() -> None:
    route_paths = {route.path for route in create_app().routes}

    assert "/api/v1/availability/rooms" in route_paths
    assert "/api/v1/pricing/quote" in route_paths
    assert "/api/v1/orders" in route_paths
    assert "/api/v1/orders/preorder" in route_paths
    assert "/api/v1/orders/expire-pending" in route_paths
    assert "/api/v1/orders/{order_id}" in route_paths
    assert "/api/v1/orders/{order_id}/renew/quote" in route_paths
    assert "/api/v1/orders/{order_id}/renew" in route_paths
    assert "/api/v1/orders/{order_id}/change-room/quote" in route_paths
    assert "/api/v1/orders/{order_id}/change-room" in route_paths
    assert "/api/v1/orders/{order_id}/cancel" in route_paths
    assert "/api/v1/orders/{order_id}/mock-pay" in route_paths
    assert "/api/v1/orders/{order_id}/start" in route_paths
    assert "/api/v1/orders/{order_id}/complete" in route_paths


def test_time_range_overlap_helper() -> None:
    base = datetime(2026, 5, 14, 10, 0, tzinfo=timezone.utc)

    assert ranges_overlap(
        base,
        base + timedelta(hours=2),
        base + timedelta(hours=1),
        base + timedelta(hours=3),
    )
    assert not ranges_overlap(
        base,
        base + timedelta(hours=2),
        base + timedelta(hours=2),
        base + timedelta(hours=3),
    )


def test_preorder_request_requires_valid_time_range() -> None:
    start_at = datetime(2026, 5, 14, 10, 0, tzinfo=timezone.utc)

    with pytest.raises(ValidationError):
        PreorderRequest(room_id="room_1", start_at=start_at, end_at=start_at)


def test_pricing_quote_applies_min_hours_and_weekday_price() -> None:
    start_at = datetime(2026, 5, 14, 10, 0, tzinfo=timezone.utc)
    end_at = start_at + timedelta(hours=1)
    rule = RoomPriceRule(
        id="rule_1",
        tenant_id="tenant_1",
        room_id="room_1",
        name="weekday",
        base_price=Decimal("40.00"),
        weekday_prices={"3": "35.00"},
        min_hours=2,
        advance_booking_days=14,
        status="active",
    )

    quote = build_quote(room_id="room_1", rule=rule, start_at=start_at, end_at=end_at)

    assert quote.duration_hours == Decimal("1.00")
    assert quote.billable_hours == Decimal("2")
    assert quote.unit_price == Decimal("35.00")
    assert quote.total_amount == Decimal("70.00")


def test_calculate_hours_rejects_reversed_range() -> None:
    start_at = datetime(2026, 5, 14, 10, 0, tzinfo=timezone.utc)

    with pytest.raises(AppError):
        calculate_hours(start_at, start_at - timedelta(minutes=1))


def test_order_state_guards_for_renewal_and_change_room() -> None:
    paid_order = Order(
        tenant_id="tenant_1",
        store_id="store_1",
        room_id="room_1",
        user_id="user_1",
        order_no="order_1",
        start_at=datetime(2026, 5, 14, 10, 0, tzinfo=timezone.utc),
        end_at=datetime(2026, 5, 14, 12, 0, tzinfo=timezone.utc),
        status="paid",
        total_amount=Decimal("80.00"),
        payable_amount=Decimal("80.00"),
    )
    completed_order = Order(
        tenant_id="tenant_1",
        store_id="store_1",
        room_id="room_1",
        user_id="user_1",
        order_no="order_2",
        start_at=datetime(2026, 5, 14, 10, 0, tzinfo=timezone.utc),
        end_at=datetime(2026, 5, 14, 12, 0, tzinfo=timezone.utc),
        status="completed",
        total_amount=Decimal("80.00"),
        payable_amount=Decimal("80.00"),
    )

    ensure_renewable(paid_order)
    ensure_changeable(paid_order)
    with pytest.raises(AppError):
        ensure_renewable(completed_order)
    with pytest.raises(AppError):
        ensure_changeable(completed_order)


def test_normalize_datetime_treats_naive_as_utc() -> None:
    naive = datetime(2026, 5, 14, 10, 0)

    normalized = normalize_datetime(naive)

    assert normalized.tzinfo == timezone.utc
