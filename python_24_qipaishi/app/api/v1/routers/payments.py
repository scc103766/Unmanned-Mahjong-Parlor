from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import (
    CurrentPrincipal,
    get_app_settings,
    get_db_session,
    require_roles,
)
from app.core.config import Settings
from app.core.errors import AppError
from app.core.responses import ok
from app.modules.audit.service import write_audit_log
from app.modules.orders.service import load_order_for_principal
from app.modules.payments.models import Payment
from app.modules.payments.schemas import (
    MockRefundCallbackRequest,
    MockWechatCallbackRequest,
    PaymentResponse,
    RefundCreateRequest,
    RefundResponse,
    WechatPrepayRequest,
)
from app.modules.payments.service import (
    close_payment,
    confirm_mock_refund,
    confirm_mock_wechat_payment,
    create_mock_wechat_payment,
    create_refund,
)
from app.modules.payments.signing import verify_callback_signature

router = APIRouter()


def _tenant_id(principal: CurrentPrincipal) -> str:
    if principal.tenant_id is None:
        raise AppError(
            "TENANT_REQUIRED",
            "A tenant-scoped identity is required.",
            status.HTTP_403_FORBIDDEN,
        )
    return principal.tenant_id


def _can_manage_payments(principal: CurrentPrincipal) -> bool:
    return principal.has_any_role(["platform_admin", "merchant_admin", "clerk", "support"])


async def _load_payment(
    session: AsyncSession,
    *,
    payment_id: str,
    tenant_id: str,
) -> Payment:
    payment = await session.get(Payment, payment_id)
    if payment is None:
        raise AppError("PAYMENT_NOT_FOUND", "Payment was not found.", status.HTTP_404_NOT_FOUND)
    if payment.tenant_id != tenant_id:
        raise AppError(
            "FORBIDDEN",
            "Cannot access another tenant payment.",
            status.HTTP_403_FORBIDDEN,
        )
    return payment


@router.post("/wechat/prepay")
async def wechat_prepay(
    payload: WechatPrepayRequest,
    request: Request,
    principal: CurrentPrincipal = Depends(
        require_roles("merchant_admin", "clerk", "customer", "support")
    ),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, object]:
    tenant_id = _tenant_id(principal)
    order = await load_order_for_principal(
        session,
        order_id=payload.order_id,
        tenant_id=tenant_id,
        user_id=principal.user_id,
        can_manage_tenant=_can_manage_payments(principal),
    )
    payment = await create_mock_wechat_payment(
        session,
        order=order,
        idempotency_key=payload.idempotency_key,
        coupon_id=payload.coupon_id,
        group_buy_code_id=payload.group_buy_code_id,
        wallet_amount=payload.wallet_amount,
    )
    await write_audit_log(
        session,
        tenant_id=tenant_id,
        actor_id=principal.user_id,
        action="payment.wechat_prepay",
        target_type="payment",
        target_id=payment.id,
        request_id=getattr(request.state, "request_id", None),
        ip_address=request.client.host if request.client else None,
        payload=payload.model_dump(),
    )
    await session.commit()
    return ok(PaymentResponse.model_validate(payment).model_dump(mode="json"), request)


@router.post("/wechat/callback")
async def wechat_callback(
    payload: MockWechatCallbackRequest,
    request: Request,
    settings: Settings = Depends(get_app_settings),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, object]:
    verify_callback_signature(
        payload.model_dump(mode="json"),
        secret=settings.payment_callback_secret,
        required=settings.payment_callback_signature_required,
        tolerance_seconds=settings.payment_callback_tolerance_seconds,
    )
    payment = await session.get(Payment, payload.payment_id)
    if payment is None:
        raise AppError("PAYMENT_NOT_FOUND", "Payment was not found.", status.HTTP_404_NOT_FOUND)
    payment = await confirm_mock_wechat_payment(
        session,
        payment=payment,
        transaction_id=payload.transaction_id,
        provider_event_id=payload.provider_event_id,
    )
    await write_audit_log(
        session,
        tenant_id=payment.tenant_id,
        action="payment.wechat_callback",
        target_type="payment",
        target_id=payment.id,
        request_id=getattr(request.state, "request_id", None),
        ip_address=request.client.host if request.client else None,
        payload=payload.model_dump(),
    )
    await session.commit()
    return ok(PaymentResponse.model_validate(payment).model_dump(mode="json"), request)


