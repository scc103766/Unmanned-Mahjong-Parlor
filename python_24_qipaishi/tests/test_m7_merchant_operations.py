from datetime import datetime, timedelta, timezone
from decimal import Decimal

from app.main import create_app
from app.modules.analytics.service import build_dashboard_summary, build_room_usage_rows
from app.modules.cleaning.models import CleaningTask
from app.modules.devices.models import Device, DeviceCommand
from app.modules.members.service import build_member_summary
from app.modules.operations.service import build_operation_exceptions
from app.modules.orders.models import Order
from app.modules.orders.service import ensure_reschedulable
from app.modules.payments.models import Payment, Refund
from app.modules.rooms.models import Room
from app.modules.users.models import User
from app.modules.wallet.models import WalletAccount, WalletLedger
from app.modules.wallet.service import adjust_wallet
from app.modules.withdrawals.models import Withdrawal
from app.modules.withdrawals.service import (
    approve_withdrawal,
    mark_withdrawal_paid,
    reject_withdrawal,
)


class FakeWalletSession:
    def __init__(self, *, wallet: WalletAccount) -> None:
        self.wallet = wallet
        self.added = []
        self.flushed = False

    async def scalar(self, statement):
        return self.wallet

    def add(self, value) -> None:
        self.added.append(value)

    async def flush(self) -> None:
        self.flushed = True


def test_m7_routes_are_registered() -> None:
    route_paths = {route.path for route in create_app().routes}

    assert "/api/v1/analytics/dashboard" in route_paths
    assert "/api/v1/analytics/rooms/usage" in route_paths
    assert "/api/v1/analytics/cleaning" in route_paths
    assert "/api/v1/operations/exceptions" in route_paths
    assert "/api/v1/operations/audit-logs" in route_paths
    assert "/api/v1/operations/compensations" in route_paths
    assert "/api/v1/orders/{order_id}/reschedule/quote" in route_paths
    assert "/api/v1/orders/{order_id}/reschedule" in route_paths
    assert "/api/v1/withdrawals" in route_paths
    assert "/api/v1/withdrawals/me" in route_paths
    assert "/api/v1/withdrawals/{withdrawal_id}/approve" in route_paths
    assert "/api/v1/withdrawals/{withdrawal_id}/reject" in route_paths
    assert "/api/v1/withdrawals/{withdrawal_id}/mark-paid" in route_paths
    assert "/api/v1/wallets/admin/adjustments" in route_paths
    assert "/api/v1/coupons/admin/issue" in route_paths
    assert "/api/v1/members" in route_paths
    assert "/api/v1/members/{user_id}" in route_paths


def test_merchant_dashboard_summary_aggregates_fact_tables() -> None:
    start_at = datetime(2026, 5, 15, 10, 0, tzinfo=timezone.utc)
    end_at = datetime(2026, 5, 15, 12, 0, tzinfo=timezone.utc)
    order = Order(
        id="order_1",
        tenant_id="tenant_1",
        store_id="store_1",
        room_id="room_1",
        user_id="user_1",
        order_no="order_1",
        start_at=start_at + timedelta(minutes=30),
        end_at=start_at + timedelta(minutes=90),
        status="completed",
        total_amount=Decimal("100.00"),
        payable_amount=Decimal("100.00"),
        created_at=start_at,
    )
    payment = Payment(
        id="payment_1",
        tenant_id="tenant_1",
        order_id="order_1",
        amount=Decimal("100.00"),
        status="paid",
        paid_at=start_at + timedelta(minutes=1),
        created_at=start_at,
    )
    refund = Refund(
        id="refund_1",
        tenant_id="tenant_1",
        payment_id="payment_1",
        order_id="order_1",
        refund_no="refund_1",
        amount=Decimal("20.00"),
        status="refunded",
        created_at=start_at,
    )
    ledger = WalletLedger(
        id="ledger_1",
        tenant_id="tenant_1",
        account_id="wallet_1",
        user_id="user_1",
        direction="credit",
        amount=Decimal("50.00"),
        cash_balance_after=Decimal("50.00"),
        gift_balance_after=Decimal("0.00"),
        biz_type="mock_recharge",
        created_at=start_at,
    )
    rooms = [
        Room(
            id="room_1",
            tenant_id="tenant_1",
            store_id="store_1",
            name="A101",
            status="active",
            cleaning_status="clean",
        ),
        Room(
            id="room_2",
            tenant_id="tenant_1",
            store_id="store_1",
            name="A102",
            status="active",
            cleaning_status="dirty",
        ),
    ]
    cleaning_task = CleaningTask(
        id="task_1",
        tenant_id="tenant_1",
        store_id="store_1",
        room_id="room_2",
        order_id="order_1",
        status="pending",
        scheduled_end_at=datetime(2020, 1, 1, tzinfo=timezone.utc),
        created_at=start_at,
    )
    device_command = DeviceCommand(
        id="command_1",
        tenant_id="tenant_1",
        device_id="device_1",
        command="open",
        biz_type="order",
        biz_id="order_1",
        status="failed",
        created_at=start_at,
    )

    summary = build_dashboard_summary(
        tenant_id="tenant_1",
        store_id="store_1",
        start_at=start_at,
        end_at=end_at,
        orders=[order],
        payments=[payment],
        refunds=[refund],
        wallet_ledgers=[ledger],
        users=[User(id="user_1", tenant_id="tenant_1"), User(id="user_2", tenant_id="tenant_1")],
        rooms=rooms,
        cleaning_tasks=[cleaning_task],
        device_commands=[device_command],
    )

    assert summary.order_count == 1
    assert summary.completed_order_count == 1
    assert summary.gross_revenue == Decimal("100.00")
    assert summary.refund_amount == Decimal("20.00")
    assert summary.net_revenue == Decimal("80.00")
    assert summary.wallet_recharge_amount == Decimal("50.00")
    assert summary.member_count == 2
    assert summary.dirty_room_count == 1
    assert summary.usage_hours == Decimal("1.00")
    assert summary.room_utilization_rate == Decimal("0.2500")
    assert summary.cleaning_overdue_count == 1
    assert summary.device_failure_count == 1


