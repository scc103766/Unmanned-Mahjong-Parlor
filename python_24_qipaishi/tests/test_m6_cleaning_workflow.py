from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

import pytest

from app.core.errors import AppError
from app.main import create_app
from app.modules.availability.service import room_conflict_reasons
from app.modules.cleaning.models import CleaningTask
from app.modules.cleaning.schemas import (
    CleaningTaskCancelRequest,
    CleaningTaskComplainRequest,
    CleaningTaskCompleteRequest,
    CleaningTaskReassignRequest,
    CleaningTaskReviewRequest,
    CleaningTaskSettleRequest,
)
from app.modules.cleaning.service import (
    accept_cleaning_task,
    cancel_cleaning_task,
    complain_cleaning_task,
    create_cleaning_task_for_order,
    ensure_cleaning_access_window,
    ensure_order_can_create_cleaning_task,
    is_cleaning_task_overdue,
    reassign_cleaning_task,
    review_cleaning_task,
    settle_cleaning_task,
    start_cleaning_task,
    unaccept_cleaning_task,
)
from app.modules.orders.models import Order
from app.modules.rooms.models import Room
from app.modules.stores.models import Store


class FakeAvailabilitySession:
    def __init__(self, *, room: Room, store: Store) -> None:
        self.room = room
        self.store = store

    async def get(self, model: Any, object_id: str) -> Any:
        if model is Room and object_id == self.room.id:
            return self.room
        if model is Store and object_id == self.store.id:
            return self.store
        return None

    async def scalar(self, statement: Any) -> None:
        return None


class FakeCleaningSession:
    def __init__(self, *, existing_task: CleaningTask, room: Room) -> None:
        self.existing_task = existing_task
        self.room = room
        self.flushed = False

    async def scalar(self, statement: Any) -> CleaningTask:
        return self.existing_task

    async def get(self, model: Any, object_id: str) -> Any:
        if model is Room and object_id == self.room.id:
            return self.room
        return None

    def add(self, value: Any) -> None:
        return None

    async def flush(self) -> None:
        self.flushed = True


def test_m6_cleaning_routes_are_registered() -> None:
    route_paths = {route.path for route in create_app().routes}

    assert "/api/v1/cleaning/tasks" in route_paths
    assert "/api/v1/cleaning/tasks/{task_id}/accept" in route_paths
    assert "/api/v1/cleaning/tasks/{task_id}/unaccept" in route_paths
    assert "/api/v1/cleaning/tasks/{task_id}/start" in route_paths
    assert "/api/v1/cleaning/tasks/{task_id}/open-door" in route_paths
    assert "/api/v1/cleaning/tasks/{task_id}/complete" in route_paths
    assert "/api/v1/cleaning/tasks/{task_id}/review" in route_paths
    assert "/api/v1/cleaning/tasks/{task_id}/cancel" in route_paths
    assert "/api/v1/cleaning/tasks/{task_id}/reassign" in route_paths
    assert "/api/v1/cleaning/tasks/{task_id}/complain" in route_paths
    assert "/api/v1/cleaning/tasks/{task_id}/settle" in route_paths
    assert "/api/v1/cleaning/summary" in route_paths
    assert "/api/v1/orders/{order_id}/cleaning-task" in route_paths


def test_cleaning_request_defaults() -> None:
    complete_payload = CleaningTaskCompleteRequest()
    review_payload = CleaningTaskReviewRequest()
    cancel_payload = CleaningTaskCancelRequest(reason="manual")
    reassign_payload = CleaningTaskReassignRequest(note="redo")
    complain_payload = CleaningTaskComplainRequest(reason="not clean")
    settle_payload = CleaningTaskSettleRequest(amount=Decimal("12.50"), note="settle ok")

    assert complete_payload.image_urls == []
    assert review_payload.approved is True
    assert cancel_payload.reason == "manual"
    assert reassign_payload.note == "redo"
    assert complain_payload.reason == "not clean"
    assert settle_payload.amount == Decimal("12.50")
    assert settle_payload.note == "settle ok"


