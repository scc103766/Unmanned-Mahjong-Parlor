from decimal import Decimal
from typing import Optional

from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError
from app.modules.availability.service import utc_now
from app.modules.wallet.models import WalletLedger
from app.modules.wallet.service import get_or_create_wallet
from app.modules.withdrawals.models import Withdrawal


async def create_withdrawal_request(
    session: AsyncSession,
    *,
    tenant_id: str,
    user_id: str,
    requested_by: str,
    amount: Decimal,
    remark: Optional[str],
    payout_payload: dict[str, object],
) -> Withdrawal:
    account = await get_or_create_wallet(session, tenant_id=tenant_id, user_id=user_id)
    if Decimal(account.cash_balance) < amount:
        raise AppError(
            "WITHDRAWAL_BALANCE_INSUFFICIENT",
            "Cash balance is insufficient for withdrawal.",
            status.HTTP_409_CONFLICT,
        )
    row = Withdrawal(
        tenant_id=tenant_id,
        user_id=user_id,
        requested_by=requested_by,
        amount=amount,
        status="pending",
        remark=remark,
        payout_payload=payout_payload,
        requested_at=utc_now(),
    )
    session.add(row)
    await session.flush()
    return row


async def load_withdrawal(
    session: AsyncSession,
    *,
    tenant_id: str,
    withdrawal_id: str,
) -> Withdrawal:
    row = await session.get(Withdrawal, withdrawal_id)
    if row is None or row.tenant_id != tenant_id:
        raise AppError(
            "WITHDRAWAL_NOT_FOUND",
            "Withdrawal was not found.",
            status.HTTP_404_NOT_FOUND,
        )
    return row


async def approve_withdrawal(
    session: AsyncSession,
    *,
    withdrawal: Withdrawal,
    reviewer_id: str,
    note: Optional[str],
) -> Withdrawal:
    if withdrawal.status != "pending":
        raise AppError(
            "WITHDRAWAL_STATE_INVALID",
            "Only pending withdrawals can be approved.",
            status.HTTP_409_CONFLICT,
        )
    account = await get_or_create_wallet(
        session,
        tenant_id=withdrawal.tenant_id,
        user_id=withdrawal.user_id,
    )
    amount = Decimal(withdrawal.amount)
    if Decimal(account.cash_balance) < amount:
        raise AppError(
            "WITHDRAWAL_BALANCE_INSUFFICIENT",
            "Cash balance is insufficient for withdrawal approval.",
            status.HTTP_409_CONFLICT,
        )
    account.cash_balance = Decimal(account.cash_balance) - amount
    session.add(
        WalletLedger(
            tenant_id=withdrawal.tenant_id,
            account_id=account.id,
            user_id=withdrawal.user_id,
            direction="debit",
            amount=amount,
            cash_balance_after=account.cash_balance,
            gift_balance_after=account.gift_balance,
            biz_type="withdrawal",
            biz_id=withdrawal.id,
            remark=note,
        )
    )
    withdrawal.status = "approved"
    withdrawal.reviewed_by = reviewer_id
    withdrawal.reviewed_at = utc_now()
    withdrawal.review_note = note
    await session.flush()
    return withdrawal


def reject_withdrawal(
    withdrawal: Withdrawal,
    *,
    reviewer_id: str,
    reason: str,
) -> Withdrawal:
    if withdrawal.status != "pending":
        raise AppError(
            "WITHDRAWAL_STATE_INVALID",
            "Only pending withdrawals can be rejected.",
            status.HTTP_409_CONFLICT,
        )
    withdrawal.status = "rejected"
    withdrawal.reviewed_by = reviewer_id
    withdrawal.reviewed_at = utc_now()
    withdrawal.rejected_at = withdrawal.reviewed_at
    withdrawal.reject_reason = reason
    return withdrawal


def mark_withdrawal_paid(
    withdrawal: Withdrawal,
    *,
    paid_by: str,
    payout_ref: str,
    note: Optional[str],
) -> Withdrawal:
    if withdrawal.status != "approved":
        raise AppError(
            "WITHDRAWAL_STATE_INVALID",
            "Only approved withdrawals can be marked as paid.",
            status.HTTP_409_CONFLICT,
        )
    withdrawal.status = "paid"
    withdrawal.paid_by = paid_by
    withdrawal.paid_at = utc_now()
    withdrawal.payout_ref = payout_ref
    withdrawal.review_note = note or withdrawal.review_note
    return withdrawal
