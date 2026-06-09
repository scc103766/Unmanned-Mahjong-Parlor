from decimal import Decimal

import pytest

from app.core.errors import AppError
from app.main import create_app
from app.modules.coupons.models import Coupon
from app.modules.coupons.service import lock_coupon, refund_coupon, return_coupon, use_coupon
from app.modules.group_buy.models import GroupBuyCode
from app.modules.group_buy.service import (
    lock_group_buy_code,
    refund_group_buy_code,
    return_group_buy_code,
    use_group_buy_code,
)
from app.modules.payments.models import Payment
from app.modules.payments.schemas import (
    MockRefundCallbackRequest,
    MockWechatCallbackRequest,
    RefundCreateRequest,
    WechatPrepayRequest,
)
from app.modules.payments.service import generate_refund_no, payment_deductions
from app.modules.payments.signing import sign_callback_payload, verify_callback_signature
from app.modules.wallet.schemas import WalletRechargeRequest


def test_m4_payment_routes_are_registered() -> None:
    route_paths = {route.path for route in create_app().routes}

    assert "/api/v1/payments/wechat/prepay" in route_paths
    assert "/api/v1/payments/wechat/callback" in route_paths
    assert "/api/v1/payments/refunds/callback" in route_paths
    assert "/api/v1/payments/{payment_id}" in route_paths
    assert "/api/v1/payments/{payment_id}/close" in route_paths
    assert "/api/v1/payments/{payment_id}/refund" in route_paths
    assert "/api/v1/wallets/me" in route_paths
    assert "/api/v1/wallets/recharge" in route_paths
    assert "/api/v1/coupon-templates" in route_paths
    assert "/api/v1/coupons/claim" in route_paths
    assert "/api/v1/group-buy/verify" in route_paths


def test_wechat_prepay_request_accepts_payment_deductions() -> None:
    payload = WechatPrepayRequest(
        order_id="order_1",
        idempotency_key="idem_1",
        coupon_id="coupon_1",
        group_buy_code_id="group_buy_1",
        wallet_amount=Decimal("12.50"),
    )

    assert payload.order_id == "order_1"
    assert payload.idempotency_key == "idem_1"
    assert payload.coupon_id == "coupon_1"
    assert payload.group_buy_code_id == "group_buy_1"
    assert payload.wallet_amount == Decimal("12.50")


def test_payment_deductions_reads_provider_payload() -> None:
    payment = Payment(
        tenant_id="tenant_1",
        order_id="order_1",
        channel="mock_wechat",
        amount=Decimal("25.00"),
        status="paying",
        provider_payload={
            "deductions": {
                "coupon_id": "coupon_1",
                "coupon_amount": "10.00",
                "wallet_amount": "15.00",
            }
        },
    )

    deductions = payment_deductions(payment)

    assert deductions["coupon_id"] == "coupon_1"
    assert deductions["coupon_amount"] == "10.00"
    assert deductions["wallet_amount"] == "15.00"


def test_refund_request_amount_is_decimal() -> None:
    payload = RefundCreateRequest(
        amount=Decimal("10.50"),
        idempotency_key="refund_idem_1",
        reason="customer request",
    )

    assert payload.amount == Decimal("10.50")
    assert payload.idempotency_key == "refund_idem_1"
    assert payload.reason == "customer request"


def test_refund_request_allows_zero_for_deduction_only_refund() -> None:
    payload = RefundCreateRequest(amount=Decimal("0.00"), reason="deduction return")

    assert payload.amount == Decimal("0.00")


def test_refund_no_prefix() -> None:
    assert generate_refund_no().startswith("RF")


def test_mock_wechat_callback_signature_round_trip() -> None:
    payload = MockWechatCallbackRequest(
        payment_id="payment_1",
        transaction_id="tx_1",
        provider_event_id="evt_1",
        timestamp=1_800_000_000,
        nonce="nonce_1",
    ).model_dump(mode="json")
    payload["signature"] = sign_callback_payload(payload, secret="secret")

    verify_callback_signature(
        payload,
        secret="secret",
        required=True,
        tolerance_seconds=300,
        now=1_800_000_010,
    )


