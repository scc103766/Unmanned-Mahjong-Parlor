from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from app.core.errors import AppError
from app.main import create_app
from app.modules.devices.adapters import MockDeviceAdapter
from app.modules.devices.models import Device
from app.modules.devices.schemas import (
    DeviceAdminCommandRequest,
    DeviceCreateRequest,
    DeviceOrderCommandRequest,
)
from app.modules.devices.service import ensure_order_device_authorized
from app.modules.orders.models import Order


def test_m5_device_routes_are_registered() -> None:
    route_paths = {route.path for route in create_app().routes}

    assert "/api/v1/devices" in route_paths
    assert "/api/v1/device-commands" in route_paths
    assert "/api/v1/device-commands/{command_id}/retry" in route_paths
    assert "/api/v1/devices/{device_id}/test" in route_paths
    assert "/api/v1/devices/{device_id}/open" in route_paths
    assert "/api/v1/devices/{device_id}/close" in route_paths
    assert "/api/v1/orders/{order_id}/open-store-door" in route_paths
    assert "/api/v1/orders/{order_id}/open-room-door" in route_paths
    assert "/api/v1/orders/{order_id}/open-room-lock" in route_paths
    assert "/api/v1/orders/{order_id}/power-on" in route_paths


def test_device_create_request_defaults_to_mock_provider() -> None:
    payload = DeviceCreateRequest(
        store_id="store_1",
        name="front door",
        device_type="store_door",
        external_id="mock_front_door",
    )

    assert payload.provider == "mock"
    assert payload.status == "active"
    assert payload.capabilities == {}


def test_device_order_command_request_accepts_idempotency_key() -> None:
    payload = DeviceOrderCommandRequest(idempotency_key="cmd_idem_1")

    assert payload.idempotency_key == "cmd_idem_1"


def test_device_admin_command_request_accepts_idempotency_key() -> None:
    payload = DeviceAdminCommandRequest(idempotency_key="admin_cmd_idem_1")

    assert payload.idempotency_key == "admin_cmd_idem_1"


def test_order_device_authorization_accepts_paid_order_inside_window() -> None:
    now = datetime(2026, 5, 15, 10, 0, tzinfo=timezone.utc)
    order = Order(
        tenant_id="tenant_1",
        store_id="store_1",
        room_id="room_1",
        user_id="user_1",
        order_no="order_1",
        start_at=now - timedelta(minutes=10),
        end_at=now + timedelta(hours=2),
        status="paid",
        total_amount=Decimal("80.00"),
        payable_amount=Decimal("80.00"),
    )

    ensure_order_device_authorized(order, now=now)


def test_order_device_authorization_rejects_cancelled_order() -> None:
    now = datetime(2026, 5, 15, 10, 0, tzinfo=timezone.utc)
    order = Order(
        tenant_id="tenant_1",
        store_id="store_1",
        room_id="room_1",
        user_id="user_1",
        order_no="order_1",
        start_at=now - timedelta(minutes=10),
        end_at=now + timedelta(hours=2),
        status="cancelled",
        total_amount=Decimal("80.00"),
        payable_amount=Decimal("80.00"),
    )

    with pytest.raises(AppError) as exc_info:
        ensure_order_device_authorized(order, now=now)

    assert exc_info.value.code == "ORDER_DEVICE_ACCESS_DENIED"


def test_order_device_authorization_rejects_closed_window() -> None:
    now = datetime(2026, 5, 15, 10, 0, tzinfo=timezone.utc)
    order = Order(
        tenant_id="tenant_1",
        store_id="store_1",
        room_id="room_1",
        user_id="user_1",
        order_no="order_1",
        start_at=now + timedelta(hours=1),
        end_at=now + timedelta(hours=3),
        status="paid",
        total_amount=Decimal("80.00"),
        payable_amount=Decimal("80.00"),
    )

    with pytest.raises(AppError) as exc_info:
        ensure_order_device_authorized(order, now=now)

    assert exc_info.value.code == "ORDER_DEVICE_ACCESS_WINDOW_CLOSED"


async def test_mock_device_adapter_returns_success_payload() -> None:
    device = Device(
        tenant_id="tenant_1",
        store_id="store_1",
        room_id=None,
        name="front door",
        device_type="store_door",
        provider="mock",
        external_id="mock_front_door",
        status="active",
    )

    response = await MockDeviceAdapter().execute(
        device=device,
        command="open",
        payload={"order_id": "order_1"},
    )

    assert response["ok"] is True
    assert response["provider"] == "mock"
    assert response["command"] == "open"


async def test_mock_device_adapter_can_simulate_failure() -> None:
    device = Device(
        tenant_id="tenant_1",
        store_id="store_1",
        room_id=None,
        name="front door",
        device_type="store_door",
        provider="mock",
        external_id="mock_fail",
        status="active",
    )

    response = await MockDeviceAdapter().execute(
        device=device,
        command="open",
        payload={"order_id": "order_1"},
    )

    assert response["ok"] is False
    assert response["error"] == "mock device failure"