@router.get("/{payment_id}")
async def get_payment(
    payment_id: str,
    request: Request,
    principal: CurrentPrincipal = Depends(
        require_roles("merchant_admin", "clerk", "customer", "support")
    ),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, object]:
    payment = await _load_payment(session, payment_id=payment_id, tenant_id=_tenant_id(principal))
    return ok(PaymentResponse.model_validate(payment).model_dump(mode="json"), request)


@router.post("/{payment_id}/close")
async def close(
    payment_id: str,
    request: Request,
    principal: CurrentPrincipal = Depends(require_roles("merchant_admin", "clerk", "support")),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, object]:
    payment = await _load_payment(session, payment_id=payment_id, tenant_id=_tenant_id(principal))
    payment = await close_payment(session, payment=payment, reason="manual close")
    await write_audit_log(
        session,
        tenant_id=payment.tenant_id,
        actor_id=principal.user_id,
        action="payment.close",
        target_type="payment",
        target_id=payment.id,
        request_id=getattr(request.state, "request_id", None),
        ip_address=request.client.host if request.client else None,
        payload={},
    )
    await session.commit()
    return ok(PaymentResponse.model_validate(payment).model_dump(mode="json"), request)


@router.post("/{payment_id}/refund")
async def refund(
    payment_id: str,
    payload: RefundCreateRequest,
    request: Request,
    principal: CurrentPrincipal = Depends(require_roles("merchant_admin", "clerk", "support")),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, object]:
    payment = await _load_payment(session, payment_id=payment_id, tenant_id=_tenant_id(principal))
    refund_row = await create_refund(
        session,
        payment=payment,
        amount=payload.amount,
        idempotency_key=payload.idempotency_key,
        reason=payload.reason,
    )
    await write_audit_log(
        session,
        tenant_id=payment.tenant_id,
        actor_id=principal.user_id,
        action="payment.refund.create",
        target_type="refund",
        target_id=refund_row.id,
        request_id=getattr(request.state, "request_id", None),
        ip_address=request.client.host if request.client else None,
        payload=payload.model_dump(mode="json"),
    )
    await session.commit()
    return ok(RefundResponse.model_validate(refund_row).model_dump(mode="json"), request)


@router.post("/refunds/callback")
async def refund_callback(
    payload: MockRefundCallbackRequest,
    request: Request,
    settings: Settings = Depends(get_app_settings),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, object]:
    from app.modules.payments.models import Refund

    verify_callback_signature(
        payload.model_dump(mode="json"),
        secret=settings.payment_callback_secret,
        required=settings.payment_callback_signature_required,
        tolerance_seconds=settings.payment_callback_tolerance_seconds,
    )
    refund_row = await session.get(Refund, payload.refund_id)
    if refund_row is None:
        raise AppError("REFUND_NOT_FOUND", "Refund was not found.", status.HTTP_404_NOT_FOUND)
    refund_row = await confirm_mock_refund(
        session,
        refund=refund_row,
        provider_refund_id=payload.provider_refund_id,
        provider_event_id=payload.provider_event_id,
    )
    await write_audit_log(
        session,
        tenant_id=refund_row.tenant_id,
        action="payment.refund.callback",
        target_type="refund",
        target_id=refund_row.id,
        request_id=getattr(request.state, "request_id", None),
        ip_address=request.client.host if request.client else None,
        payload=payload.model_dump(),
    )
    await session.commit()
    return ok(RefundResponse.model_validate(refund_row).model_dump(mode="json"), request)
