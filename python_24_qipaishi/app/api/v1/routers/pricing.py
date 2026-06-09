from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import CurrentPrincipal, get_db_session, require_roles
from app.core.errors import AppError
from app.core.responses import ok
from app.modules.pricing.schemas import PricingQuoteRequest
from app.modules.pricing.service import quote_room
from app.modules.rooms.models import Room

router = APIRouter()


def _tenant_id(principal: CurrentPrincipal) -> str:
    if principal.tenant_id is None:
        raise AppError(
            "TENANT_REQUIRED",
            "A tenant-scoped identity is required.",
            status.HTTP_403_FORBIDDEN,
        )
    return principal.tenant_id


@router.post("/quote")
async def quote(
    payload: PricingQuoteRequest,
    request: Request,
    principal: CurrentPrincipal = Depends(
        require_roles("merchant_admin", "clerk", "cleaner", "customer", "support")
    ),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, object]:
    tenant_id = _tenant_id(principal)
    room = await session.get(Room, payload.room_id)
    if room is None or room.tenant_id != tenant_id:
        raise AppError("ROOM_NOT_FOUND", "Room was not found.", status.HTTP_404_NOT_FOUND)
    quote_body = await quote_room(
        session,
        tenant_id=tenant_id,
        room_id=room.id,
        start_at=payload.start_at,
        end_at=payload.end_at,
    )
    return ok(quote_body.model_dump(mode="json"), request)
