from fastapi import status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError
from app.modules.coupons.models import Coupon, CouponTemplate


async def claim_coupon(
    session: AsyncSession,
    *,
    tenant_id: str,
    user_id: str,
    template_id: str,
) -> Coupon:
    return await issue_coupon_from_template(
        session,
        tenant_id=tenant_id,
        user_id=user_id,
        template_id=template_id,
        enforce_user_limit=True,
    )


async def issue_coupon_from_template(
    session: AsyncSession,
    *,
    tenant_id: str,
    user_id: str,
    template_id: str,
    enforce_user_limit: bool,
) -> Coupon:
    template = await session.get(CouponTemplate, template_id)
    if template is None or template.tenant_id != tenant_id:
        raise AppError(
            "COUPON_TEMPLATE_NOT_FOUND",
            "Coupon template was not found.",
            status.HTTP_404_NOT_FOUND,
        )
    if template.status != "active":
        raise AppError(
            "COUPON_TEMPLATE_DISABLED",
            "Coupon template is not active.",
            status.HTTP_409_CONFLICT,
        )
    if template.total_count and template.claimed_count >= template.total_count:
        raise AppError(
            "COUPON_TEMPLATE_EMPTY",
            "Coupon template has no remaining coupons.",
            status.HTTP_409_CONFLICT,
        )

    if enforce_user_limit:
        claimed_by_user = await session.scalar(
            select(func.count(Coupon.id)).where(
                Coupon.tenant_id == tenant_id,
                Coupon.template_id == template_id,
                Coupon.user_id == user_id,
            )
        )
        if int(claimed_by_user or 0) >= template.per_user_limit:
            raise AppError(
                "COUPON_CLAIM_LIMIT",
                "Coupon claim limit reached.",
                status.HTTP_409_CONFLICT,
            )

    coupon = Coupon(
        tenant_id=tenant_id,
        template_id=template.id,
        user_id=user_id,
        status="available",
        value=template.value,
        threshold=template.threshold,
        valid_from=template.valid_from,
        valid_to=template.valid_to,
    )
    template.claimed_count += 1
    session.add(coupon)
    await session.flush()
    return coupon


def lock_coupon(coupon: Coupon, *, tenant_id: str, user_id: str, order_id: str) -> Coupon:
    if coupon.tenant_id != tenant_id or coupon.user_id != user_id:
        raise AppError("COUPON_NOT_FOUND", "Coupon was not found.", status.HTTP_404_NOT_FOUND)
    if coupon.status != "available":
        raise AppError(
            "COUPON_STATE_INVALID",
            "Only available coupons can be locked.",
            status.HTTP_409_CONFLICT,
        )
    coupon.status = "locked"
    coupon.locked_order_id = order_id
    return coupon


def use_coupon(coupon: Coupon, *, tenant_id: str, user_id: str, order_id: str) -> Coupon:
    if coupon.tenant_id != tenant_id or coupon.user_id != user_id:
        raise AppError("COUPON_NOT_FOUND", "Coupon was not found.", status.HTTP_404_NOT_FOUND)
    if coupon.status != "locked" or coupon.locked_order_id != order_id:
        raise AppError(
            "COUPON_STATE_INVALID",
            "Coupon is not locked for this order.",
            status.HTTP_409_CONFLICT,
        )
    coupon.status = "used"
    coupon.used_order_id = order_id
    return coupon


def return_coupon(coupon: Coupon, *, tenant_id: str, user_id: str) -> Coupon:
    if coupon.tenant_id != tenant_id or coupon.user_id != user_id:
        raise AppError("COUPON_NOT_FOUND", "Coupon was not found.", status.HTTP_404_NOT_FOUND)
    if coupon.status != "locked":
        raise AppError(
            "COUPON_STATE_INVALID",
            "Only locked coupons can be returned.",
            status.HTTP_409_CONFLICT,
        )
    coupon.status = "available"
    coupon.locked_order_id = None
    return coupon


def refund_coupon(coupon: Coupon, *, tenant_id: str, user_id: str, order_id: str) -> Coupon:
    if coupon.tenant_id != tenant_id or coupon.user_id != user_id:
        raise AppError("COUPON_NOT_FOUND", "Coupon was not found.", status.HTTP_404_NOT_FOUND)
    if coupon.status != "used" or coupon.used_order_id != order_id:
        raise AppError(
            "COUPON_STATE_INVALID",
            "Only coupons used by this order can be refunded.",
            status.HTTP_409_CONFLICT,
        )
    coupon.status = "available"
    coupon.locked_order_id = None
    coupon.used_order_id = None
    return coupon
