from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import CurrentPrincipal, get_db_session, require_roles
from app.core.errors import AppError
from app.core.responses import ok
from app.modules.availability.service import get_room_availability, utc_now, validate_future_range
from app.modules.rooms.models import Room
from app.modules.stores.models import Store

router = APIRouter()


def _tenant_id(principal: CurrentPrincipal) -> str:
    if principal.tenant_id is None:
        raise AppError(
            "TENANT_REQUIRED",
            "A tenant-scoped identity is required.",
            status.HTTP_403_FORBIDDEN,
        )
    return principal.tenant_id


@router.get("/rooms")
async def room_availability(
    request: Request,
    store_id: str = Query(...),
    start_at: datetime = Query(...),
    end_at: datetime = Query(...),
    room_id: Optional[str] = Query(default=None),
    principal: CurrentPrincipal = Depends(
        require_roles("merchant_admin", "clerk", "cleaner", "customer", "support")
    ),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, object]:
    tenant_id = _tenant_id(principal)
    now = utc_now()
    validate_future_range(start_at, end_at, now)

    store = await session.get(Store, store_id)
    if store is None or store.tenant_id != tenant_id:
        raise AppError("STORE_NOT_FOUND", "Store was not found.", status.HTTP_404_NOT_FOUND)

    query = select(Room).where(Room.tenant_id == tenant_id, Room.store_id == store_id)
    if room_id is not None:
        query = query.where(Room.id == room_id)
    rooms = (await session.scalars(query.order_by(Room.sort_order, Room.created_at.desc()))).all()

    results = [
        (
            await get_room_availability(
                session,
                room=room,
                start_at=start_at,
                end_at=end_at,
                now=now,
            )
        ).model_dump(mode="json")
        for room in rooms
    ]
    return ok(results, request)
