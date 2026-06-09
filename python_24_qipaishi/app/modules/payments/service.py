from decimal import Decimal
from typing import Any, Optional
from uuid import uuid4

from fastapi import status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError
from app.modules.availability.service import utc_now
from app.modules.coupons.models import Coupon
from app.modules.coupons.service import lock_coupon, refund_coupon, return_coupon, use_coupon
from app.modules.group_buy.models import GroupBuyCode
from app.modules.group_buy.service import (
    lock_group_buy_code,
    refund_group_buy_code,
    return_group_buy_code,
    use_group_buy_code,
)
from app.modules.orders.models import Order
from app.modules.orders.service import cancel_order, transition_order_to_paid
from app.modules.payments.models import Payment, PaymentEvent, Refund
from app.modules.wallet.service import credit_wallet_split, debit_wallet


def generate_refund_no() -> str:
    return f"RF{utc_now().strftime('%Y%m%d%H%M%S')}{uuid4().hex[:8].upper()}"


async def create_mock_wechat_payment(
    session: AsyncSession,
    *,
    order: Order,
    idempotency_key: Optional[str],
    coupon_id: Optional[str] = None,
    group_buy_code_id: Optional[str] = None,
    wallet_amount: Decimal = Decimal("0.00"),
) -> Payment:
    if order.status != "pending_payment":
        raise AppError(
            "ORDER_STATE_INVALID",
            "Only pending payment orders can create payment.",
            status.HTTP_409_CONFLICT,
        )
    if idempotency_key:
        existing = await session.scalar(
            select(Payment).where(
                Payment.tenant_id == order.tenant_id,
                Payment.idempotency_key == idempotency_key,
            )
        )
        if existing is not None:
            return existing

    original_amount = Decimal(order.payable_amount)
    remaining_amount = original_amount
    deductions: dict[str, Any] = {
        "coupon_id": None,
        "coupon_amount": "0.00",
        "group_buy_code_id": None,
        "group_buy_amount": "0.00",
        "wallet_amount": "0.00",
        "wallet_cash_amount": "0.00",
        "wallet_gift_amount": "0.00",
        "coupon_returned": False,
        "group_buy_returned": False,
    }

    if group_buy_code_id is not None:
        if remaining_amount <= Decimal("0"):
            raise AppError(
                "DEDUCTION_NOT_APPLICABLE",
                "No payable amount remains for group-buy deduction.",
                status.HTTP_400_BAD_REQUEST,
            )
        group_buy_code = await session.get(GroupBuyCode, group_buy_code_id)
        if (
            group_buy_code is None
            or group_buy_code.tenant_id != order.tenant_id
            or group_buy_code.store_id != order.store_id
        ):
            raise AppError(
                "GROUP_BUY_CODE_NOT_FOUND",
                "Group-buy code was not found.",
                status.HTTP_404_NOT_FOUND,
            )
        lock_group_buy_code(group_buy_code, order_id=order.id)
        group_buy_amount = min(Decimal(group_buy_code.amount), remaining_amount)
        remaining_amount -= group_buy_amount
        deductions["group_buy_code_id"] = group_buy_code.id
        deductions["group_buy_amount"] = str(group_buy_amount)

    if coupon_id is not None:
        if remaining_amount <= Decimal("0"):
            raise AppError(
                "DEDUCTION_NOT_APPLICABLE",
                "No payable amount remains for coupon deduction.",
                status.HTTP_400_BAD_REQUEST,
            )
        coupon = await session.get(Coupon, coupon_id)
        if coupon is None:
            raise AppError("COUPON_NOT_FOUND", "Coupon was not found.", status.HTTP_404_NOT_FOUND)
        if original_amount < Decimal(coupon.threshold):
            raise AppError(
                "COUPON_THRESHOLD_NOT_MET",
                "Order amount does not meet coupon threshold.",
                status.HTTP_409_CONFLICT,
            )
        lock_coupon(coupon, tenant_id=order.tenant_id, user_id=order.user_id, order_id=order.id)
        coupon_amount = min(Decimal(coupon.value), remaining_amount)
        remaining_amount -= coupon_amount
        deductions["coupon_id"] = coupon.id
        deductions["coupon_amount"] = str(coupon_amount)

    if wallet_amount > Decimal("0"):
        if wallet_amount > remaining_amount:
            raise AppError(
                "WALLET_AMOUNT_EXCEEDED",
                "Wallet amount exceeds remaining payable amount.",
                status.HTTP_400_BAD_REQUEST,
            )
        wallet_split = await debit_wallet(
            session,
            tenant_id=order.tenant_id,
            user_id=order.user_id,
            amount=wallet_amount,
            biz_type="order_pay",
            biz_id=order.id,
            remark="order payment deduction",
        )
        remaining_amount -= wallet_amount
        deductions["wallet_amount"] = str(wallet_amount)
        deductions["wallet_cash_amount"] = str(wallet_split["cash_amount"])
        deductions["wallet_gift_amount"] = str(wallet_split["gift_amount"])

    provider_payload = {
        "provider": "mock_wechat",
        "prepay_id": f"mock_prepay_{uuid4().hex}",
        "order_no": order.order_no,
        "original_amount": str(original_amount),
        "wechat_amount": str(remaining_amount),
        "deductions": deductions,
    }
    payment = Payment(
        tenant_id=order.tenant_id,
        order_id=order.id,
        channel="mock_wechat" if remaining_amount > Decimal("0") else "wallet",
        amount=remaining_amount,
        status="paying" if remaining_amount > Decimal("0") else "paid",
        idempotency_key=idempotency_key,
        provider_payload=provider_payload,
        paid_at=utc_now() if remaining_amount == Decimal("0") else None,
    )
    session.add(payment)
    await session.flush()
    if remaining_amount == Decimal("0"):
        await transition_order_to_paid(session, order)
        await settle_payment_deductions(session, payment=payment, order=order)
        session.add(
            PaymentEvent(
                tenant_id=payment.tenant_id,
                payment_id=payment.id,
                channel=payment.channel,
                event_type="payment.paid",
                provider_event_id=f"wallet_paid_{payment.id}",
                status="processed",
                payload={"payment_id": payment.id},
                processed_at=utc_now(),
            )
        )
        await session.flush()
    return payment