def test_cleaning_task_state_flow() -> None:
    task = CleaningTask(
        tenant_id="tenant_1",
        store_id="store_1",
        room_id="room_1",
        order_id="order_1",
        status="pending",
        scheduled_start_at=datetime(2026, 5, 15, 12, 0, tzinfo=timezone.utc),
    )

    accept_cleaning_task(task, cleaner_id="cleaner_1")
    assert task.status == "accepted"
    assert task.cleaner_id == "cleaner_1"

    start_cleaning_task(task, cleaner_id="cleaner_1")
    assert task.status == "in_progress"

    task.status = "pending_review"
    review_cleaning_task(task, approved=True, note="ok")
    assert task.status == "completed"
    assert task.review_note == "ok"

    settle_cleaning_task(task, amount=Decimal("12.50"), note="settled")
    assert task.status == "settled"
    assert task.settlement_amount == Decimal("12.50")
    assert task.review_note == "settled"


def test_cleaning_task_rejects_wrong_cleaner() -> None:
    task = CleaningTask(
        tenant_id="tenant_1",
        store_id="store_1",
        room_id="room_1",
        order_id="order_1",
        cleaner_id="cleaner_1",
        status="accepted",
    )

    with pytest.raises(AppError) as exc_info:
        start_cleaning_task(task, cleaner_id="cleaner_2")

    assert exc_info.value.code == "CLEANING_TASK_FORBIDDEN"


def test_cleaning_review_can_reject_task() -> None:
    task = CleaningTask(
        tenant_id="tenant_1",
        store_id="store_1",
        room_id="room_1",
        order_id="order_1",
        cleaner_id="cleaner_1",
        status="pending_review",
    )

    review_cleaning_task(task, approved=False, note="redo")

    assert task.status == "rejected"
    assert task.review_note == "redo"


def test_cleaning_reassign_flow() -> None:
    task = CleaningTask(
        tenant_id="tenant_1",
        store_id="store_1",
        room_id="room_1",
        order_id="order_1",
        cleaner_id="cleaner_1",
        status="rejected",
    )

    reassign_cleaning_task(task, note="redo")

    assert task.status == "pending"
    assert task.cleaner_id is None
    assert task.review_note == "redo"


def test_cleaner_can_unaccept_accepted_task() -> None:
    task = CleaningTask(
        tenant_id="tenant_1",
        store_id="store_1",
        room_id="room_1",
        order_id="order_1",
        cleaner_id="cleaner_1",
        status="accepted",
    )

    unaccept_cleaning_task(task, cleaner_id="cleaner_1")

    assert task.status == "pending"
    assert task.cleaner_id is None
    assert task.accepted_at is None


def test_cleaning_cancel_flow() -> None:
    task = CleaningTask(
        tenant_id="tenant_1",
        store_id="store_1",
        room_id="room_1",
        order_id="order_1",
        status="pending",
    )

    cancel_cleaning_task(task, reason="duplicate")

    assert task.status == "canceled"
    assert task.cancel_reason == "duplicate"
    assert task.canceled_at is not None


def test_cleaning_complain_flow() -> None:
    task = CleaningTask(
        tenant_id="tenant_1",
        store_id="store_1",
        room_id="room_1",
        order_id="order_1",
        cleaner_id="cleaner_1",
        status="completed",
    )

    complain_cleaning_task(task, reason="not clean")

    assert task.status == "complained"
    assert task.complaint_reason == "not clean"


def test_cleaning_overdue_helper() -> None:
    now = datetime(2026, 5, 15, 12, 0, tzinfo=timezone.utc)
    task = CleaningTask(
        tenant_id="tenant_1",
        store_id="store_1",
        room_id="room_1",
        order_id="order_1",
        status="pending",
        scheduled_end_at=now - timedelta(minutes=1),
    )

    assert is_cleaning_task_overdue(task, now=now)


def test_cleaning_access_window_rejects_too_early_open_door() -> None:
    now = datetime(2026, 5, 15, 12, 0, tzinfo=timezone.utc)
    task = CleaningTask(
        tenant_id="tenant_1",
        store_id="store_1",
        room_id="room_1",
        order_id="order_1",
        cleaner_id="cleaner_1",
        status="accepted",
        scheduled_start_at=now + timedelta(hours=1),
        scheduled_end_at=now + timedelta(hours=2),
    )

    with pytest.raises(AppError) as exc_info:
        ensure_cleaning_access_window(task, now=now)

    assert exc_info.value.code == "CLEANING_ACCESS_TOO_EARLY"