def test_mock_refund_callback_signature_rejects_tampering() -> None:
    payload = MockRefundCallbackRequest(
        refund_id="refund_1",
        provider_refund_id="provider_refund_1",
        provider_event_id="evt_1",
        timestamp=1_800_000_000,
        nonce="nonce_1",
    ).model_dump(mode="json")
    payload["signature"] = sign_callback_payload(payload, secret="secret")
    payload["provider_event_id"] = "evt_tampered"

    with pytest.raises(AppError) as exc_info:
        verify_callback_signature(
            payload,
            secret="secret",
            required=True,
            tolerance_seconds=300,
            now=1_800_000_010,
        )

    assert exc_info.value.code == "CALLBACK_SIGNATURE_INVALID"


def test_wallet_recharge_request_defaults_gift_amount() -> None:
    payload = WalletRechargeRequest(amount=Decimal("100.00"))

    assert payload.gift_amount == Decimal("0.00")


def test_coupon_state_flow() -> None:
    coupon = Coupon(
        tenant_id="tenant_1",
        template_id="template_1",
        user_id="user_1",
        status="available",
        value=Decimal("10.00"),
        threshold=Decimal("50.00"),
    )

    lock_coupon(coupon, tenant_id="tenant_1", user_id="user_1", order_id="order_1")
    assert coupon.status == "locked"
    use_coupon(coupon, tenant_id="tenant_1", user_id="user_1", order_id="order_1")
    assert coupon.status == "used"


def test_coupon_return_flow() -> None:
    coupon = Coupon(
        tenant_id="tenant_1",
        template_id="template_1",
        user_id="user_1",
        status="locked",
        value=Decimal("10.00"),
        threshold=Decimal("50.00"),
        locked_order_id="order_1",
    )

    return_coupon(coupon, tenant_id="tenant_1", user_id="user_1")

    assert coupon.status == "available"
    assert coupon.locked_order_id is None


def test_coupon_refund_flow() -> None:
    coupon = Coupon(
        tenant_id="tenant_1",
        template_id="template_1",
        user_id="user_1",
        status="used",
        value=Decimal("10.00"),
        threshold=Decimal("50.00"),
        locked_order_id="order_1",
        used_order_id="order_1",
    )

    refund_coupon(coupon, tenant_id="tenant_1", user_id="user_1", order_id="order_1")

    assert coupon.status == "available"
    assert coupon.locked_order_id is None
    assert coupon.used_order_id is None


def test_group_buy_code_state_flow() -> None:
    row = GroupBuyCode(
        tenant_id="tenant_1",
        store_id="store_1",
        code="GB001",
        amount=Decimal("88.00"),
        status="available",
    )

    lock_group_buy_code(row, order_id="order_1")
    assert row.status == "locked"
    use_group_buy_code(row, order_id="order_1")
    assert row.status == "used"


def test_group_buy_code_return_flow() -> None:
    row = GroupBuyCode(
        tenant_id="tenant_1",
        store_id="store_1",
        code="GB001",
        amount=Decimal("88.00"),
        status="locked",
        locked_order_id="order_1",
    )

    return_group_buy_code(row)

    assert row.status == "available"
    assert row.locked_order_id is None


def test_group_buy_code_refund_flow() -> None:
    row = GroupBuyCode(
        tenant_id="tenant_1",
        store_id="store_1",
        code="GB001",
        amount=Decimal("88.00"),
        status="used",
        locked_order_id="order_1",
        verified_order_id="order_1",
    )

    refund_group_buy_code(row, order_id="order_1")

    assert row.status == "available"
    assert row.locked_order_id is None
    assert row.verified_order_id is None