def test_room_usage_rows_are_per_room() -> None:
    start_at = datetime(2026, 5, 15, 10, 0, tzinfo=timezone.utc)
    end_at = datetime(2026, 5, 15, 12, 0, tzinfo=timezone.utc)
    room = Room(
        id="room_1",
        tenant_id="tenant_1",
        store_id="store_1",
        name="A101",
        status="active",
        cleaning_status="clean",
    )
    order = Order(
        tenant_id="tenant_1",
        store_id="store_1",
        room_id="room_1",
        user_id="user_1",
        order_no="order_1",
        start_at=start_at,
        end_at=end_at,
        status="completed",
        total_amount=Decimal("100.00"),
        payable_amount=Decimal("100.00"),
    )

    rows = build_room_usage_rows(rooms=[room], orders=[order], start_at=start_at, end_at=end_at)

    assert rows[0].room_id == "room_1"
    assert rows[0].order_count == 1
    assert rows[0].usage_hours == Decimal("2.00")
    assert rows[0].utilization_rate == Decimal("1.0000")


def test_operation_exceptions_include_core_m7_sources() -> None:
    now = datetime(2026, 5, 15, 12, 0, tzinfo=timezone.utc)
    payment = Payment(
        id="payment_1",
        tenant_id="tenant_1",
        order_id="order_1",
        amount=Decimal("100.00"),
        status="paying",
        created_at=now - timedelta(hours=1),
    )
    refund = Refund(
        id="refund_1",
        tenant_id="tenant_1",
        payment_id="payment_1",
        order_id="order_1",
        refund_no="refund_1",
        amount=Decimal("20.00"),
        status="failed",
        created_at=now,
    )
    device = Device(
        id="device_1",
        tenant_id="tenant_1",
        store_id="store_1",
        name="Door",
        device_type="room_door",
        provider="mock",
        external_id="mock_fail",
    )
    command = DeviceCommand(
        id="command_1",
        tenant_id="tenant_1",
        device_id="device_1",
        command="open",
        biz_type="order",
        biz_id="order_1",
        status="failed",
        failure_reason="adapter failed",
        created_at=now,
    )
    cleaning_task = CleaningTask(
        id="task_1",
        tenant_id="tenant_1",
        store_id="store_1",
        room_id="room_1",
        order_id="order_1",
        status="pending",
        scheduled_end_at=now - timedelta(minutes=1),
        created_at=now,
    )
    withdrawal = Withdrawal(
        id="withdrawal_1",
        tenant_id="tenant_1",
        user_id="user_1",
        requested_by="user_1",
        amount=Decimal("30.00"),
        status="pending",
        requested_at=now - timedelta(days=2),
        created_at=now - timedelta(days=2),
    )

    exceptions = build_operation_exceptions(
        payments=[payment],
        refunds=[refund],
        withdrawals=[withdrawal],
        device_commands=[command],
        devices=[device],
        cleaning_tasks=[cleaning_task],
        now=now,
    )

    sources = {row.source for row in exceptions}
    assert {"payment", "refund", "withdrawal", "device", "cleaning"} == sources
    assert {row.entity_type for row in exceptions} >= {
        "payment",
        "refund",
        "withdrawal",
        "device_command",
        "cleaning_task",
    }


