from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.main import create_app
from app.modules.rooms.schemas import (
    RoomBlockedSlotCreateRequest,
    RoomPriceRuleCreateRequest,
)


def test_m2_routes_are_registered() -> None:
    route_paths = {route.path for route in create_app().routes}

    assert "/api/v1/stores" in route_paths
    assert "/api/v1/stores/{store_id}" in route_paths
    assert "/api/v1/rooms" in route_paths
    assert "/api/v1/rooms/{room_id}/price-rules" in route_paths
    assert "/api/v1/rooms/{room_id}/blocked-slots" in route_paths


def test_room_price_rule_requires_positive_base_price() -> None:
    payload = RoomPriceRuleCreateRequest(base_price=Decimal("38.00"))

    assert payload.base_price == Decimal("38.00")
    assert payload.min_hours == 1


def test_room_blocked_slot_requires_end_after_start() -> None:
    start_at = datetime.now(timezone.utc)

    with pytest.raises(ValidationError):
        RoomBlockedSlotCreateRequest(start_at=start_at, end_at=start_at - timedelta(hours=1))
