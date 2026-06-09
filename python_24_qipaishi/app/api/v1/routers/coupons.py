from fastapi import APIRouter, Depends, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import CurrentPrincipal, get_db_session, require_roles
from app.core.errors import AppError
from app.core.responses import ok
from app.modules.audit.service import write_audit_log
from app.modules.coupons.models import Coupon, CouponTemplate
from app.modules.coupons.schemas import (
    CouponClaimRequest,
    CouponIssueRequest,
    CouponOrderRequest,
    CouponResponse,
    CouponTemplateCreateRequest,
    CouponTemplateResponse,
)
from app.modules.coupons.service import (
    claim_coupon,
    issue_coupon_from_template,
    lock_coupon,
    return_coupon,
    use_coupon,
)
from app.modules.users.models import User

templates_router = APIRouter()
coupons_router = APIRouter()


def _tenant_id(principal: CurrentPrincipal) -> str:
    if principal.tenant_id is None:
        raise AppError(
            "TENANT_REQUIRED",
            "A tenant-scoped identity is required.",
            status.HTTP_403_FORBIDDEN,
        )
    return principal.tenant_id


@templates_router.get("")
async def list_templates(
    request: Request,
    principal: CurrentPrincipal = Depends(
        require_roles("merchant_admin", "clerk", "customer", "support")
    ),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, object]:
    rows = (
        await session.scalars(
            select(CouponTemplate)
            .where(CouponTemplate.tenant_id == _tenant_id(principal))
            .order_by(CouponTemplate.created_at.desc())
        )
    ).all()
    return ok(
        [CouponTemplateResponse.model_validate(row).model_dump(mode="json") for row in rows],
        request,
    )


@templates_router.post("")
async def create_template(
    payload: CouponTemplateCreateRequest,
    request: Request,
    principal: CurrentPrincipal = Depends(require_roles("merchant_admin", "clerk")),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, object]:
    template = CouponTemplate(tenant_id=_tenant_id(principal), **payload.model_dump())
    session.add(template)
    await session.flush()
    await write_audit_log(
        session,
        tenant_id=template.tenant_id,
        actor_id=principal.user_id,
        action="coupon_template.create",
        target_type="coupon_template",
        target_id=template.id,
        request_id=getattr(request.state, "request_id", None),
        ip_address=request.client.host if request.client else None,
        payload=payload.model_dump(mode="json"),
    )
    await session.commit()
    return ok(CouponTemplateResponse.model_validate(template).model_dump(mode="json"), request)


@coupons_router.get("/me")
async def my_coupons(
    request: Request,
    principal: CurrentPrincipal = Depends(require_roles("customer")),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, object]:
    rows = (
        await session.scalars(
            select(Coupon)
            .where(Coupon.tenant_id == _tenant_id(principal), Coupon.user_id == principal.user_id)
            .order_by(Coupon.created_at.desc())
        )
    ).all()
    return ok([CouponResponse.model_validate(row).model_dump(mode="json") for row in rows], request)


@coupons_router.post("/claim")
async def claim(
    payload: CouponClaimRequest,
    request: Request,
    principal: CurrentPrincipal = Depends(require_roles("customer")),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, object]:
    coupon = await claim_coupon(
        session,
        tenant_id=_tenant_id(principal),
        user_id=principal.user_id,
        template_id=payload.template_id,
    )
    await write_audit_log(
        session,
        tenant_id=coupon.tenant_id,
        actor_id=principal.user_id,
        action="coupon.claim",
        target_type="coupon",
        target_id=coupon.id,
        request_id=getattr(request.state, "request_id", None),
        ip_address=request.client.host if request.client else None,
        payload=payload.model_dump(),
    )
    await session.commit()
    return ok(CouponResponse.model_validate(coupon).model_dump(mode="json"), request)


@coupons_router.post("/admin/issue")
async def admin_issue_coupon(
    payload: CouponIssueRequest,
    request: Request,
    principal: CurrentPrincipal = Depends(require_roles("merchant_admin", "support")),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, object]:
    tenant_id = _tenant_id(principal)
    user = await session.get(User, payload.user_id)
    if user is None or user.tenant_id != tenant_id:
        raise AppError("USER_NOT_FOUND", "User was not found.", status.HTTP_404_NOT_FOUND)
    coupon = await issue_coupon_from_template(
        session,
        tenant_id=tenant_id,
        user_id=user.id,
        template_id=payload.template_id,
        enforce_user_limit=payload.enforce_user_limit,
    )
    await write_audit_log(
        session,
        tenant_id=coupon.tenant_id,
        actor_id=principal.user_id,
        action="coupon.admin_issue",
        target_type="coupon",
        target_id=coupon.id,
        request_id=getattr(request.state, "request_id", None),
        ip_address=request.client.host if request.client else None,
        payload=payload.model_dump(mode="json"),
    )
    await session.commit()
    return ok(CouponResponse.model_validate(coupon).model_dump(mode="json"), request)


async def _load_coupon(session: AsyncSession, coupon_id: str) -> Coupon:
    coupon = await session.get(Coupon, coupon_id)
    if coupon is None:
        raise AppError("COUPON_NOT_FOUND", "Coupon was not found.", status.HTTP_404_NOT_FOUND)
    return coupon


@coupons_router.post("/{coupon_id}/lock")
async def lock(
    coupon_id: str,
    payload: CouponOrderRequest,
    request: Request,
    principal: CurrentPrincipal = Depends(require_roles("customer")),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, object]:
    coupon = lock_coupon(
        await _load_coupon(session, coupon_id),
        tenant_id=_tenant_id(principal),
        user_id=principal.user_id,
        order_id=payload.order_id,
    )
    await session.commit()
    return ok(CouponResponse.model_validate(coupon).model_dump(mode="json"), request)


@coupons_router.post("/{coupon_id}/use")
async def use(
    coupon_id: str,
    payload: CouponOrderRequest,
    request: Request,
    principal: CurrentPrincipal = Depends(require_roles("customer")),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, object]:
    coupon = use_coupon(
        await _load_coupon(session, coupon_id),
        tenant_id=_tenant_id(principal),
        user_id=principal.user_id,
        order_id=payload.order_id,
    )
    await session.commit()
    return ok(CouponResponse.model_validate(coupon).model_dump(mode="json"), request)


@coupons_router.post("/{coupon_id}/return")
async def return_locked(
    coupon_id: str,
    request: Request,
    principal: CurrentPrincipal = Depends(require_roles("customer")),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, object]:
    coupon = return_coupon(
        await _load_coupon(session, coupon_id),
        tenant_id=_tenant_id(principal),
        user_id=principal.user_id,
    )
    await session.commit()
    return ok(CouponResponse.model_validate(coupon).model_dump(mode="json"), request)
