from collections.abc import Sequence
from datetime import datetime, timedelta, timezone
from decimal import ROUND_HALF_UP, Decimal
from typing import Optional

from sqlalchemy import false, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.analytics.schemas import (
    CleaningAnalyticsResponse,
    MerchantDashboardResponse,
    RoomUsageListResponse,
    RoomUsageResponse,
)
from app.modules.availability.service import ranges_overlap, utc_now
from app.modules.cleaning.models import CleaningTask
from app.modules.cleaning.service import is_cleaning_task_overdue
from app.modules.devices.models import DeviceCommand
from app.modules.orders.models import Order
from app.modules.payments.models import Payment, Refund
from app.modules.rooms.models import Room
from app.modules.users.models import User
from app.modules.wallet.models import WalletLedger

ACTIVE_ORDER_STATUSES = {"paid", "in_use", "completed"}
DECIMAL_ZERO = Decimal("0.00")


def default_analytics_range(
    *,
    start_at: Optional[datetime],
    end_at: Optional[datetime],
) -> tuple[datetime, datetime]:
    resolved_end_at = normalize_datetime(end_at or utc_now())
    resolved_start_at = normalize_datetime(start_at or (resolved_end_at - timedelta(days=7)))
    return resolved_start_at, resolved_end_at


def normalize_datetime(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def decimal_money(value: Decimal) -> Decimal:
    return Decimal(value).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def overlap_hours(
    *,
    start_at: datetime,
    end_at: datetime,
    window_start_at: datetime,
    window_end_at: datetime,
) -> Decimal:
    start_at = normalize_datetime(start_at)
    end_at = normalize_datetime(end_at)
    if not ranges_overlap(start_at, end_at, window_start_at, window_end_at):
        return DECIMAL_ZERO
    clipped_start = max(start_at, window_start_at)
    clipped_end = min(end_at, window_end_at)
    seconds = Decimal(str((clipped_end - clipped_start).total_seconds()))
    return (seconds / Decimal("3600")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def utilization_rate(
    *,
    usage_hours: Decimal,
    room_count: int,
    start_at: datetime,
    end_at: datetime,
) -> Decimal:
    if room_count <= 0 or end_at <= start_at:
        return DECIMAL_ZERO
    window_hours = Decimal(str((end_at - start_at).total_seconds())) / Decimal("3600")
    capacity_hours = window_hours * Decimal(room_count)
    if capacity_hours <= 0:
        return DECIMAL_ZERO
    return (usage_hours / capacity_hours).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)


def _order_matches_window(order: Order, *, start_at: datetime, end_at: datetime) -> bool:
    return (
        order.status in ACTIVE_ORDER_STATUSES
        and ranges_overlap(
            normalize_datetime(order.start_at),
            normalize_datetime(order.end_at),
            start_at,
            end_at,
        )
    )


def build_room_usage_rows(
    *,
    rooms: Sequence[Room],
    orders: Sequence[Order],
    start_at: datetime,
    end_at: datetime,
) -> list[RoomUsageResponse]:
    rows = []
    for room in rooms:
        room_orders = [
            order
            for order in orders
            if order.room_id == room.id
            and _order_matches_window(order, start_at=start_at, end_at=end_at)
        ]
        hours = sum(
            (
                overlap_hours(
                    start_at=order.start_at,
                    end_at=order.end_at,
                    window_start_at=start_at,
                    window_end_at=end_at,
                )
                for order in room_orders
            ),
            DECIMAL_ZERO,
        )
        rows.append(
            RoomUsageResponse(
                room_id=room.id,
                room_name=room.name,
                order_count=len(room_orders),
                usage_hours=decimal_money(hours),
                utilization_rate=utilization_rate(
                    usage_hours=hours,
                    room_count=1,
                    start_at=start_at,
                    end_at=end_at,
                ),
            )
        )
    return rows


def build_cleaning_analytics(
    *,
    tenant_id: str,
    store_id: Optional[str],
    start_at: datetime,
    end_at: datetime,
    cleaning_tasks: Sequence[CleaningTask],
) -> CleaningAnalyticsResponse:
    return CleaningAnalyticsResponse(
        tenant_id=tenant_id,
        store_id=store_id,
        start_at=start_at,
        end_at=end_at,
        pending_count=sum(1 for task in cleaning_tasks if task.status == "pending"),
        accepted_count=sum(1 for task in cleaning_tasks if task.status == "accepted"),
        in_progress_count=sum(1 for task in cleaning_tasks if task.status == "in_progress"),
        pending_review_count=sum(1 for task in cleaning_tasks if task.status == "pending_review"),
        completed_count=sum(1 for task in cleaning_tasks if task.status == "completed"),
        rejected_count=sum(1 for task in cleaning_tasks if task.status == "rejected"),
        canceled_count=sum(1 for task in cleaning_tasks if task.status == "canceled"),
        complained_count=sum(1 for task in cleaning_tasks if task.status == "complained"),
        settled_count=sum(1 for task in cleaning_tasks if task.status == "settled"),
        overdue_count=sum(1 for task in cleaning_tasks if is_cleaning_task_overdue(task)),
        settlement_amount=decimal_money(
            sum(
                (
                    Decimal(task.settlement_amount)
                    for task in cleaning_tasks
                    if task.status == "settled"
                ),
                DECIMAL_ZERO,
            )
        ),
    )


def build_dashboard_summary(
    *,
    tenant_id: str,
    store_id: Optional[str],
    start_at: datetime,
    end_at: datetime,
    orders: Sequence[Order],
    payments: Sequence[Payment],
    refunds: Sequence[Refund],
    wallet_ledgers: Sequence[WalletLedger],
    users: Sequence[User],
    rooms: Sequence[Room],
    cleaning_tasks: Sequence[CleaningTask],
    device_commands: Sequence[DeviceCommand],
) -> MerchantDashboardResponse:
    gross_revenue = decimal_money(
        sum(
            (Decimal(payment.amount) for payment in payments if payment.status == "paid"),
            DECIMAL_ZERO,
        )
    )
    refund_amount = decimal_money(
        sum(
            (
                Decimal(refund.amount)
                for refund in refunds
                if refund.status in {"created", "refunded", "succeeded"}
            ),
            DECIMAL_ZERO,
        )
    )
    wallet_recharge_amount = decimal_money(
        sum(
            (
                Decimal(ledger.amount)
                for ledger in wallet_ledgers
                if ledger.direction == "credit" and ledger.biz_type == "mock_recharge"
            ),
            DECIMAL_ZERO,
        )
    )
    active_rooms = [room for room in rooms if room.status == "active"]
    usage_hours = decimal_money(
        sum(
            (
                overlap_hours(
                    start_at=order.start_at,
                    end_at=order.end_at,
                    window_start_at=start_at,
                    window_end_at=end_at,
                )
                for order in orders
                if _order_matches_window(order, start_at=start_at, end_at=end_at)
            ),
            DECIMAL_ZERO,
        )
    )
    return MerchantDashboardResponse(
        tenant_id=tenant_id,
        store_id=store_id,
        start_at=start_at,
        end_at=end_at,
        order_count=len(orders),
        paid_order_count=sum(1 for order in orders if order.status == "paid"),
        in_use_order_count=sum(1 for order in orders if order.status == "in_use"),
        completed_order_count=sum(1 for order in orders if order.status == "completed"),
        cancelled_order_count=sum(1 for order in orders if order.status == "cancelled"),
        gross_revenue=gross_revenue,
        refund_amount=refund_amount,
        net_revenue=decimal_money(gross_revenue - refund_amount),
        wallet_recharge_amount=wallet_recharge_amount,
        member_count=len(users),
        room_count=len(rooms),
        active_room_count=len(active_rooms),
        dirty_room_count=sum(1 for room in rooms if room.cleaning_status != "clean"),
        usage_hours=usage_hours,
        room_utilization_rate=utilization_rate(
            usage_hours=usage_hours,
            room_count=len(active_rooms),
            start_at=start_at,
            end_at=end_at,
        ),
        cleaning_pending_count=sum(1 for task in cleaning_tasks if task.status == "pending"),
        cleaning_overdue_count=sum(1 for task in cleaning_tasks if is_cleaning_task_overdue(task)),
        cleaning_completed_count=sum(1 for task in cleaning_tasks if task.status == "completed"),
        cleaning_complained_count=sum(1 for task in cleaning_tasks if task.status == "complained"),
        device_failure_count=sum(1 for command in device_commands if command.status == "failed"),
    )


async def _store_order_ids(
    session: AsyncSession,
    *,
    tenant_id: str,
    store_id: Optional[str],
) -> Optional[list[str]]:
    if store_id is None:
        return None
    rows = await session.scalars(
        select(Order.id).where(Order.tenant_id == tenant_id, Order.store_id == store_id)
    )
    return list(rows.all())


async def _load_dashboard_rows(
    session: AsyncSession,
    *,
    tenant_id: str,
    store_id: Optional[str],
    start_at: datetime,
    end_at: datetime,
) -> dict[str, object]:
    order_query = select(Order).where(
        Order.tenant_id == tenant_id,
        Order.created_at >= start_at,
        Order.created_at < end_at,
    )
    room_query = select(Room).where(Room.tenant_id == tenant_id)
    cleaning_query = select(CleaningTask).where(
        CleaningTask.tenant_id == tenant_id,
        CleaningTask.created_at >= start_at,
        CleaningTask.created_at < end_at,
    )
    device_query = select(DeviceCommand).where(
        DeviceCommand.tenant_id == tenant_id,
        DeviceCommand.created_at >= start_at,
        DeviceCommand.created_at < end_at,
    )
    if store_id is not None:
        order_query = order_query.where(Order.store_id == store_id)
        room_query = room_query.where(Room.store_id == store_id)
        cleaning_query = cleaning_query.where(CleaningTask.store_id == store_id)
    order_ids = await _store_order_ids(session, tenant_id=tenant_id, store_id=store_id)

    payment_query = select(Payment).where(
        Payment.tenant_id == tenant_id,
        Payment.paid_at.is_not(None),
        Payment.paid_at >= start_at,
        Payment.paid_at < end_at,
    )
    refund_query = select(Refund).where(
        Refund.tenant_id == tenant_id,
        Refund.created_at >= start_at,
        Refund.created_at < end_at,
    )
    if order_ids is not None:
        if not order_ids:
            payment_query = payment_query.where(false())
            refund_query = refund_query.where(false())
        else:
            payment_query = payment_query.where(Payment.order_id.in_(order_ids))
            refund_query = refund_query.where(Refund.order_id.in_(order_ids))

    wallet_query = select(WalletLedger).where(
        WalletLedger.tenant_id == tenant_id,
        WalletLedger.created_at >= start_at,
        WalletLedger.created_at < end_at,
    )
    user_query = select(User).where(User.tenant_id == tenant_id)
    return {
        "orders": list((await session.scalars(order_query)).all()),
        "payments": list((await session.scalars(payment_query)).all()),
        "refunds": list((await session.scalars(refund_query)).all()),
        "wallet_ledgers": list((await session.scalars(wallet_query)).all()),
        "users": list((await session.scalars(user_query)).all()),
        "rooms": list((await session.scalars(room_query)).all()),
        "cleaning_tasks": list((await session.scalars(cleaning_query)).all()),
        "device_commands": list((await session.scalars(device_query)).all()),
    }


async def get_dashboard_summary(
    session: AsyncSession,
    *,
    tenant_id: str,
    store_id: Optional[str],
    start_at: datetime,
    end_at: datetime,
) -> MerchantDashboardResponse:
    rows = await _load_dashboard_rows(
        session,
        tenant_id=tenant_id,
        store_id=store_id,
        start_at=start_at,
        end_at=end_at,
    )
    return build_dashboard_summary(
        tenant_id=tenant_id,
        store_id=store_id,
        start_at=start_at,
        end_at=end_at,
        orders=rows["orders"],  # type: ignore[arg-type]
        payments=rows["payments"],  # type: ignore[arg-type]
        refunds=rows["refunds"],  # type: ignore[arg-type]
        wallet_ledgers=rows["wallet_ledgers"],  # type: ignore[arg-type]
        users=rows["users"],  # type: ignore[arg-type]
        rooms=rows["rooms"],  # type: ignore[arg-type]
        cleaning_tasks=rows["cleaning_tasks"],  # type: ignore[arg-type]
        device_commands=rows["device_commands"],  # type: ignore[arg-type]
    )


async def get_room_usage(
    session: AsyncSession,
    *,
    tenant_id: str,
    store_id: Optional[str],
    start_at: datetime,
    end_at: datetime,
) -> RoomUsageListResponse:
    rows = await _load_dashboard_rows(
        session,
        tenant_id=tenant_id,
        store_id=store_id,
        start_at=start_at,
        end_at=end_at,
    )
    return RoomUsageListResponse(
        tenant_id=tenant_id,
        store_id=store_id,
        start_at=start_at,
        end_at=end_at,
        rooms=build_room_usage_rows(
            rooms=rows["rooms"],  # type: ignore[arg-type]
            orders=rows["orders"],  # type: ignore[arg-type]
            start_at=start_at,
            end_at=end_at,
        ),
    )


async def get_cleaning_analytics(
    session: AsyncSession,
    *,
    tenant_id: str,
    store_id: Optional[str],
    start_at: datetime,
    end_at: datetime,
) -> CleaningAnalyticsResponse:
    rows = await _load_dashboard_rows(
        session,
        tenant_id=tenant_id,
        store_id=store_id,
        start_at=start_at,
        end_at=end_at,
    )
    return build_cleaning_analytics(
        tenant_id=tenant_id,
        store_id=store_id,
        start_at=start_at,
        end_at=end_at,
        cleaning_tasks=rows["cleaning_tasks"],  # type: ignore[arg-type]
    )