async def test_withdrawal_approval_debits_cash_wallet_and_marks_paid() -> None:
    wallet = WalletAccount(
        id="wallet_1",
        tenant_id="tenant_1",
        user_id="user_1",
        cash_balance=Decimal("100.00"),
        gift_balance=Decimal("20.00"),
        status="active",
    )
    withdrawal = Withdrawal(
        id="withdrawal_1",
        tenant_id="tenant_1",
        user_id="user_1",
        requested_by="user_1",
        amount=Decimal("30.00"),
        status="pending",
        requested_at=datetime(2026, 5, 15, 12, 0, tzinfo=timezone.utc),
    )
    session = FakeWalletSession(wallet=wallet)

    await approve_withdrawal(
        session,
        withdrawal=withdrawal,
        reviewer_id="admin_1",
        note="ok",
    )
    mark_withdrawal_paid(
        withdrawal,
        paid_by="admin_1",
        payout_ref="wx-001",
        note="paid",
    )

    assert wallet.cash_balance == Decimal("70.00")
    assert wallet.gift_balance == Decimal("20.00")
    assert withdrawal.status == "paid"
    assert withdrawal.payout_ref == "wx-001"
    assert len(session.added) == 1
    assert session.added[0].biz_type == "withdrawal"
    assert session.flushed


def test_pending_withdrawal_can_be_rejected() -> None:
    withdrawal = Withdrawal(
        tenant_id="tenant_1",
        user_id="user_1",
        requested_by="user_1",
        amount=Decimal("30.00"),
        status="pending",
        requested_at=datetime(2026, 5, 15, 12, 0, tzinfo=timezone.utc),
    )

    reject_withdrawal(withdrawal, reviewer_id="admin_1", reason="bad account")

    assert withdrawal.status == "rejected"
    assert withdrawal.reject_reason == "bad account"
    assert withdrawal.rejected_at is not None


async def test_manual_wallet_adjustment_credits_cash_and_gift() -> None:
    wallet = WalletAccount(
        id="wallet_1",
        tenant_id="tenant_1",
        user_id="user_1",
        cash_balance=Decimal("10.00"),
        gift_balance=Decimal("2.00"),
        status="active",
    )
    session = FakeWalletSession(wallet=wallet)

    await adjust_wallet(
        session,
        tenant_id="tenant_1",
        user_id="user_1",
        direction="credit",
        cash_amount=Decimal("5.00"),
        gift_amount=Decimal("3.00"),
        actor_id="admin_1",
        remark="compensation",
    )

    assert wallet.cash_balance == Decimal("15.00")
    assert wallet.gift_balance == Decimal("5.00")
    assert session.added[0].biz_type == "manual_adjustment"


def test_member_summary_combines_consumption_wallet_and_coupon_state() -> None:
    user = User(id="user_1", tenant_id="tenant_1", phone="13800000000", status="active")
    wallet = WalletAccount(
        id="wallet_1",
        tenant_id="tenant_1",
        user_id="user_1",
        cash_balance=Decimal("10.00"),
        gift_balance=Decimal("2.00"),
        status="active",
    )
    orders = [
        Order(
            tenant_id="tenant_1",
            store_id="store_1",
            room_id="room_1",
            user_id="user_1",
            order_no="order_1",
            start_at=datetime(2026, 5, 15, 10, 0, tzinfo=timezone.utc),
            end_at=datetime(2026, 5, 15, 12, 0, tzinfo=timezone.utc),
            status="completed",
            total_amount=Decimal("80.00"),
            payable_amount=Decimal("70.00"),
        ),
        Order(
            tenant_id="tenant_1",
            store_id="store_1",
            room_id="room_1",
            user_id="user_1",
            order_no="order_2",
            start_at=datetime(2026, 5, 16, 10, 0, tzinfo=timezone.utc),
            end_at=datetime(2026, 5, 16, 12, 0, tzinfo=timezone.utc),
            status="cancelled",
            total_amount=Decimal("80.00"),
            payable_amount=Decimal("80.00"),
        ),
    ]
    coupons = [
        type("CouponStub", (), {"status": "available"})(),
        type("CouponStub", (), {"status": "used"})(),
    ]

    summary = build_member_summary(user=user, wallet=wallet, orders=orders, coupons=coupons)

    assert summary.order_count == 2
    assert summary.completed_order_count == 1
    assert summary.total_spend == Decimal("70.00")
    assert summary.cash_balance == Decimal("10.00")
    assert summary.available_coupon_count == 1


def test_reschedule_guard_allows_pending_and_paid_orders() -> None:
    pending_order = Order(
        tenant_id="tenant_1",
        store_id="store_1",
        room_id="room_1",
        user_id="user_1",
        order_no="order_1",
        start_at=datetime(2026, 5, 15, 10, 0, tzinfo=timezone.utc),
        end_at=datetime(2026, 5, 15, 12, 0, tzinfo=timezone.utc),
        status="pending_payment",
        total_amount=Decimal("80.00"),
        payable_amount=Decimal("80.00"),
    )
    paid_order = Order(
        tenant_id="tenant_1",
        store_id="store_1",
        room_id="room_1",
        user_id="user_1",
        order_no="order_2",
        start_at=datetime(2026, 5, 15, 10, 0, tzinfo=timezone.utc),
        end_at=datetime(2026, 5, 15, 12, 0, tzinfo=timezone.utc),
        status="paid",
        total_amount=Decimal("80.00"),
        payable_amount=Decimal("80.00"),
    )

    ensure_reschedulable(pending_order)
    ensure_reschedulable(paid_order)
