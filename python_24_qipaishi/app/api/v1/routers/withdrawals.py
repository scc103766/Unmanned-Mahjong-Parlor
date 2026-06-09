from typing import Optional

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import CurrentPrincipal, get_db_session, require_roles
from app.core.errors import AppError
from app.core.responses import ok
from app.modules.audit.service import write_audit_log
from app.modules.withdrawals.models import Withdrawal
from app.modules.withdrawals.schemas import (
    WithdrawalCreateRequest,
    WithdrawalPaidRequest,
    WithdrawalRejectRequest,
    WithdrawalResponse,
    WithdrawalReviewRequest,
)
from app.modules.withdrawals.service import (
    approve_withdrawal,
    create_withdrawal_request,
    load_withdrawal,
    mark_withdrawal_paid,
    reject_withdrawal,
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


@router.get("")
async def list_withdrawals(
    request: Request,
    status_value: Optional[str] = Query(default=None, alias="status"),
    user_id: Optional[str] = Query(default=None),
    principal: CurrentPrincipal = Depends(require_roles("merchant_admin", "support")),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, object]:
    query = select(Withdrawal).where(Withdrawal.tenant_id == _tenant_id(principal))
    if status_value is not None:
        query = query.where(Withdrawal.status == status_value)
    if user_id is not None:
        query = query.where(Withdrawal.user_id == user_id)
    rows = (await session.scalars(query.order_by(Withdrawal.created_at.desc()))).all()
    return ok(
        [WithdrawalResponse.model_validate(row).model_dump(mode="json") for row in rows],
        request,
    )


@router.get("/me")
async def my_withdrawals(
    request: Request,
    principal: CurrentPrincipal = Depends(require_roles("customer", "cleaner", "merchant_admin")),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, object]:
    rows = (
        await session.scalars(
            select(Withdrawal)
            .where(Withdrawal.tenant_id == _tenant_id(principal))
            .where(Withdrawal.user_id == principal.user_id)
            .order_by(Withdrawal.created_at.desc())
        )
    ).all()
    return ok(
        [WithdrawalResponse.model_validate(row).model_dump(mode="json") for row in rows],
        request,
    )


@router.post("")
async def create_withdrawal(
    payload: WithdrawalCreateRequest,
    request: Request,
    principal: CurrentPrincipal = Depends(require_roles("customer", "cleaner", "merchant_admin")),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, object]:
    withdrawal = await create_withdrawal_request(
        session,
        tenant_id=_tenant_id(principal),
        user_id=principal.user_id,
        requested_by=principal.user_id,
        amount=payload.amount,
        remark=payload.remark,
        payout_payload=payload.payout_payload,
    )
    await write_audit_log(
        session,
        tenant_id=withdrawal.tenant_id,
        actor_id=principal.user_id,
        action="withdrawal.create",
        target_type="withdrawal",
        target_id=withdrawal.id,
        request_id=getattr(request.state, "request_id", None),
        ip_address=request.client.host if request.client else None,
        payload=payload.model_dump(mode="json"),
    )
    await session.commit()
    return ok(WithdrawalResponse.model_validate(withdrawal).model_dump(mode="json"), request)


@router.post("/{withdrawal_id}/approve")
async def approve(
    withdrawal_id: str,
    payload: WithdrawalReviewRequest,
    request: Request,
    principal: CurrentPrincipal = Depends(require_roles("merchant_admin", "support")),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, object]:
    withdrawal = await load_withdrawal(
        session,
        tenant_id=_tenant_id(principal),
        withdrawal_id=withdrawal_id,
    )
    await approve_withdrawal(
        session,
        withdrawal=withdrawal,
        reviewer_id=principal.user_id,
        note=payload.note,
    )
    await write_audit_log(
        session,
        tenant_id=withdrawal.tenant_id,
        actor_id=principal.user_id,
        action="withdrawal.approve",
        target_type="withdrawal",
        target_id=withdrawal.id,
        request_id=getattr(request.state, "request_id", None),
        ip_address=request.client.host if request.client else None,
        payload=payload.model_dump(mode="json"),
    )
    await session.commit()
    return ok(WithdrawalResponse.model_validate(withdrawal).model_dump(mode="json"), request)


@router.post("/{withdrawal_id}/reject")
async def reject(
    withdrawal_id: str,
    payload: WithdrawalRejectRequest,
    request: Request,
    principal: CurrentPrincipal = Depends(require_roles("merchant_admin", "support")),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, object]:
    withdrawal = await load_withdrawal(
        session,
        tenant_id=_tenant_id(principal),
        withdrawal_id=withdrawal_id,
    )
    reject_withdrawal(withdrawal, reviewer_id=principal.user_id, reason=payload.reason)
    await write_audit_log(
        session,
        tenant_id=withdrawal.tenant_id,
        actor_id=principal.user_id,
        action="withdrawal.reject",
        target_type="withdrawal",
        target_id=withdrawal.id,
        request_id=getattr(request.state, "request_id", None),
        ip_address=request.client.host if request.client else None,
        payload=payload.model_dump(mode="json"),
    )
    await session.commit()
    return ok(WithdrawalResponse.model_validate(withdrawal).model_dump(mode="json"), request)


@router.post("/{withdrawal_id}/mark-paid")
async def mark_paid(
    withdrawal_id: str,
    payload: WithdrawalPaidRequest,
    request: Request,
    principal: CurrentPrincipal = Depends(require_roles("merchant_admin", "support")),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, object]:
    withdrawal = await load_withdrawal(
        session,
        tenant_id=_tenant_id(principal),
        withdrawal_id=withdrawal_id,
    )
    mark_withdrawal_paid(
        withdrawal,
        paid_by=principal.user_id,
        payout_ref=payload.payout_ref,
        note=payload.note,
    )
    await write_audit_log(
        session,
        tenant_id=withdrawal.tenant_id,
        actor_id=principal.user_id,
        action="withdrawal.mark_paid",
        target_type="withdrawal",
        target_id=withdrawal.id,
        request_id=getattr(request.state, "request_id", None),
        ip_address=request.client.host if request.client else None,
        payload=payload.model_dump(mode="json"),
    )
    await session.commit()
    return ok(WithdrawalResponse.model_validate(withdrawal).model_dump(mode="json"), request)
