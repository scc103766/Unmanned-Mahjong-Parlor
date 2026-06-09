from collections.abc import Sequence
from decimal import Decimal
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.coupons.models import Coupon
from app.modules.members.schemas import MemberDetailResponse, MemberSummaryResponse
from app.modules.orders.models import Order
from app.modules.users.models import User
from app.modules.wallet.models import WalletAccount, WalletLedger


def build_member_summary(
    *,
    user: User,
    wallet: Optional[WalletAccount],
    orders: Sequence[Order],
    coupons: Sequence[Coupon],
) -> MemberSummaryResponse:
    return MemberSummaryResponse(
        user_id=user.id,
        tenant_id=user.tenant_id or "",
        phone=user.phone,
        nickname=user.nickname,
        status=user.status,
        cash_balance=Decimal(wallet.cash_balance) if wallet is not None else Decimal("0.00"),
        gift_balance=Decimal(wallet.gift_balance) if wallet is not None else Decimal("0.00"),
        order_count=len(orders),
        completed_order_count=sum(1 for order in orders if order.status == "completed"),
        total_spend=sum(
            (Decimal(order.payable_amount) for order in orders if order.status == "completed"),
            Decimal("0.00"),
        ),
        coupon_count=len(coupons),
        available_coupon_count=sum(1 for coupon in coupons if coupon.status == "available"),
        created_at=user.created_at,
    )


async def load_member_summary(
    session: AsyncSession,
    *,
    tenant_id: str,
    user: User,
) -> MemberSummaryResponse:
    wallet = await session.scalar(
        select(WalletAccount).where(
            WalletAccount.tenant_id == tenant_id,
            WalletAccount.user_id == user.id,
        )
    )
    orders = list(
        (
            await session.scalars(
                select(Order).where(Order.tenant_id == tenant_id, Order.user_id == user.id)
            )
        ).all()
    )
    coupons = list(
        (
            await session.scalars(
                select(Coupon).where(Coupon.tenant_id == tenant_id, Coupon.user_id == user.id)
            )
        ).all()
    )
    return build_member_summary(user=user, wallet=wallet, orders=orders, coupons=coupons)


async def list_member_summaries(
    session: AsyncSession,
    *,
    tenant_id: str,
    limit: int,
) -> list[MemberSummaryResponse]:
    users = (
        await session.scalars(
            select(User)
            .where(User.tenant_id == tenant_id)
            .order_by(User.created_at.desc())
            .limit(limit)
        )
    ).all()
    return [
        await load_member_summary(session, tenant_id=tenant_id, user=user)
        for user in users
    ]


async def load_member_detail(
    session: AsyncSession,
    *,
    tenant_id: str,
    user: User,
) -> MemberDetailResponse:
    summary = await load_member_summary(session, tenant_id=tenant_id, user=user)
    recent_orders = (
        await session.scalars(
            select(Order)
            .where(Order.tenant_id == tenant_id, Order.user_id == user.id)
            .order_by(Order.created_at.desc())
            .limit(10)
        )
    ).all()
    recent_ledgers = (
        await session.scalars(
            select(WalletLedger)
            .where(WalletLedger.tenant_id == tenant_id, WalletLedger.user_id == user.id)
            .order_by(WalletLedger.created_at.desc())
            .limit(10)
        )
    ).all()
    return MemberDetailResponse(
        **summary.model_dump(),
        recent_order_ids=[order.id for order in recent_orders],
        recent_ledger_ids=[ledger.id for ledger in recent_ledgers],
    )