def payment_deductions(payment: Payment) -> dict[str, Any]:
    payload = payment.provider_payload or {}
    deductions = payload.get("deductions")
    if isinstance(deductions, dict):
        return deductions
    return {}


def deduction_amount(deductions: dict[str, Any], key: str) -> Decimal:
    return Decimal(str(deductions.get(key) or "0.00"))


def refundable_deduction_amount(payment: Payment) -> Decimal:
    deductions = payment_deductions(payment)
    amount = deduction_amount(deductions, "wallet_cash_amount")
    amount += deduction_amount(deductions, "wallet_gift_amount")
    if deductions.get("coupon_returned") is not True:
        amount += deduction_amount(deductions, "coupon_amount")
    if deductions.get("group_buy_returned") is not True:
        amount += deduction_amount(deductions, "group_buy_amount")
    return amount


async def settle_payment_deductions(
    session: AsyncSession,
    *,
    payment: Payment,
    order: Order,
) -> None:
    deductions = payment_deductions(payment)
    coupon_id = deductions.get("coupon_id")
    if isinstance(coupon_id, str):
        coupon = await session.get(Coupon, coupon_id)
        if coupon is not None and coupon.status == "locked":
            use_coupon(coupon, tenant_id=order.tenant_id, user_id=order.user_id, order_id=order.id)

    group_buy_code_id = deductions.get("group_buy_code_id")
    if isinstance(group_buy_code_id, str):
        group_buy_code = await session.get(GroupBuyCode, group_buy_code_id)
        if group_buy_code is not None and group_buy_code.status == "locked":
            use_group_buy_code(group_buy_code, order_id=order.id)


