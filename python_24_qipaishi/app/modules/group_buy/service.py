from fastapi import status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError
from app.modules.group_buy.models import GroupBuyCode


async def verify_group_buy_code(
    session: AsyncSession,
    *,
    tenant_id: str,
    store_id: str,
    code: str,
) -> GroupBuyCode:
    row = await session.scalar(
        select(GroupBuyCode).where(
            GroupBuyCode.tenant_id == tenant_id,
            GroupBuyCode.store_id == store_id,
            GroupBuyCode.code == code,
        )
    )
    if row is None:
        raise AppError(
            "GROUP_BUY_CODE_NOT_FOUND",
            "Group-buy code was not found.",
            status.HTTP_404_NOT_FOUND,
        )
    if row.status not in {"available", "locked"}:
        raise AppError(
            "GROUP_BUY_CODE_STATE_INVALID",
            "Group-buy code is not available.",
            status.HTTP_409_CONFLICT,
        )
    return row


def lock_group_buy_code(row: GroupBuyCode, *, order_id: str) -> GroupBuyCode:
    if row.status != "available":
        raise AppError(
            "GROUP_BUY_CODE_STATE_INVALID",
            "Only available codes can be locked.",
            status.HTTP_409_CONFLICT,
        )
    row.status = "locked"
    row.locked_order_id = order_id
    return row


def use_group_buy_code(row: GroupBuyCode, *, order_id: str) -> GroupBuyCode:
    if row.status != "locked" or row.locked_order_id != order_id:
        raise AppError(
            "GROUP_BUY_CODE_STATE_INVALID",
            "Code is not locked for this order.",
            status.HTTP_409_CONFLICT,
        )
    row.status = "used"
    row.verified_order_id = order_id
    return row


def return_group_buy_code(row: GroupBuyCode) -> GroupBuyCode:
    if row.status != "locked":
        raise AppError(
            "GROUP_BUY_CODE_STATE_INVALID",
            "Only locked codes can be returned.",
            status.HTTP_409_CONFLICT,
        )
    row.status = "available"
    row.locked_order_id = None
    return row


def refund_group_buy_code(row: GroupBuyCode, *, order_id: str) -> GroupBuyCode:
    if row.status != "used" or row.verified_order_id != order_id:
        raise AppError(
            "GROUP_BUY_CODE_STATE_INVALID",
            "Only codes used by this order can be refunded.",
            status.HTTP_409_CONFLICT,
        )
    row.status = "available"
    row.locked_order_id = None
    row.verified_order_id = None
    return row
