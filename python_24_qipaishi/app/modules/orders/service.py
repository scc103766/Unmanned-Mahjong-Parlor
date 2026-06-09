from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Optional
from uuid import uuid4

from fastapi import status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError
from app.modules.availability.service import ensure_room_available, utc_now
from app.modules.orders.models import Order, OrderItem, RoomTimeLock
from app.modules.orders.schemas import (
    OrderChangeRoomQuoteResponse,
    OrderItemResponse,
    OrderRenewQuoteResponse,
    OrderRescheduleQuoteResponse,
    OrderResponse,
)
from app.modules.pricing.service import quote_room
from app.modules.rooms.models import Room

PENDING_PAYMENT_TTL_MINUTES = 15


def generate_order_no() -> str:
    return f"QPS{utc_now().strftime('%Y%m%d%H%M%S')}{uuid4().hex[:8].upper()}"


def normalize_datetime(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


async def load_order_items(session: AsyncSession, order_id: str) -> list[OrderItem]:
    result = await session.scalars(
        select(OrderItem).where(OrderItem.order_id == order_id).order_by(OrderItem.created_at)
    )
    return list(result.all())


async def build_order_response(session: AsyncSession, order: Order) -> OrderResponse:
    items = await load_order_items(session, order.id)
    return OrderResponse.model_validate(order).model_copy(
        update={"items": [OrderItemResponse.model_validate(item) for item in items]}
    )


def ensure_renewable(order: Order) -> None:
    if order.status not in {"paid", "in_use"}:
        raise AppError(
            "ORDER_STATE_INVALID",
            "Only paid or in-use orders can be renewed.",
            status.HTTP_409_CONFLICT,
        )


def ensure_changeable(order: Order) -> None:
    if order.status not in {"pending_payment", "paid", "in_use"}:
        raise AppError(
            "ORDER_STATE_INVALID",
            "Only pending, paid, or in-use orders can change room.",
            status.HTTP_409_CONFLICT,
        )


def ensure_reschedulable(order: Order) -> None:
    if order.status not in {"pending_payment", "paid"}:
        raise AppError(
            "ORDER_STATE_INVALID",
            "Only pending payment or paid orders can be rescheduled.",
            status.HTTP_409_CONFLICT,
        )


async def load_order_for_principal(
    session: AsyncSession,
    *,
    order_id: str,
    tenant_id: str,
    user_id: str,
    can_manage_tenant: bool,
) -> Order:
    order = await session.get(Order, order_id)
    if order is None:
        raise AppError("ORDER_NOT_FOUND", "Order was not found.", status.HTTP_404_NOT_FOUND)
    if order.tenant_id != tenant_id:
        raise AppError(
            "FORBIDDEN",
            "Cannot access another tenant order.",
            status.HTTP_403_FORBIDDEN,
        )
    if not can_manage_tenant and order.user_id != user_id:
        raise AppError(
            "FORBIDDEN",
            "Cannot access another user's order.",
            status.HTTP_403_FORBIDDEN,
        )
    return order


async def create_preorder(
    session: AsyncSession,
    *,
    tenant_id: str,
    user_id: str,
    room_id: str,
    start_at: datetime,
    end_at: datetime,
) -> Order:
    now = utc_now()
    room = await session.get(Room, room_id)
    if room is None or room.tenant_id != tenant_id:
        raise AppError("ROOM_NOT_FOUND", "Room was not found.", status.HTTP_404_NOT_FOUND)
    if room.status != "active":
        raise AppError("ROOM_NOT_AVAILABLE", "Room is not active.", status.HTTP_409_CONFLICT)

    await ensure_room_available(
        session,
        tenant_id=tenant_id,
        room_id=room.id,
        start_at=start_at,
        end_at=end_at,
        now=now,
    )
    quote = await quote_room(
        session,
        tenant_id=tenant_id,
        room_id=room.id,
        start_at=start_at,
        end_at=end_at,
    )
    expires_at = now + timedelta(minutes=PENDING_PAYMENT_TTL_MINUTES)
    order = Order(
        tenant_id=tenant_id,
        store_id=room.store_id,
        room_id=room.id,
        user_id=user_id,
        order_no=generate_order_no(),
        start_at=start_at,
        end_at=end_at,
        status="pending_payment",
        total_amount=quote.total_amount,
        payable_amount=quote.total_amount,
        pricing_snapshot=quote.model_dump(mode="json"),
        expires_at=expires_at,
    )
    session.add(order)
    await session.flush()
    session.add(
        OrderItem(
            tenant_id=tenant_id,
            order_id=order.id,
            item_type="room_hours",
            description="房间预约",
            quantity=quote.billable_hours,
            unit_price=quote.unit_price,
            amount=quote.total_amount,
        )
    )
    session.add(
        RoomTimeLock(
            tenant_id=tenant_id,
            room_id=room.id,
            order_id=order.id,
            start_at=start_at,
            end_at=end_at,
            status="pending_payment",
            expires_at=expires_at,
        )
    )
    await session.flush()
    return order


async def quote_order_renewal(
    session: AsyncSession,
    *,
    order: Order,
    new_end_at: datetime,
) -> OrderRenewQuoteResponse:
    ensure_renewable(order)
    current_end_at = normalize_datetime(order.end_at)
    new_end_at = normalize_datetime(new_end_at)
    if new_end_at <= current_end_at:
        raise AppError(
            "INVALID_RENEWAL_TIME",
            "Renewal end time must be later than current order end time.",
            status.HTTP_400_BAD_REQUEST,
        )
    now = utc_now()
    await ensure_room_available(
        session,
        tenant_id=order.tenant_id,
        room_id=order.room_id,
        start_at=current_end_at,
        end_at=new_end_at,
        now=now,
    )
    quote = await quote_room(
        session,
        tenant_id=order.tenant_id,
        room_id=order.room_id,
        start_at=current_end_at,
        end_at=new_end_at,
    )
    return OrderRenewQuoteResponse(
        order_id=order.id,
        room_id=order.room_id,
        current_end_at=current_end_at,
        new_end_at=new_end_at,
        additional_hours=quote.billable_hours,
        additional_amount=quote.total_amount,
        pricing_quote=quote.model_dump(mode="json"),
    )


async def renew_order(
    session: AsyncSession,
    *,
    order: Order,
    new_end_at: datetime,
) -> OrderRenewQuoteResponse:
    renewal_quote = await quote_order_renewal(session, order=order, new_end_at=new_end_at)
    current_end_at = normalize_datetime(order.end_at)
    new_end_at = normalize_datetime(new_end_at)
    order.end_at = new_end_at
    order.total_amount = Decimal(order.total_amount) + renewal_quote.additional_amount
    order.payable_amount = Decimal(order.payable_amount) + renewal_quote.additional_amount
    order.pricing_snapshot = {
        **order.pricing_snapshot,
        "latest_renewal": renewal_quote.model_dump(mode="json"),
    }
    session.add(
        OrderItem(
            tenant_id=order.tenant_id,
            order_id=order.id,
            item_type="renewal_hours",
            description="订单续费",
            quantity=renewal_quote.additional_hours,
            unit_price=renewal_quote.additional_amount / renewal_quote.additional_hours,
            amount=renewal_quote.additional_amount,
        )
    )
    session.add(
        RoomTimeLock(
            tenant_id=order.tenant_id,
            room_id=order.room_id,
            order_id=order.id,
            start_at=current_end_at,
            end_at=new_end_at,
            status="occupied",
            expires_at=None,
        )
    )
    await session.flush()
    return renewal_quote


async def quote_order_room_change(
    session: AsyncSession,
    *,
    order: Order,
    new_room_id: str,
) -> OrderChangeRoomQuoteResponse:
    ensure_changeable(order)
    if new_room_id == order.room_id:
        raise AppError(
            "ROOM_CHANGE_INVALID",
            "New room must be different from current room.",
            status.HTTP_400_BAD_REQUEST,
        )
    new_room = await session.get(Room, new_room_id)
    if new_room is None or new_room.tenant_id != order.tenant_id:
        raise AppError("ROOM_NOT_FOUND", "Room was not found.", status.HTTP_404_NOT_FOUND)
    if new_room.store_id != order.store_id:
        raise AppError(
            "ROOM_CHANGE_STORE_MISMATCH",
            "Room change must stay in the same store.",
            status.HTTP_400_BAD_REQUEST,
        )
    if new_room.status != "active":
        raise AppError("ROOM_NOT_AVAILABLE", "Room is not active.", status.HTTP_409_CONFLICT)

    now = utc_now()
    await ensure_room_available(
        session,
        tenant_id=order.tenant_id,
        room_id=new_room.id,
        start_at=normalize_datetime(order.start_at),
        end_at=normalize_datetime(order.end_at),
        now=now,
    )
    quote = await quote_room(
        session,
        tenant_id=order.tenant_id,
        room_id=new_room.id,
        start_at=normalize_datetime(order.start_at),
        end_at=normalize_datetime(order.end_at),
    )
    original_amount = Decimal(order.total_amount)
    return OrderChangeRoomQuoteResponse(
        order_id=order.id,
        current_room_id=order.room_id,
        new_room_id=new_room.id,
        start_at=normalize_datetime(order.start_at),
        end_at=normalize_datetime(order.end_at),
        original_amount=original_amount,
        new_amount=quote.total_amount,
        delta_amount=quote.total_amount - original_amount,
        pricing_quote=quote.model_dump(mode="json"),
    )


async def change_order_room(
    session: AsyncSession,
    *,
    order: Order,
    new_room_id: str,
) -> OrderChangeRoomQuoteResponse:
    change_quote = await quote_order_room_change(session, order=order, new_room_id=new_room_id)
    old_room_id = order.room_id
    new_status = "pending_payment" if order.status == "pending_payment" else "occupied"
    new_expires_at = order.expires_at if order.status == "pending_payment" else None

    await release_order_locks(session, order.id, status_value="released")
    order.room_id = new_room_id
    order.total_amount = change_quote.new_amount
    order.payable_amount = change_quote.new_amount
    order.pricing_snapshot = {
        **order.pricing_snapshot,
        "latest_room_change": change_quote.model_dump(mode="json"),
    }
    delta = change_quote.delta_amount
    if delta != Decimal("0.00"):
        session.add(
            OrderItem(
                tenant_id=order.tenant_id,
                order_id=order.id,
                item_type="room_change_adjustment",
                description=f"换房调整 {old_room_id} -> {new_room_id}",
                quantity=Decimal("1"),
                unit_price=delta,
                amount=delta,
            )
        )
    session.add(
        RoomTimeLock(
            tenant_id=order.tenant_id,
            room_id=new_room_id,
            order_id=order.id,
            start_at=normalize_datetime(order.start_at),
            end_at=normalize_datetime(order.end_at),
            status=new_status,
            expires_at=new_expires_at,
        )
    )
    await session.flush()
    return change_quote


async def quote_order_reschedule(
    session: AsyncSession,
    *,
    order: Order,
    new_start_at: datetime,
    new_end_at: datetime,
) -> OrderRescheduleQuoteResponse:
    ensure_reschedulable(order)
    new_start_at = normalize_datetime(new_start_at)
    new_end_at = normalize_datetime(new_end_at)
    now = utc_now()
    await ensure_room_available(
        session,
        tenant_id=order.tenant_id,
        room_id=order.room_id,
        start_at=new_start_at,
        end_at=new_end_at,
        now=now,
        exclude_order_id=order.id,
    )
    quote = await quote_room(
        session,
        tenant_id=order.tenant_id,
        room_id=order.room_id,
        start_at=new_start_at,
        end_at=new_end_at,
    )
    original_amount = Decimal(order.total_amount)
    return OrderRescheduleQuoteResponse(
        order_id=order.id,
        room_id=order.room_id,
        original_start_at=normalize_datetime(order.start_at),
        original_end_at=normalize_datetime(order.end_at),
        new_start_at=new_start_at,
        new_end_at=new_end_at,
        original_amount=original_amount,
        new_amount=quote.total_amount,
        delta_amount=quote.total_amount - original_amount,
        pricing_quote=quote.model_dump(mode="json"),
    )


async def reschedule_order(
    session: AsyncSession,
    *,
    order: Order,
    new_start_at: datetime,
    new_end_at: datetime,
) -> OrderRescheduleQuoteResponse:
    reschedule_quote = await quote_order_reschedule(
        session,
        order=order,
        new_start_at=new_start_at,
        new_end_at=new_end_at,
    )
    new_lock_status = "pending_payment" if order.status == "pending_payment" else "occupied"
    new_expires_at = order.expires_at if order.status == "pending_payment" else None
    order.start_at = reschedule_quote.new_start_at
    order.end_at = reschedule_quote.new_end_at
    order.total_amount = reschedule_quote.new_amount
    order.payable_amount = reschedule_quote.new_amount
    order.pricing_snapshot = {
        **order.pricing_snapshot,
        "latest_reschedule": reschedule_quote.model_dump(mode="json"),
    }
    delta = reschedule_quote.delta_amount
    if delta != Decimal("0.00"):
        session.add(
            OrderItem(
                tenant_id=order.tenant_id,
                order_id=order.id,
                item_type="reschedule_adjustment",
                description="订单改时调整",
                quantity=Decimal("1"),
                unit_price=delta,
                amount=delta,
            )
        )
    await release_order_locks(session, order.id, status_value="released")
    session.add(
        RoomTimeLock(
            tenant_id=order.tenant_id,
            room_id=order.room_id,
            order_id=order.id,
            start_at=reschedule_quote.new_start_at,
            end_at=reschedule_quote.new_end_at,
            status=new_lock_status,
            expires_at=new_expires_at,
        )
    )
    await session.flush()
    return reschedule_quote


async def transition_order_to_paid(session: AsyncSession, order: Order) -> None:
    now = utc_now()
    if order.status != "pending_payment":
        raise AppError(
            "ORDER_STATE_INVALID",
            "Only pending payment orders can be confirmed as paid.",
            status.HTTP_409_CONFLICT,
        )
    if order.expires_at is not None and normalize_datetime(order.expires_at) <= now:
        await release_order_locks(session, order.id, status_value="expired")
        order.status = "cancelled"
        order.cancelled_at = now
        order.cancel_reason = "pending payment expired"
        raise AppError(
            "ORDER_EXPIRED",
            "Pending payment order has expired.",
            status.HTTP_409_CONFLICT,
        )
    order.status = "paid"
    order.paid_at = now
    order.expires_at = None
    locks = (
        await session.scalars(
            select(RoomTimeLock).where(
                RoomTimeLock.order_id == order.id,
                RoomTimeLock.status == "pending_payment",
            )
        )
    ).all()
    for lock in locks:
        lock.status = "occupied"
        lock.expires_at = None
    await session.flush()


async def transition_order_to_in_use(session: AsyncSession, order: Order) -> None:
    if order.status != "paid":
        raise AppError(
            "ORDER_STATE_INVALID",
            "Only paid orders can be started.",
            status.HTTP_409_CONFLICT,
        )
    order.status = "in_use"
    order.started_at = utc_now()
    await session.flush()


async def release_order_locks(session: AsyncSession, order_id: str, *, status_value: str) -> None:
    locks = (
        await session.scalars(
            select(RoomTimeLock).where(
                RoomTimeLock.order_id == order_id,
                RoomTimeLock.status.in_(["pending_payment", "occupied"]),
            )
        )
    ).all()
    for lock in locks:
        lock.status = status_value
        lock.expires_at = None
    await session.flush()


async def cancel_order(session: AsyncSession, order: Order, *, reason: Optional[str]) -> None:
    if order.status not in {"pending_payment", "paid", "in_use"}:
        raise AppError(
            "ORDER_STATE_INVALID",
            "Only pending payment, paid, or in-use orders can be cancelled.",
            status.HTTP_409_CONFLICT,
        )
    order.status = "cancelled"
    order.cancelled_at = utc_now()
    order.cancel_reason = reason
    await release_order_locks(session, order.id, status_value="released")
    await session.flush()


async def complete_order(session: AsyncSession, order: Order) -> None:
    if order.status not in {"paid", "in_use"}:
        raise AppError(
            "ORDER_STATE_INVALID",
            "Only paid or in-use orders can be completed.",
            status.HTTP_409_CONFLICT,
        )
    order.status = "completed"
    order.completed_at = utc_now()
    await release_order_locks(session, order.id, status_value="released")
    await session.flush()


async def expire_pending_orders(
    session: AsyncSession,
    *,
    tenant_id: Optional[str] = None,
    now: Optional[datetime] = None,
) -> list[Order]:
    now = now or utc_now()
    query = select(Order).where(
        Order.status == "pending_payment",
        Order.expires_at.is_not(None),
        Order.expires_at <= now,
    )
    if tenant_id is not None:
        query = query.where(Order.tenant_id == tenant_id)
    orders = list((await session.scalars(query)).all())
    for order in orders:
        order.status = "cancelled"
        order.cancelled_at = now
        order.cancel_reason = "pending payment expired"
        await release_order_locks(session, order.id, status_value="expired")
    await session.flush()
    return orders
