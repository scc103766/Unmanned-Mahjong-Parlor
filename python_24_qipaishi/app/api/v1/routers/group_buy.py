from fastapi import APIRouter, Depends, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import CurrentPrincipal, get_db_session, require_roles
from app.core.errors import AppError
from app.core.responses import ok
from app.modules.audit.service import write_audit_log
from app.modules.group_buy.models import GroupBuyCode
from app.modules.group_buy.schemas import (
    GroupBuyCodeCreateRequest,
    GroupBuyCodeResponse,
    GroupBuyOrderRequest,
    GroupBuyVerifyRequest,
)
from app.modules.group_buy.service import (
    lock_group_buy_code,
    return_group_buy_code,
    use_group_buy_code,
    verify_group_buy_code,
)

router = APIRouter()


def _tenant_id(principal: CurrentPrincipal) -> str:
    if principal.tenant_id is None:
        raise AppError(
            "TENANT_REQUIRED",
            "A tenant-scoped identity is required.",
            status.HTTP_403_FORBIDDEN,
        )
    return principal.tenant_id


@router.get("/codes")
async def list_codes(
    request: Request,
    principal: CurrentPrincipal = Depends(require_roles("merchant_admin", "clerk", "support")),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, object]:
    rows = (
        await session.scalars(
            select(GroupBuyCode)
            .where(GroupBuyCode.tenant_id == _tenant_id(principal))
            .order_by(GroupBuyCode.created_at.desc())
        )
    ).all()
    return ok(
        [GroupBuyCodeResponse.model_validate(row).model_dump(mode="json") for row in rows],
        request,
    )


@router.post("/codes")
async def create_code(
    payload: GroupBuyCodeCreateRequest,
    request: Request,
    principal: CurrentPrincipal = Depends(require_roles("merchant_admin", "clerk")),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, object]:
    row = GroupBuyCode(tenant_id=_tenant_id(principal), status="available", **payload.model_dump())
    session.add(row)
    await session.flush()
    await write_audit_log(
        session,
        tenant_id=row.tenant_id,
        actor_id=principal.user_id,
        action="group_buy_code.create",
        target_type="group_buy_code",
        target_id=row.id,
        request_id=getattr(request.state, "request_id", None),
        ip_address=request.client.host if request.client else None,
        payload=payload.model_dump(mode="json"),
    )
    await session.commit()
    return ok(GroupBuyCodeResponse.model_validate(row).model_dump(mode="json"), request)


@router.post("/verify")
async def verify(
    payload: GroupBuyVerifyRequest,
    request: Request,
    principal: CurrentPrincipal = Depends(require_roles("customer")),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, object]:
    row = await verify_group_buy_code(
        session,
        tenant_id=_tenant_id(principal),
        store_id=payload.store_id,
        code=payload.code,
    )
    return ok(GroupBuyCodeResponse.model_validate(row).model_dump(mode="json"), request)


async def _load_code(session: AsyncSession, code_id: str, tenant_id: str) -> GroupBuyCode:
    row = await session.get(GroupBuyCode, code_id)
    if row is None or row.tenant_id != tenant_id:
        raise AppError(
            "GROUP_BUY_CODE_NOT_FOUND",
            "Group-buy code was not found.",
            status.HTTP_404_NOT_FOUND,
        )
    return row


@router.post("/codes/{code_id}/lock")
async def lock(
    code_id: str,
    payload: GroupBuyOrderRequest,
    request: Request,
    principal: CurrentPrincipal = Depends(require_roles("customer")),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, object]:
    row = lock_group_buy_code(
        await _load_code(session, code_id, _tenant_id(principal)),
        order_id=payload.order_id,
    )
    await session.commit()
    return ok(GroupBuyCodeResponse.model_validate(row).model_dump(mode="json"), request)


@router.post("/codes/{code_id}/use")
async def use(
    code_id: str,
    payload: GroupBuyOrderRequest,
    request: Request,
    principal: CurrentPrincipal = Depends(require_roles("customer")),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, object]:
    row = use_group_buy_code(
        await _load_code(session, code_id, _tenant_id(principal)),
        order_id=payload.order_id,
    )
    await session.commit()
    return ok(GroupBuyCodeResponse.model_validate(row).model_dump(mode="json"), request)


@router.post("/codes/{code_id}/return")
async def return_locked(
    code_id: str,
    request: Request,
    principal: CurrentPrincipal = Depends(require_roles("customer")),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, object]:
    row = return_group_buy_code(await _load_code(session, code_id, _tenant_id(principal)))
    await session.commit()
    return ok(GroupBuyCodeResponse.model_validate(row).model_dump(mode="json"), request)
