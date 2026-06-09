from typing import Optional

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import CurrentPrincipal, get_db_session, require_roles
from app.core.errors import AppError
from app.core.responses import ok
from app.modules.audit.service import write_audit_log
from app.modules.rooms.models import Room, RoomBlockedSlot, RoomPriceRule
from app.modules.rooms.schemas import (
    RoomBlockedSlotCreateRequest,
    RoomBlockedSlotResponse,
    RoomCreateRequest,
    RoomDetailResponse,
    RoomPriceRuleCreateRequest,
    RoomPriceRuleResponse,
    RoomResponse,
    RoomUpdateRequest,
)
from app.modules.stores.models import Store

router = APIRouter()


async def _load_store(
    session: AsyncSession,
    store_id: str,
    principal: CurrentPrincipal,
) -> Store:
    store = await session.get(Store, store_id)
    if store is None:
        raise AppError("STORE_NOT_FOUND", "Store was not found.", status.HTTP_404_NOT_FOUND)
    if not principal.has_role("platform_admin") and principal.tenant_id != store.tenant_id:
        raise AppError(
            "FORBIDDEN",
            "Cannot access another tenant store.",
            status.HTTP_403_FORBIDDEN,
        )
    return store


async def _load_room(
    session: AsyncSession,
    room_id: str,
    principal: CurrentPrincipal,
) -> Room:
    room = await session.get(Room, room_id)
    if room is None:
        raise AppError("ROOM_NOT_FOUND", "Room was not found.", status.HTTP_404_NOT_FOUND)
    if not principal.has_role("platform_admin") and principal.tenant_id != room.tenant_id:
        raise AppError("FORBIDDEN", "Cannot access another tenant room.", status.HTTP_403_FORBIDDEN)
    return room


async def _room_detail(session: AsyncSession, room: Room) -> RoomDetailResponse:
    price_rules = (
        await session.scalars(
            select(RoomPriceRule)
            .where(RoomPriceRule.room_id == room.id)
            .order_by(RoomPriceRule.created_at.desc())
        )
    ).all()
    blocked_slots = (
        await session.scalars(
            select(RoomBlockedSlot)
            .where(RoomBlockedSlot.room_id == room.id)
            .order_by(RoomBlockedSlot.start_at.desc())
        )
    ).all()
    return RoomDetailResponse.model_validate(room).model_copy(
        update={
            "price_rules": [
                RoomPriceRuleResponse.model_validate(rule) for rule in price_rules
            ],
            "blocked_slots": [
                RoomBlockedSlotResponse.model_validate(slot) for slot in blocked_slots
            ],
        }
    )


@router.get("")
async def list_rooms(
    request: Request,
    store_id: Optional[str] = Query(default=None),
    tenant_id: Optional[str] = Query(default=None),
    principal: CurrentPrincipal = Depends(
        require_roles("merchant_admin", "clerk", "cleaner", "customer", "support")
    ),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, object]:
    query = select(Room).order_by(Room.sort_order, Room.created_at.desc())
    if store_id is not None:
        await _load_store(session, store_id, principal)
        query = query.where(Room.store_id == store_id)
    elif principal.has_role("platform_admin"):
        if tenant_id is not None:
            query = query.where(Room.tenant_id == tenant_id)
    elif principal.tenant_id is not None:
        query = query.where(Room.tenant_id == principal.tenant_id)
    else:
        raise AppError("TENANT_REQUIRED", "A tenant-scoped identity is required.")

    rooms = (await session.scalars(query)).all()
    return ok(
        [RoomResponse.model_validate(room).model_dump(mode="json") for room in rooms],
        request,
    )


@router.post("")
async def create_room(
    payload: RoomCreateRequest,
    request: Request,
    principal: CurrentPrincipal = Depends(require_roles("merchant_admin")),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, object]:
    store = await _load_store(session, payload.store_id, principal)
    room = Room(
        tenant_id=store.tenant_id,
        store_id=payload.store_id,
        name=payload.name,
        room_type=payload.room_type,
        capacity=payload.capacity,
        tags=payload.tags,
        images=payload.images,
        status=payload.status,
        sort_order=payload.sort_order,
    )
    session.add(room)
    await session.flush()
    await write_audit_log(
        session,
        tenant_id=store.tenant_id,
        actor_id=principal.user_id,
        action="room.create",
        target_type="room",
        target_id=room.id,
        request_id=getattr(request.state, "request_id", None),
        ip_address=request.client.host if request.client else None,
        payload=payload.model_dump(),
    )
    await session.commit()
    return ok(RoomResponse.model_validate(room).model_dump(mode="json"), request)


@router.get("/{room_id}")
async def get_room(
    room_id: str,
    request: Request,
    principal: CurrentPrincipal = Depends(
        require_roles("merchant_admin", "clerk", "cleaner", "customer", "support")
    ),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, object]:
    room = await _load_room(session, room_id, principal)
    detail = await _room_detail(session, room)
    return ok(detail.model_dump(mode="json"), request)


@router.patch("/{room_id}")
async def update_room(
    room_id: str,
    payload: RoomUpdateRequest,
    request: Request,
    principal: CurrentPrincipal = Depends(require_roles("merchant_admin")),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, object]:
    room = await _load_room(session, room_id, principal)
    changes = payload.model_dump(exclude_unset=True)
    for key, value in changes.items():
        setattr(room, key, value)
    await write_audit_log(
        session,
        tenant_id=room.tenant_id,
        actor_id=principal.user_id,
        action="room.update",
        target_type="room",
        target_id=room.id,
        request_id=getattr(request.state, "request_id", None),
        ip_address=request.client.host if request.client else None,
        payload=changes,
    )
    await session.commit()
    return ok(RoomResponse.model_validate(room).model_dump(mode="json"), request)


@router.post("/{room_id}/price-rules")
async def create_room_price_rule(
    room_id: str,
    payload: RoomPriceRuleCreateRequest,
    request: Request,
    principal: CurrentPrincipal = Depends(require_roles("merchant_admin")),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, object]:
    room = await _load_room(session, room_id, principal)
    rule = RoomPriceRule(tenant_id=room.tenant_id, room_id=room.id, **payload.model_dump())
    session.add(rule)
    await session.flush()
    await write_audit_log(
        session,
        tenant_id=room.tenant_id,
        actor_id=principal.user_id,
        action="room_price_rule.create",
        target_type="room_price_rule",
        target_id=rule.id,
        request_id=getattr(request.state, "request_id", None),
        ip_address=request.client.host if request.client else None,
        payload=payload.model_dump(mode="json"),
    )
    await session.commit()
    return ok(RoomPriceRuleResponse.model_validate(rule).model_dump(mode="json"), request)


@router.post("/{room_id}/blocked-slots")
async def create_room_blocked_slot(
    room_id: str,
    payload: RoomBlockedSlotCreateRequest,
    request: Request,
    principal: CurrentPrincipal = Depends(require_roles("merchant_admin")),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, object]:
    room = await _load_room(session, room_id, principal)
    slot = RoomBlockedSlot(tenant_id=room.tenant_id, room_id=room.id, **payload.model_dump())
    session.add(slot)
    await session.flush()
    await write_audit_log(
        session,
        tenant_id=room.tenant_id,
        actor_id=principal.user_id,
        action="room_blocked_slot.create",
        target_type="room_blocked_slot",
        target_id=slot.id,
        request_id=getattr(request.state, "request_id", None),
        ip_address=request.client.host if request.client else None,
        payload=payload.model_dump(mode="json"),
    )
    await session.commit()
    return ok(RoomBlockedSlotResponse.model_validate(slot).model_dump(mode="json"), request)
