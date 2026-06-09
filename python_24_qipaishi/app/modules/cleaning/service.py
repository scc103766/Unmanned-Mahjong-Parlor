from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional

from fastapi import status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError
from app.modules.availability.service import utc_now
from app.modules.cleaning.models import CleaningProof, CleaningTask
from app.modules.devices.models import DeviceCommand
from app.modules.devices.service import execute_device_command, find_active_device
from app.modules.orders.models import Order
from app.modules.rooms.models import Room

CLEANING_DEFAULT_DURATION_MINUTES = 30
CLEANING_OVERDUE_STATUSES = {"pending", "accepted", "in_progress", "pending_review", "rejected"}
CLEANING_ACCESS_EARLY_MINUTES = 15
CLEANING_ACCESS_LATE_MINUTES = 8 * 60
CLEANING_TERMINAL_STATUSES = {"completed", "settled", "complained", "canceled"}


async def create_cleaning_task_for_order(
    session: AsyncSession,
    *,
    order: Order,
) -> CleaningTask:
    existing = await session.scalar(
        select(CleaningTask).where(
            CleaningTask.tenant_id == order.tenant_id,
            CleaningTask.order_id == order.id,
        )
    )
    if existing is not None:
        if existing.status == "canceled":
            existing.status = "pending"
            existing.cleaner_id = None
            existing.accepted_at = None
            existing.started_at = None
            existing.completed_at = None
            existing.reviewed_at = None
            existing.settled_at = None
            existing.canceled_at = None
            existing.cancel_reason = None
            existing.review_note = None
            existing.complaint_reason = None
            existing.complained_at = None
            existing.scheduled_start_at = order.end_at
            existing.scheduled_end_at = order.end_at + timedelta(
                minutes=CLEANING_DEFAULT_DURATION_MINUTES
            )
            existing.settlement_amount = Decimal("0.00")
            room = await session.get(Room, order.room_id)
            if room is not None:
                room.cleaning_status = "dirty"
            await session.flush()
        return existing

    task = CleaningTask(
        tenant_id=order.tenant_id,
        store_id=order.store_id,
        room_id=order.room_id,
        order_id=order.id,
        status="pending",
        scheduled_start_at=order.end_at,
        scheduled_end_at=order.end_at + timedelta(minutes=CLEANING_DEFAULT_DURATION_MINUTES),
        settlement_amount=Decimal("0.00"),
    )
    session.add(task)
    room = await session.get(Room, order.room_id)
    if room is not None:
        room.cleaning_status = "dirty"
    await session.flush()
    return task


def ensure_order_can_create_cleaning_task(order: Order) -> None:
    if order.status not in {"completed", "cancelled"}:
        raise AppError(
            "ORDER_STATE_INVALID",
            "Only completed or cancelled used orders can trigger cleaning tasks.",
            status.HTTP_409_CONFLICT,
        )
    if order.status == "cancelled" and order.started_at is None:
        raise AppError(
            "ORDER_NOT_USED",
            "Cancelled orders that were not started do not need cleaning tasks.",
            status.HTTP_409_CONFLICT,
        )


async def load_cleaning_task(
    session: AsyncSession,
    *,
    task_id: str,
    tenant_id: str,
) -> CleaningTask:
    task = await session.get(CleaningTask, task_id)
    if task is None or task.tenant_id != tenant_id:
        raise AppError(
            "CLEANING_TASK_NOT_FOUND",
            "Cleaning task was not found.",
            status.HTTP_404_NOT_FOUND,
        )
    return task


def ensure_cleaner_can_operate(task: CleaningTask, *, cleaner_id: str) -> None:
    if task.cleaner_id != cleaner_id:
        raise AppError(
            "CLEANING_TASK_FORBIDDEN",
            "Cleaning task is not assigned to this cleaner.",
            status.HTTP_403_FORBIDDEN,
        )


def accept_cleaning_task(task: CleaningTask, *, cleaner_id: str) -> CleaningTask:
    if task.status != "pending":
        raise AppError(
            "CLEANING_TASK_STATE_INVALID",
            "Only pending cleaning tasks can be accepted.",
            status.HTTP_409_CONFLICT,
        )
    task.status = "accepted"
    task.cleaner_id = cleaner_id
    task.accepted_at = utc_now()
    return task


def unaccept_cleaning_task(task: CleaningTask, *, cleaner_id: str) -> CleaningTask:
    ensure_cleaner_can_operate(task, cleaner_id=cleaner_id)
    if task.status != "accepted":
        raise AppError(
            "CLEANING_TASK_STATE_INVALID",
            "Only accepted cleaning tasks can be released.",
            status.HTTP_409_CONFLICT,
        )
    task.status = "pending"
    task.cleaner_id = None
    task.accepted_at = None
    return task


def start_cleaning_task(task: CleaningTask, *, cleaner_id: str) -> CleaningTask:
    ensure_cleaner_can_operate(task, cleaner_id=cleaner_id)
    if task.status != "accepted":
        raise AppError(
            "CLEANING_TASK_STATE_INVALID",
            "Only accepted cleaning tasks can be started.",
            status.HTTP_409_CONFLICT,
        )
    task.status = "in_progress"
    task.started_at = utc_now()
    return task


