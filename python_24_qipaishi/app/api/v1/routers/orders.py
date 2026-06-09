from fastapi import APIRouter, Depends, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import CurrentPrincipal, get_db_session, require_roles
from app.core.errors import AppError
from app.core.responses import ok
from app.modules.audit.service import write_audit_log
from app.modules.cleaning.schemas import CleaningTaskResponse
from app.modules.cleaning.service import (
    create_cleaning_task_for_order,
    ensure_order_can_create_cleaning_task,
)
from app.modules.devices.schemas import DeviceCommandResponse, DeviceOrderCommandRequest
from app.modules.devices.service import execute_order_device_command
from app.modules.orders.models import Order
from app.modules.orders.schemas import (
    OrderCancelRequest,
    OrderChangeRoomQuoteRequest,
    OrderChangeRoomRequest,
    OrderCreateRequest,
    OrderExpirePendingResponse,
    OrderRenewQuoteRequest,
    OrderRenewRequest,
    OrderRescheduleQuoteRequest,
    OrderRescheduleRequest,
    PreorderRequest,
)
from app.modules.orders.service import (
    build_order_response,
    cancel_order,
    change_order_room,
    complete_order,
    create_preorder,
    expire_pending_orders,
    load_order_for_principal,
    quote_order_renewal,
    quote_order_reschedule,
    quote_order_room_change,
    renew_order,
    reschedule_order,
    transition_order_to_in_use,
    transition_order_to_paid,
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


def _can_manage_orders(principal: CurrentPrincipal) -> bool:
    return principal.has_any_role(["platform_admin", "merchant_admin", "clerk", "support"])


async def _execute_order_device_action(
    *,
    session: AsyncSession,
    request: Request,
    principal: CurrentPrincipal,
    order_id: str,
    payload: DeviceOrderCommandRequest,
    device_type: str,
    command: str,
    action: str,
) -> dict[str, object]:
    order = await load_order_for_principal(
        session,
        order_id=order_id,
        tenant_id=_tenant_id(principal),
        user_id=principal.user_id,
        can_manage_tenant=_can_manage_orders(principal),
    )
    device_command = await execute_order_device_command(
        session,
        order=order,
        actor_id=principal.user_id,
        device_type=device_type,
        command=command,
        idempotency_key=payload.idempotency_key,
    )
    await write_audit_log(
        session,
        tenant_id=order.tenant_id,
        actor_id=principal.user_id,
        action=action,
        target_type="device_command",
        target_id=device_command.id,
        request_id=getattr(request.state, "request_id", None),
        ip_address=request.client.host if request.client else None,
        payload={
            **payload.model_dump(mode="json"),
            "order_id": order.id,
            "device_id": device_command.device_id,
            "command": command,
        },
    )
    await session.commit()
    return ok(DeviceCommandResponse.model_validate(device_command).model_dump(mode="json"), request)


@router.get("")
async def list_orders(
    request: Request,
    principal: CurrentPrincipal = Depends(
        require_roles("merchant_admin", "clerk", "customer", "support")
    ),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, object]:
    tenant_id = _tenant_id(principal)
    query = select(Order).where(Order.tenant_id == tenant_id).order_by(Order.created_at.desc())
    if not _can_manage_orders(principal):
        query = query.where(Order.user_id == principal.user_id)
    orders = (await session.scalars(query)).all()
    rows = [
        (await build_order_response(session, order)).model_dump(mode="json") for order in orders
    ]
    return ok(rows, request)


@router.post("/preorder")
async def preorder(
    payload: PreorderRequest,
    request: Request,
    principal: CurrentPrincipal = Depends(require_roles("customer")),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, object]:
    tenant_id = _tenant_id(principal)
    order = await create_preorder(
        session,
        tenant_id=tenant_id,
        user_id=principal.user_id,
        room_id=payload.room_id,
        start_at=payload.start_at,
        end_at=payload.end_at,
    )
    await write_audit_log(
        session,
        tenant_id=tenant_id,
        actor_id=principal.user_id,
        action="order.preorder",
        target_type="order",
        target_id=order.id,
        request_id=getattr(request.state, "request_id", None),
        ip_address=request.client.host if request.client else None,
        payload=payload.model_dump(mode="json"),
    )
    await session.commit()
    response = await build_order_response(session, order)
    return ok(response.model_dump(mode="json"), request)


@router.post("")
async def create_order(
    payload: OrderCreateRequest,
    request: Request,
    principal: CurrentPrincipal = Depends(require_roles("customer")),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, object]:
    tenant_id = _tenant_id(principal)
    order = await create_preorder(
        session,
        tenant_id=tenant_id,
        user_id=principal.user_id,
        room_id=payload.room_id,
        start_at=payload.start_at,
        end_at=payload.end_at,
    )
    await write_audit_log(
        session,
        tenant_id=tenant_id,
        actor_id=principal.user_id,
        action="order.create",
        target_type="order",
        target_id=order.id,
        request_id=getattr(request.state, "request_id", None),
        ip_address=request.client.host if request.client else None,
        payload=payload.model_dump(mode="json"),
    )
    await session.commit()
    response = await build_order_response(session, order)
    return ok(response.model_dump(mode="json"), request)


@router.post("/expire-pending")
async def expire_pending(
    request: Request,
    principal: CurrentPrincipal = Depends(require_roles("merchant_admin", "clerk", "support")),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, object]:
    expired_orders = await expire_pending_orders(session, tenant_id=_tenant_id(principal))
    await write_audit_log(
        session,
        tenant_id=_tenant_id(principal),
        actor_id=principal.user_id,
        action="order.expire_pending",
        target_type="order",
        request_id=getattr(request.state, "request_id", None),
        ip_address=request.client.host if request.client else None,
        payload={"expired_order_ids": [order.id for order in expired_orders]},
    )
    await session.commit()
    return ok(
        OrderExpirePendingResponse(
            expired_order_ids=[order.id for order in expired_orders]
        ).model_dump(mode="json"),
        request,
    )


@router.get("/{order_id}")
async def get_order(
    order_id: str,
    request: Request,
    principal: CurrentPrincipal = Depends(
        require_roles("merchant_admin", "clerk", "customer", "support")
    ),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, object]:
    order = await load_order_for_principal(
        session,
        order_id=order_id,
        tenant_id=_tenant_id(principal),
        user_id=principal.user_id,
        can_manage_tenant=_can_manage_orders(principal),
    )
    response = await build_order_response(session, order)
    return ok(response.model_dump(mode="json"), request)


@router.post("/{order_id}/renew/quote")
async def renew_quote(
    order_id: str,
    payload: OrderRenewQuoteRequest,
    request: Request,
    principal: CurrentPrincipal = Depends(
        require_roles("merchant_admin", "clerk", "customer", "support")
    ),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, object]:
    order = await load_order_for_principal(
        session,
        order_id=order_id,
        tenant_id=_tenant_id(principal),
        user_id=principal.user_id,
        can_manage_tenant=_can_manage_orders(principal),
    )
    quote = await quote_order_renewal(session, order=order, new_end_at=payload.new_end_at)
    return ok(quote.model_dump(mode="json"), request)


@router.post("/{order_id}/renew")
async def renew(
    order_id: str,
    payload: OrderRenewRequest,
    request: Request,
    principal: CurrentPrincipal = Depends(
        require_roles("merchant_admin", "clerk", "customer", "support")
    ),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, object]:
    order = await load_order_for_principal(
        session,
        order_id=order_id,
        tenant_id=_tenant_id(principal),
        user_id=principal.user_id,
        can_manage_tenant=_can_manage_orders(principal),
    )
    renewal_quote = await renew_order(session, order=order, new_end_at=payload.new_end_at)
    await write_audit_log(
        session,
        tenant_id=order.tenant_id,
        actor_id=principal.user_id,
        action="order.renew",
        target_type="order",
        target_id=order.id,
        request_id=getattr(request.state, "request_id", None),
        ip_address=request.client.host if request.client else None,
        payload=renewal_quote.model_dump(mode="json"),
    )
    await session.commit()
    response = await build_order_response(session, order)
    return ok(response.model_dump(mode="json"), request)


@router.post("/{order_id}/change-room/quote")
async def change_room_quote(
    order_id: str,
    payload: OrderChangeRoomQuoteRequest,
    request: Request,
    principal: CurrentPrincipal = Depends(
        require_roles("merchant_admin", "clerk", "customer", "support")
    ),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, object]:
    order = await load_order_for_principal(
        session,
        order_id=order_id,
        tenant_id=_tenant_id(principal),
        user_id=principal.user_id,
        can_manage_tenant=_can_manage_orders(principal),
    )
    quote = await quote_order_room_change(session, order=order, new_room_id=payload.new_room_id)
    return ok(quote.model_dump(mode="json"), request)


@router.post("/{order_id}/change-room")
async def change_room(
    order_id: str,
    payload: OrderChangeRoomRequest,
    request: Request,
    principal: CurrentPrincipal = Depends(
        require_roles("merchant_admin", "clerk", "customer", "support")
    ),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, object]:
    order = await load_order_for_principal(
        session,
        order_id=order_id,
        tenant_id=_tenant_id(principal),
        user_id=principal.user_id,
        can_manage_tenant=_can_manage_orders(principal),
    )
    change_quote = await change_order_room(session, order=order, new_room_id=payload.new_room_id)
    await write_audit_log(
        session,
        tenant_id=order.tenant_id,
        actor_id=principal.user_id,
        action="order.change_room",
        target_type="order",
        target_id=order.id,
        request_id=getattr(request.state, "request_id", None),
        ip_address=request.client.host if request.client else None,
        payload=change_quote.model_dump(mode="json"),
    )
    await session.commit()
    response = await build_order_response(session, order)
    return ok(response.model_dump(mode="json"), request)


@router.post("/{order_id}/reschedule/quote")
async def reschedule_quote(
    order_id: str,
    payload: OrderRescheduleQuoteRequest,
    request: Request,
    principal: CurrentPrincipal = Depends(
        require_roles("merchant_admin", "clerk", "support")
    ),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, object]:
    order = await load_order_for_principal(
        session,
        order_id=order_id,
        tenant_id=_tenant_id(principal),
        user_id=principal.user_id,
        can_manage_tenant=True,
    )
    quote = await quote_order_reschedule(
        session,
        order=order,
        new_start_at=payload.start_at,
        new_end_at=payload.end_at,
    )
    return ok(quote.model_dump(mode="json"), request)


@router.post("/{order_id}/reschedule")
async def reschedule(
    order_id: str,
    payload: OrderRescheduleRequest,
    request: Request,
    principal: CurrentPrincipal = Depends(
        require_roles("merchant_admin", "clerk", "support")
    ),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, object]:
    order = await load_order_for_principal(
        session,
        order_id=order_id,
        tenant_id=_tenant_id(principal),
        user_id=principal.user_id,
        can_manage_tenant=True,
    )
    reschedule_quote = await reschedule_order(
        session,
        order=order,
        new_start_at=payload.start_at,
        new_end_at=payload.end_at,
    )
    await write_audit_log(
        session,
        tenant_id=order.tenant_id,
        actor_id=principal.user_id,
        action="order.reschedule",
        target_type="order",
        target_id=order.id,
        request_id=getattr(request.state, "request_id", None),
        ip_address=request.client.host if request.client else None,
        payload=reschedule_quote.model_dump(mode="json"),
    )
    await session.commit()
    response = await build_order_response(session, order)
    return ok(response.model_dump(mode="json"), request)


@router.post("/{order_id}/cancel")
async def cancel(
    order_id: str,
    payload: OrderCancelRequest,
    request: Request,
    principal: CurrentPrincipal = Depends(
        require_roles("merchant_admin", "clerk", "customer", "support")
    ),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, object]:
    order = await load_order_for_principal(
        session,
        order_id=order_id,
        tenant_id=_tenant_id(principal),
        user_id=principal.user_id,
        can_manage_tenant=_can_manage_orders(principal),
    )
    was_started = order.status == "in_use" or order.started_at is not None
    await cancel_order(session, order, reason=payload.reason)
    cleaning_task = None
    if was_started:
        cleaning_task = await create_cleaning_task_for_order(session, order=order)
    await write_audit_log(
        session,
        tenant_id=order.tenant_id,
        actor_id=principal.user_id,
        action="order.cancel",
        target_type="order",
        target_id=order.id,
        request_id=getattr(request.state, "request_id", None),
        ip_address=request.client.host if request.client else None,
        payload={
            **payload.model_dump(),
            "cleaning_task_id": cleaning_task.id if cleaning_task is not None else None,
        },
    )
    await session.commit()
    response = await build_order_response(session, order)
    return ok(response.model_dump(mode="json"), request)


@router.post("/{order_id}/mock-pay")
async def mock_pay(
    order_id: str,
    request: Request,
    principal: CurrentPrincipal = Depends(
        require_roles("merchant_admin", "clerk", "customer", "support")
    ),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, object]:
    order = await load_order_for_principal(
        session,
        order_id=order_id,
        tenant_id=_tenant_id(principal),
        user_id=principal.user_id,
        can_manage_tenant=_can_manage_orders(principal),
    )
    await transition_order_to_paid(session, order)
    await write_audit_log(
        session,
        tenant_id=order.tenant_id,
        actor_id=principal.user_id,
        action="order.mock_pay",
        target_type="order",
        target_id=order.id,
        request_id=getattr(request.state, "request_id", None),
        ip_address=request.client.host if request.client else None,
        payload={},
    )
    await session.commit()
    response = await build_order_response(session, order)
    return ok(response.model_dump(mode="json"), request)


@router.post("/{order_id}/start")
async def start_order(
    order_id: str,
    request: Request,
    principal: CurrentPrincipal = Depends(
        require_roles("merchant_admin", "clerk", "customer", "support")
    ),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, object]:
    order = await load_order_for_principal(
        session,
        order_id=order_id,
        tenant_id=_tenant_id(principal),
        user_id=principal.user_id,
        can_manage_tenant=_can_manage_orders(principal),
    )
    await transition_order_to_in_use(session, order)
    await write_audit_log(
        session,
        tenant_id=order.tenant_id,
        actor_id=principal.user_id,
        action="order.start",
        target_type="order",
        target_id=order.id,
        request_id=getattr(request.state, "request_id", None),
        ip_address=request.client.host if request.client else None,
        payload={},
    )
    await session.commit()
    response = await build_order_response(session, order)
    return ok(response.model_dump(mode="json"), request)


@router.post("/{order_id}/complete")
async def complete(
    order_id: str,
    request: Request,
    principal: CurrentPrincipal = Depends(require_roles("merchant_admin", "clerk", "support")),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, object]:
    order = await load_order_for_principal(
        session,
        order_id=order_id,
        tenant_id=_tenant_id(principal),
        user_id=principal.user_id,
        can_manage_tenant=True,
    )
    await complete_order(session, order)
    cleaning_task = await create_cleaning_task_for_order(session, order=order)
    await write_audit_log(
        session,
        tenant_id=order.tenant_id,
        actor_id=principal.user_id,
        action="order.complete",
        target_type="order",
        target_id=order.id,
        request_id=getattr(request.state, "request_id", None),
        ip_address=request.client.host if request.client else None,
        payload={"cleaning_task_id": cleaning_task.id},
    )
    await session.commit()
    response = await build_order_response(session, order)
    return ok(response.model_dump(mode="json"), request)


@router.post("/{order_id}/cleaning-task")
async def trigger_cleaning_task(
    order_id: str,
    request: Request,
    principal: CurrentPrincipal = Depends(require_roles("merchant_admin", "clerk", "support")),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, object]:
    order = await load_order_for_principal(
        session,
        order_id=order_id,
        tenant_id=_tenant_id(principal),
        user_id=principal.user_id,
        can_manage_tenant=True,
    )
    ensure_order_can_create_cleaning_task(order)
    cleaning_task = await create_cleaning_task_for_order(session, order=order)
    await write_audit_log(
        session,
        tenant_id=order.tenant_id,
        actor_id=principal.user_id,
        action="order.trigger_cleaning_task",
        target_type="cleaning_task",
        target_id=cleaning_task.id,
        request_id=getattr(request.state, "request_id", None),
        ip_address=request.client.host if request.client else None,
        payload={"order_id": order.id},
    )
    await session.commit()
    return ok(CleaningTaskResponse.model_validate(cleaning_task).model_dump(mode="json"), request)


@router.post("/{order_id}/open-store-door")
async def open_store_door(
    order_id: str,
    payload: DeviceOrderCommandRequest,
    request: Request,
    principal: CurrentPrincipal = Depends(
        require_roles("merchant_admin", "clerk", "customer", "support")
    ),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, object]:
    return await _execute_order_device_action(
        session=session,
        request=request,
        principal=principal,
        order_id=order_id,
        payload=payload,
        device_type="store_door",
        command="open",
        action="order.open_store_door",
    )


@router.post("/{order_id}/open-room-door")
async def open_room_door(
    order_id: str,
    payload: DeviceOrderCommandRequest,
    request: Request,
    principal: CurrentPrincipal = Depends(
        require_roles("merchant_admin", "clerk", "customer", "support")
    ),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, object]:
    return await _execute_order_device_action(
        session=session,
        request=request,
        principal=principal,
        order_id=order_id,
        payload=payload,
        device_type="room_door",
        command="open",
        action="order.open_room_door",
    )


@router.post("/{order_id}/open-room-lock")
async def open_room_lock(
    order_id: str,
    payload: DeviceOrderCommandRequest,
    request: Request,
    principal: CurrentPrincipal = Depends(
        require_roles("merchant_admin", "clerk", "customer", "support")
    ),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, object]:
    return await _execute_order_device_action(
        session=session,
        request=request,
        principal=principal,
        order_id=order_id,
        payload=payload,
        device_type="room_lock",
        command="unlock",
        action="order.open_room_lock",
    )


@router.post("/{order_id}/power-on")
async def power_on(
    order_id: str,
    payload: DeviceOrderCommandRequest,
    request: Request,
    principal: CurrentPrincipal = Depends(
        require_roles("merchant_admin", "clerk", "customer", "support")
    ),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, object]:
    return await _execute_order_device_action(
        session=session,
        request=request,
        principal=principal,
        order_id=order_id,
        payload=payload,
        device_type="power",
        command="power_on",
        action="order.power_on",
    )
