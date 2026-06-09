from decimal import Decimal
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError
from app.modules.wallet.models import WalletAccount, WalletLedger


async def get_or_create_wallet(
    session: AsyncSession,
    *,
    tenant_id: str,
    user_id: str,
) -> WalletAccount:
    account = await session.scalar(
        select(WalletAccount).where(
            WalletAccount.tenant_id == tenant_id,
            WalletAccount.user_id == user_id,
        )
    )
    if account is not None:
        return account
    account = WalletAccount(
        tenant_id=tenant_id,
        user_id=user_id,
        cash_balance=Decimal("0.00"),
        gift_balance=Decimal("0.00"),
        status="active",
    )
    session.add(account)
    await session.flush()
    return account


async def recharge_wallet(
    session: AsyncSession,
    *,
    tenant_id: str,
    user_id: str,
    amount: Decimal,
    gift_amount: Decimal,
    remark: Optional[str],
) -> WalletAccount:
    account = await get_or_create_wallet(session, tenant_id=tenant_id, user_id=user_id)
    account.cash_balance = Decimal(account.cash_balance) + amount
    account.gift_balance = Decimal(account.gift_balance) + gift_amount
    session.add(
        WalletLedger(
            tenant_id=tenant_id,
            account_id=account.id,
            user_id=user_id,
            direction="credit",
            amount=amount + gift_amount,
            cash_balance_after=account.cash_balance,
            gift_balance_after=account.gift_balance,
            biz_type="mock_recharge",
            biz_id=None,
            remark=remark,
        )
    )
    await session.flush()
    return account


async def adjust_wallet(
    session: AsyncSession,
    *,
    tenant_id: str,
    user_id: str,
    direction: str,
    cash_amount: Decimal,
    gift_amount: Decimal,
    actor_id: str,
    remark: Optional[str],
) -> WalletAccount:
    account = await get_or_create_wallet(session, tenant_id=tenant_id, user_id=user_id)
    if cash_amount + gift_amount <= Decimal("0"):
        raise AppError("WALLET_ADJUSTMENT_EMPTY", "Wallet adjustment amount must be positive.")
    if direction == "credit":
        account.cash_balance = Decimal(account.cash_balance) + cash_amount
        account.gift_balance = Decimal(account.gift_balance) + gift_amount
    elif direction == "debit":
        cash_insufficient = Decimal(account.cash_balance) < cash_amount
        gift_insufficient = Decimal(account.gift_balance) < gift_amount
        if cash_insufficient or gift_insufficient:
            raise AppError("WALLET_BALANCE_INSUFFICIENT", "Wallet balance is insufficient.")
        account.cash_balance = Decimal(account.cash_balance) - cash_amount
        account.gift_balance = Decimal(account.gift_balance) - gift_amount
    else:
        raise AppError("WALLET_ADJUSTMENT_INVALID", "Wallet adjustment direction is invalid.")

    session.add(
        WalletLedger(
            tenant_id=tenant_id,
            account_id=account.id,
            user_id=user_id,
            direction=direction,
            amount=cash_amount + gift_amount,
            cash_balance_after=account.cash_balance,
            gift_balance_after=account.gift_balance,
            biz_type="manual_adjustment",
            biz_id=actor_id,
            remark=remark,
        )
    )
    await session.flush()
    return account


async def debit_wallet(
    session: AsyncSession,
    *,
    tenant_id: str,
    user_id: str,
    amount: Decimal,
    biz_type: str,
    biz_id: Optional[str],
    remark: Optional[str],
) -> dict[str, Decimal]:
    account = await get_or_create_wallet(session, tenant_id=tenant_id, user_id=user_id)
    cash_balance = Decimal(account.cash_balance)
    gift_balance = Decimal(account.gift_balance)
    if amount <= Decimal("0"):
        return {"cash_amount": Decimal("0.00"), "gift_amount": Decimal("0.00")}
    if cash_balance + gift_balance < amount:
        raise AppError("WALLET_BALANCE_INSUFFICIENT", "Wallet balance is insufficient.")

    gift_amount = min(gift_balance, amount)
    cash_amount = amount - gift_amount
    account.gift_balance = gift_balance - gift_amount
    account.cash_balance = cash_balance - cash_amount
    session.add(
        WalletLedger(
            tenant_id=tenant_id,
            account_id=account.id,
            user_id=user_id,
            direction="debit",
            amount=amount,
            cash_balance_after=account.cash_balance,
            gift_balance_after=account.gift_balance,
            biz_type=biz_type,
            biz_id=biz_id,
            remark=remark,
        )
    )
    await session.flush()
    return {"cash_amount": cash_amount, "gift_amount": gift_amount}


async def credit_wallet_split(
    session: AsyncSession,
    *,
    tenant_id: str,
    user_id: str,
    cash_amount: Decimal,
    gift_amount: Decimal,
    biz_type: str,
    biz_id: Optional[str],
    remark: Optional[str],
) -> WalletAccount:
    account = await get_or_create_wallet(session, tenant_id=tenant_id, user_id=user_id)
    account.cash_balance = Decimal(account.cash_balance) + cash_amount
    account.gift_balance = Decimal(account.gift_balance) + gift_amount
    session.add(
        WalletLedger(
            tenant_id=tenant_id,
            account_id=account.id,
            user_id=user_id,
            direction="credit",
            amount=cash_amount + gift_amount,
            cash_balance_after=account.cash_balance,
            gift_balance_after=account.gift_balance,
            biz_type=biz_type,
            biz_id=biz_id,
            remark=remark,
        )
    )
    await session.flush()
    return account
