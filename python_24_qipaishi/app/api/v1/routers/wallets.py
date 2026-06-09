from fastapi import APIRouter, Depends, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import CurrentPrincipal, get_db_session, require_roles
from app.core.errors import AppError
from app.core.responses import ok
from app.modules.audit.service import write_audit_log
from app.modules.wallet.models import WalletLedger
from app.modules.wallet.schemas import (
    WalletAccountResponse,
    WalletAdjustmentRequest,
    WalletLedgerResponse,
    WalletRechargeRequest,
)
from app.modules.wallet.service import adjust_wallet, get_or_create_wallet, recharge_wallet

router = APIRouter()


def _tenant_id(principal: CurrentPrincipal) -> str:
    if principal.tenant_id is None:
        raise AppError(
            "TENANT_REQUIRED",
            "A tenant-scoped identity is required.",
            status.HTTP_403_FORBIDDEN,
        )
    return principal.tenant_id


@router.get("/me")
async def my_wallet(
    request: Request,
    principal: CurrentPrincipal = Depends(require_roles("customer")),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, object]:
    account = await get_or_create_wallet(
        session,
        tenant_id=_tenant_id(principal),
        user_id=principal.user_id,
    )
    await session.commit()
    return ok(WalletAccountResponse.model_validate(account).model_dump(mode="json"), request)


@router.post("/recharge")
async def recharge(
    payload: WalletRechargeRequest,
    request: Request,
    principal: CurrentPrincipal = Depends(require_roles("customer")),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, object]:
    account = await recharge_wallet(
        session,
        tenant_id=_tenant_id(principal),
        user_id=principal.user_id,
        amount=payload.amount,
        gift_amount=payload.gift_amount,
        remark=payload.remark,
    )
    await write_audit_log(
        session,
        tenant_id=account.tenant_id,
        actor_id=principal.user_id,
        action="wallet.recharge",
        target_type="wallet_account",
        target_id=account.id,
        request_id=getattr(request.state, "request_id", None),
        ip_address=request.client.host if request.client else None,
        payload=payload.model_dump(mode="json"),
    )
    await session.commit()
    return ok(WalletAccountResponse.model_validate(account).model_dump(mode="json"), request)


@router.get("/me/ledgers")
async def my_wallet_ledgers(
    request: Request,
    principal: CurrentPrincipal = Depends(require_roles("customer")),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, object]:
    rows = (
        await session.scalars(
            select(WalletLedger)
            .where(WalletLedger.tenant_id == _tenant_id(principal))
            .where(WalletLedger.user_id == principal.user_id)
            .order_by(WalletLedger.created_at.desc())
        )
    ).all()
    return ok(
        [WalletLedgerResponse.model_validate(row).model_dump(mode="json") for row in rows],
        request,
    )


@router.post("/admin/adjustments")
async def admin_adjust_wallet(
    payload: WalletAdjustmentRequest,
    request: Request,
    principal: CurrentPrincipal = Depends(require_roles("merchant_admin", "support")),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, object]:
    account = await adjust_wallet(
        session,
        tenant_id=_tenant_id(principal),
        user_id=payload.user_id,
        direction=payload.direction,
        cash_amount=payload.cash_amount,
        gift_amount=payload.gift_amount,
        actor_id=principal.user_id,
        remark=payload.remark,
    )
    await write_audit_log(
        session,
        tenant_id=account.tenant_id,
        actor_id=principal.user_id,
        action="wallet.admin_adjust",
        target_type="wallet_account",
        target_id=account.id,
        request_id=getattr(request.state, "request_id", None),
        ip_address=request.client.host if request.client else None,
        payload=payload.model_dump(mode="json"),
    )
    await session.commit()
    return ok(WalletAccountResponse.model_validate(account).model_dump(mode="json"), request)