async def return_payment_deductions(
    session: AsyncSession,
    *,
    payment: Payment,
    order: Order,
) -> None:
    deductions = payment_deductions(payment)
    changed = False
    coupon_id = deductions.get("coupon_id")
    if isinstance(coupon_id, str):
        coupon = await session.get(Coupon, coupon_id)
        if coupon is not None and coupon.status == "locked":
            return_coupon(coupon, tenant_id=order.tenant_id, user_id=order.user_id)
            deductions["coupon_returned"] = True
            changed = True

    group_buy_code_id = deductions.get("group_buy_code_id")
    if isinstance(group_buy_code_id, str):
        group_buy_code = await session.get(GroupBuyCode, group_buy_code_id)
        if group_buy_code is not None and group_buy_code.status == "locked":
            return_group_buy_code(group_buy_code)
            deductions["group_buy_returned"] = True
            changed = True

    wallet_cash_amount = Decimal(str(deductions.get("wallet_cash_amount") or "0.00"))
    wallet_gift_amount = Decimal(str(deductions.get("wallet_gift_amount") or "0.00"))
    if wallet_cash_amount or wallet_gift_amount:
        await credit_wallet_split(
            session,
            tenant_id=order.tenant_id,
            user_id=order.user_id,
            cash_amount=wallet_cash_amount,
            gift_amount=wallet_gift_amount,
            biz_type="order_pay_return",
            biz_id=order.id,
            remark="payment closed return",
        )
        deductions["wallet_cash_amount"] = "0.00"
        deductions["wallet_gift_amount"] = "0.00"
        deductions["wallet_amount"] = "0.00"
        changed = True
    if changed:
        payment.provider_payload = {**(payment.provider_payload or {}), "deductions": deductions}


async def refund_payment_deductions(
    session: AsyncSession,
    *,
    payment: Payment,
    order: Order,
) -> None:
    deductions = payment_deductions(payment)
    changed = False
    coupon_id = deductions.get("coupon_id")
    if isinstance(coupon_id, str) and deductions.get("coupon_returned") is not True:
        coupon = await session.get(Coupon, coupon_id)
        if coupon is not None and coupon.status == "used":
            refund_coupon(
                coupon,
                tenant_id=order.tenant_id,
                user_id=order.user_id,
                order_id=order.id,
            )
        deductions["coupon_returned"] = True
        changed = True

    group_buy_code_id = deductions.get("group_buy_code_id")
    if isinstance(group_buy_code_id, str) and deductions.get("group_buy_returned") is not True:
        group_buy_code = await session.get(GroupBuyCode, group_buy_code_id)
        if group_buy_code is not None and group_buy_code.status == "used":
            refund_group_buy_code(group_buy_code, order_id=order.id)
        deductions["group_buy_returned"] = True
        changed = True

    wallet_cash_amount = deduction_amount(deductions, "wallet_cash_amount")
    wallet_gift_amount = deduction_amount(deductions, "wallet_gift_amount")
    if wallet_cash_amount or wallet_gift_amount:
        await credit_wallet_split(
            session,
            tenant_id=order.tenant_id,
            user_id=order.user_id,
            cash_amount=wallet_cash_amount,
            gift_amount=wallet_gift_amount,
            biz_type="order_refund_return",
            biz_id=order.id,
            remark="payment refunded return",
        )
        deductions["wallet_cash_amount"] = "0.00"
        deductions["wallet_gift_amount"] = "0.00"
        deductions["wallet_amount"] = "0.00"
        changed = True

    if changed:
        payment.provider_payload = {**(payment.provider_payload or {}), "deductions": deductions}


async def confirm_mock_wechat_payment(
    session: AsyncSession,
    *,
    payment: Payment,
    transaction_id: str,
    provider_event_id: str,
) -> Payment:
    existing_event = await session.scalar(
        select(PaymentEvent).where(
            PaymentEvent.channel == payment.channel,
            PaymentEvent.provider_event_id == provider_event_id,
        )
    )
    if existing_event is not None:
        return payment

    order = await session.get(Order, payment.order_id)
    if order is None:
        raise AppError("ORDER_NOT_FOUND", "Order was not found.", status.HTTP_404_NOT_FOUND)

    if payment.status != "paid":
        await transition_order_to_paid(session, order)
        payment.status = "paid"
        payment.transaction_id = transaction_id
        payment.paid_at = utc_now()
        await settle_payment_deductions(session, payment=payment, order=order)

    session.add(
        PaymentEvent(
            tenant_id=payment.tenant_id,
            payment_id=payment.id,
            channel=payment.channel,
            event_type="payment.paid",
            provider_event_id=provider_event_id,
            status="processed",
            payload={"transaction_id": transaction_id, "payment_id": payment.id},
            processed_at=utc_now(),
        )
    )
    await session.flush()
    return payment


async def close_payment(
    session: AsyncSession,
    *,
    payment: Payment,
    reason: Optional[str],
) -> Payment:
    if payment.status == "paid":
        raise AppError(
            "PAYMENT_STATE_INVALID",
            "Paid payment cannot be closed.",
            status.HTTP_409_CONFLICT,
        )
    if payment.status == "closed":
        return payment

    order = await session.get(Order, payment.order_id)
    if order is not None and order.status == "pending_payment":
        await return_payment_deductions(session, payment=payment, order=order)
        await cancel_order(session, order, reason=reason or "payment closed")
    payment.status = "closed"
    payment.closed_at = utc_now()
    payment.provider_payload = {**(payment.provider_payload or {}), "close_reason": reason}
    await session.flush()
    return payment