def test_completed_or_used_cancelled_order_can_trigger_cleaning() -> None:
    completed_order = Order(
        tenant_id="tenant_1",
        store_id="store_1",
        room_id="room_1",
        user_id="user_1",
        order_no="order_1",
        start_at=datetime(2026, 5, 15, 10, 0, tzinfo=timezone.utc),
        end_at=datetime(2026, 5, 15, 12, 0, tzinfo=timezone.utc),
        status="completed",
        total_amount=Decimal("80.00"),
        payable_amount=Decimal("80.00"),
    )
    unused_cancelled_order = Order(
        tenant_id="tenant_1",
        store_id="store_1",
        room_id="room_1",
        user_id="user_1",
        order_no="order_2",
        start_at=datetime(2026, 5, 15, 10, 0, tzinfo=timezone.utc),
        end_at=datetime(2026, 5, 15, 12, 0, tzinfo=timezone.utc),
        status="cancelled",
        total_amount=Decimal("80.00"),
        payable_amount=Decimal("80.00"),
    )

    ensure_order_can_create_cleaning_task(completed_order)
    with pytest.raises(AppError) as exc_info:
        ensure_order_can_create_cleaning_task(unused_cancelled_order)

    assert exc_info.value.code == "ORDER_NOT_USED"


async def test_cancelled_cleaning_task_is_reactivated_for_manual_trigger() -> None:
    end_at = datetime(2026, 5, 15, 12, 0, tzinfo=timezone.utc)
    order = Order(
        tenant_id="tenant_1",
        store_id="store_1",
        room_id="room_1",
        user_id="user_1",
        order_no="order_1",
        start_at=end_at - timedelta(hours=2),
        end_at=end_at,
        status="completed",
        total_amount=Decimal("80.00"),
        payable_amount=Decimal("80.00"),
    )
    task = CleaningTask(
        tenant_id="tenant_1",
        store_id="store_1",
        room_id="room_1",
        order_id="order_1",
        status="canceled",
        cancel_reason="duplicate",
        canceled_at=end_at,
    )
    room = Room(
        id="room_1",
        tenant_id="tenant_1",
        store_id="store_1",
        name="A101",
        status="active",
        cleaning_status="clean",
    )
    session = FakeCleaningSession(existing_task=task, room=room)

    result = await create_cleaning_task_for_order(session, order=order)

    assert result is task
    assert task.status == "pending"
    assert task.cancel_reason is None
    assert task.canceled_at is None
    assert room.cleaning_status == "dirty"
    assert session.flushed


async def test_dirty_room_blocks_availability_by_default() -> None:
    now = datetime(2026, 5, 15, 12, 0, tzinfo=timezone.utc)
    room = Room(
        id="room_1",
        tenant_id="tenant_1",
        store_id="store_1",
        name="A101",
        status="active",
        cleaning_status="dirty",
    )
    store = Store(id="store_1", tenant_id="tenant_1", name="Main", cleaning_settings={})

    reasons = await room_conflict_reasons(
        FakeAvailabilitySession(room=room, store=store),
        tenant_id="tenant_1",
        room_id="room_1",
        start_at=now + timedelta(hours=1),
        end_at=now + timedelta(hours=2),
        now=now,
    )

    assert reasons == ["room_needs_cleaning"]


async def test_dirty_room_can_be_allowed_by_store_policy() -> None:
    now = datetime(2026, 5, 15, 12, 0, tzinfo=timezone.utc)
    room = Room(
        id="room_1",
        tenant_id="tenant_1",
        store_id="store_1",
        name="A101",
        status="active",
        cleaning_status="dirty",
    )
    store = Store(
        id="store_1",
        tenant_id="tenant_1",
        name="Main",
        cleaning_settings={"allow_dirty_booking": True},
    )

    reasons = await room_conflict_reasons(
        FakeAvailabilitySession(room=room, store=store),
        tenant_id="tenant_1",
        room_id="room_1",
        start_at=now + timedelta(hours=1),
        end_at=now + timedelta(hours=2),
        now=now,
    )

    assert "room_needs_cleaning" not in reasons
