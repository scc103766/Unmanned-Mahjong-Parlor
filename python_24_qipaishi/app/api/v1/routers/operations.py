from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import CurrentPrincipal, get_db_session, require_roles
from app.core.errors import AppError
from app.core.responses import ok
from app.modules.analytics.service import default_analytics_range
from app.modules.audit.service import write_audit_log
from app.modules.coupons.service import issue_coupon_from_template
from app.modules.operations.schemas import (
    AuditLogListResponse,
    ManualCompensationRequest,
    ManualCompensationResponse,
    OperationExceptionListResponse,
)
from app.modules.operations.service import list_audit_logs, list_operation_exceptions
from app.modules.users.models import User
from app.modules.wallet.service import adjust_wallet

router = APIRouter()


def _tenant_scope(principal: CurrentPrincipal, requested_tenant_id: Optional[str]) -> Optional[str]:
    if principal.has_role("platform_admin"):
        return requested_tenant_id
    if principal.tenant_id is None:
        raise AppError(
            "TENANT_REQUIRED",
            "A tenant-scoped identity is required.",
            status.HTTP_403_FORBIDDEN,
        )
    if requested_tenant_id is not None and requested_tenant_id != principal.tenant_id:
        raise AppError(
            "FORBIDDEN",
            "Cannot query another tenant operations data.",
            status.HTTP_403_FORBIDDEN,
        )
    return principal.tenant_id


def _resolve_range(
    *,
    start_at: Optional[datetime],
    end_at: Optional[datetime],
) -> tuple[datetime, datetime]:
    resolved_start_at, resolved_end_at = default_analytics_range(start_at=start_at, end_at=end_at)
    if resolved_end_at <= resolved_start_at:
        raise AppError("INVALID_TIME_RANGE", "end_at must be later than start_at.")
    return resolved_start_at, resolved_end_at


@router.get("/exceptions")
async def exceptions(
    request: Request,
    tenant_id: Optional[str] = Query(default=None),
    store_id: Optional[str] = Query(default=None),
    source: Optional[str] = Query(
        default=None,
        pattern="^(payment|refund|withdrawal|device|cleaning)$",
    ),
    start_at: Optional[datetime] = Query(default=None),
    end_at: Optional[datetime] = Query(default=None),
    principal: CurrentPrincipal = Depends(require_roles("merchant_admin", "support")),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, object]:
    resolved_start_at, resolved_end_at = _resolve_range(start_at=start_at, end_at=end_at)
    rows = await list_operation_exceptions(
        session,
        tenant_id=_tenant_scope(principal, tenant_id),
        store_id=store_id,
        source=source,
        start_at=resolved_start_at,
        end_at=resolved_end_at,
    )
    return ok(OperationExceptionListResponse(exceptions=rows).model_dump(mode="json"), request)


@router.get("/audit-logs")
async def audit_logs(
    request: Request,
    tenant_id: Optional[str] = Query(default=None),
    actor_id: Optional[str] = Query(default=None),
    action: Optional[str] = Query(default=None),
    target_type: Optional[str] = Query(default=None),
    start_at: Optional[datetime] = Query(default=None),
    end_at: Optional[datetime] = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    principal: CurrentPrincipal = Depends(require_roles("merchant_admin", "support")),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, object]:
    resolved_start_at, resolved_end_at = _resolve_range(start_at=start_at, end_at=end_at)
    rows = await list_audit_logs(
        session,
        tenant_id=_tenant_scope(principal, tenant_id),
        actor_id=actor_id,
        action=action,
        target_type=target_type,
        start_at=resolved_start_at,
        end_at=resolved_end_at,
        limit=limit,
    )
    return ok(AuditLogListResponse(logs=rows).model_dump(mode="json"), request)


@router.post("/compensations")
async def create_compensation(
    payload: ManualCompensationRequest,
    request: Request,
    principal: CurrentPrincipal = Depends(require_roles("merchant_admin", "support")),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, object]:
    tenant_id = _tenant_scope(principal, payload.tenant_id)
    if tenant_id is None:
        raise AppError(
            "TENANT_REQUIRED",
            "tenant_id is required for manual compensation.",
            status.HTTP_400_BAD_REQUEST,
        )
    if (
        payload.cash_amount <= 0
        and payload.gift_amount <= 0
        and payload.coupon_template_id is None
    ):
        raise AppError(
            "COMPENSATION_EMPTY",
            "Manual compensation must include wallet amount or coupon template.",
            status.HTTP_400_BAD_REQUEST,
        )
    user = await session.get(User, payload.user_id)
    if user is None or user.tenant_id != tenant_id:
        raise AppError("USER_NOT_FOUND", "User was not found.", status.HTTP_404_NOT_FOUND)

    wallet_account_id = None
    coupon_id = None
    if payload.cash_amount > 0 or payload.gift_amount > 0:
        account = await adjust_wallet(
            session,
            tenant_id=tenant_id,
            user_id=user.id,
            direction="credit",
            cash_amount=payload.cash_amount,
            gift_amount=payload.gift_amount,
            actor_id=principal.user_id,
            remark=payload.reason,
        )
        wallet_account_id = account.id
    if payload.coupon_template_id is not None:
        coupon = await issue_coupon_from_template(
            session,
            tenant_id=tenant_id,
            user_id=user.id,
            template_id=payload.coupon_template_id,
            enforce_user_limit=False,
        )
        coupon_id = coupon.id

    await write_audit_log(
        session,
        tenant_id=tenant_id,
        actor_id=principal.user_id,
        action="operations.compensate",
        target_type="user",
        target_id=user.id,
        request_id=getattr(request.state, "request_id", None),
        ip_address=request.client.host if request.client else None,
        payload=payload.model_dump(mode="json"),
    )
    await session.commit()
    response = ManualCompensationResponse(
        user_id=user.id,
        cash_amount=payload.cash_amount,
        gift_amount=payload.gift_amount,
        coupon_id=coupon_id,
        wallet_account_id=wallet_account_id,
    )
    return ok(response.model_dump(mode="json"), request)
