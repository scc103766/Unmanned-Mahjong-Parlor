from datetime import datetime, timezone
from typing import Optional

from fastapi import status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError
from app.modules.availability.schemas import RoomAvailabilityResponse
from app.modules.orders.models import RoomTimeLock
from app.modules.rooms.models import Room, RoomBlockedSlot
from app.modules.stores.models import Store

ACTIVE_LOCK_STATUSES = {"pending_payment", "occupied"}


def ranges_overlap(
    first_start: datetime,
    first_end: datetime,
    second_start: datetime,
    second_end: datetime,
) -> bool:
    return first_start < second_end and first_end > second_start


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def validate_future_range(start_at: datetime, end_at: datetime, now: datetime) -> None:
    if end_at <= start_at:
        raise AppError("INVALID_TIME_RANGE", "end_at must be later than start_at.")
    if start_at < now:
        raise AppError(
            "BOOKING_TIME_IN_PAST",
            "Booking start time cannot be in the past.",
            status.HTTP_400_BAD_REQUEST,
        )


async def room_conflict_reasons(
    session: AsyncSession,
    *,
    tenant_id: str,
    room_id: str,
    start_at: datetime,
    end_at: datetime,
    now: datetime,
    exclude_order_id: Optional[str] = None,
) -> list[str]:
    room = await session.get(Room, room_id)
    blocked_slot = await session.scalar(
        select(RoomBlockedSlot).where(
            RoomBlockedSlot.tenant_id == tenant_id,
            RoomBlockedSlot.room_id == room_id,
            RoomBlockedSlot.status == "active",
            RoomBlockedSlot.start_at < end_at,
            RoomBlockedSlot.end_at > start_at,
        )
    )
    reasons = []
    if room is not None and room.cleaning_status != "clean":
        store = await session.get(Store, room.store_id)
        cleaning_settings = store.cleaning_settings if store is not None else {}
        allow_unclean_booking = bool(
            cleaning_settings.get("allow_unclean_booking")
            or cleaning_settings.get("allow_dirty_booking")
        )
        if not allow_unclean_booking:
            reasons.append("room_needs_cleaning")

    if blocked_slot is not None:
        reasons.append("blocked_slot")

    lock_query = select(RoomTimeLock).where(
        RoomTimeLock.tenant_id == tenant_id,
        RoomTimeLock.room_id == room_id,
        RoomTimeLock.start_at < end_at,
        RoomTimeLock.end_at > start_at,
        or_(
            RoomTimeLock.status == "occupied",
            (RoomTimeLock.status == "pending_payment") & (RoomTimeLock.expires_at > now),
        ),
    )
    if exclude_order_id is not None:
        lock_query = lock_query.where(RoomTimeLock.order_id != exclude_order_id)
    lock = await session.scalar(lock_query)
    if lock is not None:
        reasons.append("time_lock")
    return reasons


async def ensure_room_available(
    session: AsyncSession,
    *,
    tenant_id: str,
    room_id: str,
    start_at: datetime,
    end_at: datetime,
    now: datetime,
    exclude_order_id: Optional[str] = None,
) -> None:
    validate_future_range(start_at, end_at, now)
    reasons = await room_conflict_reasons(
        session,
        tenant_id=tenant_id,
        room_id=room_id,
        start_at=start_at,
        end_at=end_at,
        now=now,
        exclude_order_id=exclude_order_id,
    )
    if reasons:
        raise AppError(
            "ROOM_TIME_CONFLICT",
            "Room is not available for the selected time range.",
            status.HTTP_409_CONFLICT,
            details={"room_id": room_id, "reasons": reasons},
        )


async def get_room_availability(
    session: AsyncSession,
    *,
    room: Room,
    start_at: datetime,
    end_at: datetime,
    now: datetime,
) -> RoomAvailabilityResponse:
    validate_future_range(start_at, end_at, now)
    reasons = await room_conflict_reasons(
        session,
        tenant_id=room.tenant_id,
        room_id=room.id,
        start_at=start_at,
        end_at=end_at,
        now=now,
    )
    return RoomAvailabilityResponse(
        room_id=room.id,
        store_id=room.store_id,
        start_at=start_at,
        end_at=end_at,
        available=not reasons and room.status == "active",
        conflict_reasons=reasons if room.status == "active" else reasons + ["room_inactive"],
    )