async def create_refund(
    session: AsyncSession,
    *,
    payment: Payment,
    amount: Decimal,
    idempotency_key: Optional[str],
    reason: Optional[str],
) -> Refund:
    if payment.status != "paid":
        raise AppError(
            "PAYMENT_STATE_INVALID",
            "Only paid payments can be refunded.",
            status.HTTP_409_CONFLICT,
        )
    if idempotency_key:
        existing = await session.scalar(
            select(Refund).where(
                Refund.tenant_id == payment.tenant_id,
                Refund.idempotency_key == idempotency_key,
            )
        )
        if existing is not None:
            return existing

    refunded_amount = await session.scalar(
        select(func.coalesce(func.sum(Refund.amount), 0)).where(
            Refund.payment_id == payment.id,
            Refund.status.in_(["created", "refunded"]),
        )
    )
    paid_refund_amount = refunded_amount or Decimal("0")
    payment_amount = Decimal(payment.amount)
    if payment_amount > Decimal("0") and amount <= Decimal("0"):
        raise AppError(
            "REFUND_AMOUNT_INVALID",
            "Refund amount must be greater than zero for gateway payments.",
            status.HTTP_400_BAD_REQUEST,
        )
    if payment_amount == Decimal("0") and (
        amount != Decimal("0") or refundable_deduction_amount(payment) <= Decimal("0")
    ):
        raise AppError(
            "REFUND_AMOUNT_INVALID",
            "Zero-amount refunds are only allowed when refundable deductions exist.",
            status.HTTP_400_BAD_REQUEST,
        )
    if Decimal(paid_refund_amount) + amount > payment_amount:
        raise AppError(
            "REFUND_AMOUNT_EXCEEDED",
            "Refund amount exceeds paid amount.",
            status.HTTP_400_BAD_REQUEST,
        )

    refund = Refund(
        tenant_id=payment.tenant_id,
        payment_id=payment.id,
        order_id=payment.order_id,
        refund_no=generate_refund_no(),
        amount=amount,
        reason=reason,
        status="created",
        idempotency_key=idempotency_key,
        provider_payload={
            "provider": "mock_wechat",
            "idempotency_key": idempotency_key,
        },
    )
    session.add(refund)
    await session.flush()
    return refund


async def confirm_mock_refund(
    session: AsyncSession,
    *,
    refund: Refund,
    provider_refund_id: str,
    provider_event_id: str,
) -> Refund:
    existing_event = await session.scalar(
        select(PaymentEvent).where(
            PaymentEvent.channel == "mock_wechat",
            PaymentEvent.provider_event_id == provider_event_id,
        )
    )
    if existing_event is not None:
        return refund

    if refund.status != "refunded":
        refund.status = "refunded"
        refund.provider_refund_id = provider_refund_id
        refund.refunded_at = utc_now()
        await session.flush()

        payment = await session.get(Payment, refund.payment_id)
        if payment is None:
            raise AppError("PAYMENT_NOT_FOUND", "Payment was not found.", status.HTTP_404_NOT_FOUND)
        refunded_amount = await session.scalar(
            select(func.coalesce(func.sum(Refund.amount), 0)).where(
                Refund.payment_id == payment.id,
                Refund.status == "refunded",
            )
        )
        full_gateway_refund = Decimal(refunded_amount or 0) >= Decimal(payment.amount)
        if full_gateway_refund:
            order = await session.get(Order, payment.order_id)
            if order is not None:
                await refund_payment_deductions(session, payment=payment, order=order)
                if order.status == "paid":
                    await cancel_order(session, order, reason="payment refunded")
            payment.status = "refunded"

    session.add(
        PaymentEvent(
            tenant_id=refund.tenant_id,
            payment_id=refund.payment_id,
            channel="mock_wechat",
            event_type="refund.refunded",
            provider_event_id=provider_event_id,
            status="processed",
            payload={"provider_refund_id": provider_refund_id, "refund_id": refund.id},
            processed_at=utc_now(),
        )
    )
    await session.flush()
    return refund
