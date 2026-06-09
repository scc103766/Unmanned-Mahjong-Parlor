from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import CurrentPrincipal, get_db_session, require_roles
from app.core.errors import AppError
from app.core.responses import ok
from app.modules.analytics.service import (
    default_analytics_range,
    get_cleaning_analytics,
    get_dashboard_summary,
    get_room_usage,
)

router = APIRouter()


def _tenant_id(principal: CurrentPrincipal, requested_tenant_id: Optional[str]) -> str:
    if principal.has_role("platform_admin"):
        if requested_tenant_id is None:
            raise AppError(
                "TENANT_REQUIRED",
                "tenant_id is required when platform admin queries tenant analytics.",
                status.HTTP_400_BAD_REQUEST,
            )
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
            "Cannot query another tenant analytics.",
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


@router.get("/dashboard")
async def dashboard(
    request: Request,
    tenant_id: Optional[str] = Query(default=None),
    store_id: Optional[str] = Query(default=None),
    start_at: Optional[datetime] = Query(default=None),
    end_at: Optional[datetime] = Query(default=None),
    principal: CurrentPrincipal = Depends(require_roles("merchant_admin", "clerk", "support")),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, object]:
    resolved_start_at, resolved_end_at = _resolve_range(start_at=start_at, end_at=end_at)
    response = await get_dashboard_summary(
        session,
        tenant_id=_tenant_id(principal, tenant_id),
        store_id=store_id,
        start_at=resolved_start_at,
        end_at=resolved_end_at,
    )
    return ok(response.model_dump(mode="json"), request)


@router.get("/rooms/usage")
async def room_usage(
    request: Request,
    tenant_id: Optional[str] = Query(default=None),
    store_id: Optional[str] = Query(default=None),
    start_at: Optional[datetime] = Query(default=None),
    end_at: Optional[datetime] = Query(default=None),
    principal: CurrentPrincipal = Depends(require_roles("merchant_admin", "clerk", "support")),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, object]:
    resolved_start_at, resolved_end_at = _resolve_range(start_at=start_at, end_at=end_at)
    response = await get_room_usage(
        session,
        tenant_id=_tenant_id(principal, tenant_id),
        store_id=store_id,
        start_at=resolved_start_at,
        end_at=resolved_end_at,
    )
    return ok(response.model_dump(mode="json"), request)


@router.get("/cleaning")
async def cleaning_analytics(
    request: Request,
    tenant_id: Optional[str] = Query(default=None),
    store_id: Optional[str] = Query(default=None),
    start_at: Optional[datetime] = Query(default=None),
    end_at: Optional[datetime] = Query(default=None),
    principal: CurrentPrincipal = Depends(require_roles("merchant_admin", "clerk", "support")),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, object]:
    resolved_start_at, resolved_end_at = _resolve_range(start_at=start_at, end_at=end_at)
    response = await get_cleaning_analytics(
        session,
        tenant_id=_tenant_id(principal, tenant_id),
        store_id=store_id,
        start_at=resolved_start_at,
        end_at=resolved_end_at,
    )
    return ok(response.model_dump(mode="json"), request)