async def complete_cleaning_task(
    session: AsyncSession,
    *,
    task: CleaningTask,
    cleaner_id: str,
    image_urls: list[str],
    remark: Optional[str],
) -> CleaningTask:
    ensure_cleaner_can_operate(task, cleaner_id=cleaner_id)
    if task.status != "in_progress":
        raise AppError(
            "CLEANING_TASK_STATE_INVALID",
            "Only in-progress cleaning tasks can be completed.",
            status.HTTP_409_CONFLICT,
        )
    task.status = "pending_review"
    task.completed_at = utc_now()
    if image_urls or remark:
        session.add(
            CleaningProof(
                tenant_id=task.tenant_id,
                task_id=task.id,
                uploaded_by=cleaner_id,
                image_urls=image_urls,
                remark=remark,
            )
        )
    await session.flush()
    return task


def review_cleaning_task(
    task: CleaningTask,
    *,
    approved: bool,
    note: Optional[str],
) -> CleaningTask:
    if task.status != "pending_review":
        raise AppError(
            "CLEANING_TASK_STATE_INVALID",
            "Only pending-review cleaning tasks can be reviewed.",
            status.HTTP_409_CONFLICT,
        )
    task.status = "completed" if approved else "rejected"
    task.reviewed_at = utc_now()
    task.review_note = note
    return task


async def mark_room_clean_after_approval(
    session: AsyncSession,
    *,
    task: CleaningTask,
) -> None:
    room = await session.get(Room, task.room_id)
    if room is not None:
        room.cleaning_status = "clean"
    await session.flush()


def reassign_cleaning_task(task: CleaningTask, *, note: Optional[str]) -> CleaningTask:
    if task.status != "rejected":
        raise AppError(
            "CLEANING_TASK_STATE_INVALID",
            "Only rejected cleaning tasks can be reassigned.",
            status.HTTP_409_CONFLICT,
        )
    task.status = "pending"
    task.cleaner_id = None
    task.accepted_at = None
    task.started_at = None
    task.completed_at = None
    task.reviewed_at = None
    task.review_note = note
    return task


def cancel_cleaning_task(task: CleaningTask, *, reason: Optional[str]) -> CleaningTask:
    if task.status in CLEANING_TERMINAL_STATUSES:
        raise AppError(
            "CLEANING_TASK_STATE_INVALID",
            "Terminal cleaning tasks cannot be cancelled.",
            status.HTTP_409_CONFLICT,
        )
    task.status = "canceled"
    task.cancel_reason = reason
    task.canceled_at = utc_now()
    return task


def complain_cleaning_task(task: CleaningTask, *, reason: str) -> CleaningTask:
    if task.status not in {"pending_review", "completed", "settled"}:
        raise AppError(
            "CLEANING_TASK_STATE_INVALID",
            "Only submitted or completed cleaning tasks can be complained.",
            status.HTTP_409_CONFLICT,
        )
    task.status = "complained"
    task.complaint_reason = reason
    task.complained_at = utc_now()
    return task


def settle_cleaning_task(
    task: CleaningTask,
    *,
    amount: Decimal,
    note: Optional[str],
) -> CleaningTask:
    if task.status != "completed":
        raise AppError(
            "CLEANING_TASK_STATE_INVALID",
            "Only completed cleaning tasks can be settled.",
            status.HTTP_409_CONFLICT,
        )
    task.status = "settled"
    task.settled_at = utc_now()
    task.settlement_amount = amount
    task.review_note = note or task.review_note
    return task


def is_cleaning_task_overdue(task: CleaningTask, *, now: Optional[datetime] = None) -> bool:
    now = now or utc_now()
    return (
        task.status in CLEANING_OVERDUE_STATUSES
        and task.scheduled_end_at is not None
        and task.scheduled_end_at < now
    )


def ensure_cleaning_access_window(task: CleaningTask, *, now: Optional[datetime] = None) -> None:
    now = now or utc_now()
    if task.scheduled_start_at is not None:
        earliest = task.scheduled_start_at - timedelta(minutes=CLEANING_ACCESS_EARLY_MINUTES)
        if now < earliest:
            raise AppError(
                "CLEANING_ACCESS_TOO_EARLY",
                "Cleaning room door access is not available yet.",
                status.HTTP_409_CONFLICT,
            )
    if task.scheduled_end_at is not None:
        latest = task.scheduled_end_at + timedelta(minutes=CLEANING_ACCESS_LATE_MINUTES)
        if now > latest:
            raise AppError(
                "CLEANING_ACCESS_EXPIRED",
                "Cleaning room door access window has expired.",
                status.HTTP_409_CONFLICT,
            )


async def execute_cleaning_open_door(
    session: AsyncSession,
    *,
    task: CleaningTask,
    cleaner_id: str,
    idempotency_key: Optional[str],
) -> DeviceCommand:
    ensure_cleaner_can_operate(task, cleaner_id=cleaner_id)
    if task.status not in {"accepted", "in_progress"}:
        raise AppError(
            "CLEANING_TASK_STATE_INVALID",
            "Only accepted or in-progress cleaning tasks can open room doors.",
            status.HTTP_409_CONFLICT,
        )
    ensure_cleaning_access_window(task)
    device = await find_active_device(
        session,
        tenant_id=task.tenant_id,
        store_id=task.store_id,
        room_id=task.room_id,
        device_type="room_door",
    )
    return await execute_device_command(
        session,
        device=device,
        actor_id=cleaner_id,
        command="open",
        biz_type="cleaning_task",
        biz_id=task.id,
        idempotency_key=idempotency_key,
        request_payload={
            "task_id": task.id,
            "order_id": task.order_id,
            "store_id": task.store_id,
            "room_id": task.room_id,
            "command": "open",
        },
    )
