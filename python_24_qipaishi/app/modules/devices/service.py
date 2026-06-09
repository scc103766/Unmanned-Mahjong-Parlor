from datetime import datetime, timedelta
from typing import Optional

from fastapi import status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError
from app.modules.availability.service import utc_now
from app.modules.devices.adapters import MockDeviceAdapter
from app.modules.devices.models import Device, DeviceCommand
from app.modules.orders.models import Order
from app.modules.orders.service import normalize_datetime
from app.modules.rooms.models import Room
from app.modules.stores.models import Store

ORDER_DEVICE_ACCESS_BEFORE_MINUTES = 15
ORDER_DEVICE_ACCESS_AFTER_MINUTES = 30
DEVICE_COMMAND_DEDUP_SECONDS = 10


def ensure_order_device_authorized(order: Order, *, now: Optional[datetime] = None) -> None:
    now = now or utc_now()
    if order.status not in {"paid", "in_use"}:
        raise AppError(
            "ORDER_DEVICE_ACCESS_DENIED",
            "Only paid or in-use orders can operate devices.",
            status.HTTP_409_CONFLICT,
        )

    start_at = normalize_datetime(order.start_at) - timedelta(
        minutes=ORDER_DEVICE_ACCESS_BEFORE_MINUTES
    )
    end_at = normalize_datetime(order.end_at) + timedelta(
        minutes=ORDER_DEVICE_ACCESS_AFTER_MINUTES
    )
    if not (start_at <= normalize_datetime(now) <= end_at):
        raise AppError(
            "ORDER_DEVICE_ACCESS_WINDOW_CLOSED",
            "Order is outside the allowed device access window.",
            status.HTTP_409_CONFLICT,
        )


async def validate_device_scope(
    session: AsyncSession,
    *,
    tenant_id: str,
    store_id: str,
    room_id: Optional[str],
) -> None:
    store = await session.get(Store, store_id)
    if store is None or store.tenant_id != tenant_id:
        raise AppError("STORE_NOT_FOUND", "Store was not found.", status.HTTP_404_NOT_FOUND)
    if room_id is None:
        return
    room = await session.get(Room, room_id)
    if room is None or room.tenant_id != tenant_id:
        raise AppError("ROOM_NOT_FOUND", "Room was not found.", status.HTTP_404_NOT_FOUND)
    if room.store_id != store_id:
        raise AppError(
            "DEVICE_ROOM_STORE_MISMATCH",
            "Device room must belong to the selected store.",
            status.HTTP_400_BAD_REQUEST,
        )


async def find_active_device(
    session: AsyncSession,
    *,
    tenant_id: str,
    store_id: str,
    room_id: Optional[str],
    device_type: str,
) -> Device:
    query = select(Device).where(
        Device.tenant_id == tenant_id,
        Device.store_id == store_id,
        Device.device_type == device_type,
        Device.status == "active",
    )
    if room_id is None:
        query = query.where(Device.room_id.is_(None))
    else:
        query = query.where(Device.room_id == room_id)
    device = await session.scalar(query.order_by(Device.created_at.desc()))
    if device is None:
        raise AppError(
            "DEVICE_NOT_FOUND",
            "Active device was not found.",
            status.HTTP_404_NOT_FOUND,
        )
    return device


async def execute_device_command(
    session: AsyncSession,
    *,
    device: Device,
    actor_id: Optional[str],
    command: str,
    biz_type: str,
    biz_id: str,
    idempotency_key: Optional[str],
    request_payload: dict[str, object],
) -> DeviceCommand:
    now = utc_now()
    if idempotency_key:
        existing = await session.scalar(
            select(DeviceCommand).where(
                DeviceCommand.tenant_id == device.tenant_id,
                DeviceCommand.idempotency_key == idempotency_key,
            )
        )
        if existing is not None:
            return existing
    else:
        duplicate = await session.scalar(
            select(DeviceCommand)
            .where(
                DeviceCommand.tenant_id == device.tenant_id,
                DeviceCommand.device_id == device.id,
                DeviceCommand.actor_id == actor_id,
                DeviceCommand.command == command,
                DeviceCommand.biz_type == biz_type,
                DeviceCommand.biz_id == biz_id,
                DeviceCommand.status.in_(["pending", "succeeded"]),
                DeviceCommand.created_at >= now - timedelta(seconds=DEVICE_COMMAND_DEDUP_SECONDS),
            )
            .order_by(DeviceCommand.created_at.desc())
        )
        if duplicate is not None:
            return duplicate

    row = DeviceCommand(
        tenant_id=device.tenant_id,
        device_id=device.id,
        actor_id=actor_id,
        command=command,
        biz_type=biz_type,
        biz_id=biz_id,
        status="pending",
        idempotency_key=idempotency_key,
        request_payload=request_payload,
        response_payload={},
        retry_count=0,
    )
    session.add(row)
    await session.flush()
    return await dispatch_device_command(session, row=row, device=device)


async def dispatch_device_command(
    session: AsyncSession,
    *,
    row: DeviceCommand,
    device: Device,
) -> DeviceCommand:
    if device.provider != "mock":
        row.status = "failed"
        row.failure_reason = f"Unsupported device provider: {device.provider}"
        row.executed_at = utc_now()
        await session.flush()
        return row

    response = await MockDeviceAdapter().execute(
        device=device,
        command=row.command,
        payload=row.request_payload,
    )
    row.response_payload = response
    row.executed_at = utc_now()
    if response.get("ok") is True:
        row.status = "succeeded"
    else:
        row.status = "failed"
        row.failure_reason = str(response.get("error") or "device command failed")
    await session.flush()
    return row


async def retry_device_command(
    session: AsyncSession,
    *,
    command_id: str,
    tenant_id: str,
) -> DeviceCommand:
    row = await session.get(DeviceCommand, command_id)
    if row is None or row.tenant_id != tenant_id:
        raise AppError(
            "DEVICE_COMMAND_NOT_FOUND",
            "Device command was not found.",
            status.HTTP_404_NOT_FOUND,
        )
    if row.status != "failed":
        raise AppError(
            "DEVICE_COMMAND_STATE_INVALID",
            "Only failed device commands can be retried.",
            status.HTTP_409_CONFLICT,
        )
    device = await session.get(Device, row.device_id)
    if device is None or device.tenant_id != tenant_id:
        raise AppError("DEVICE_NOT_FOUND", "Device was not found.", status.HTTP_404_NOT_FOUND)
    row.status = "pending"
    row.retry_count += 1
    row.failure_reason = None
    row.response_payload = {}
    await session.flush()
    return await dispatch_device_command(session, row=row, device=device)


async def execute_order_device_command(
    session: AsyncSession,
    *,
    order: Order,
    actor_id: str,
    device_type: str,
    command: str,
    idempotency_key: Optional[str],
) -> DeviceCommand:
    ensure_order_device_authorized(order)
    room_id = None if device_type == "store_door" else order.room_id
    device = await find_active_device(
        session,
        tenant_id=order.tenant_id,
        store_id=order.store_id,
        room_id=room_id,
        device_type=device_type,
    )
    return await execute_device_command(
        session,
        device=device,
        actor_id=actor_id,
        command=command,
        biz_type="order",
        biz_id=order.id,
        idempotency_key=idempotency_key,
        request_payload={
            "order_id": order.id,
            "order_no": order.order_no,
            "store_id": order.store_id,
            "room_id": order.room_id,
            "device_type": device_type,
            "command": command,
        },
    )
