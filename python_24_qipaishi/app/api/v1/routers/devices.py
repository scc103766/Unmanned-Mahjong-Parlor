from typing import Optional

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import CurrentPrincipal, get_db_session, require_roles
from app.core.errors import AppError
from app.core.responses import ok
from app.modules.audit.service import write_audit_log
from app.modules.devices.models import Device, DeviceCommand
from app.modules.devices.schemas import (
    DeviceAdminCommandRequest,
    DeviceCommandResponse,
    DeviceCreateRequest,
    DeviceResponse,
)
from app.modules.devices.service import (
    execute_device_command,
    retry_device_command,
    validate_device_scope,
)

router = APIRouter()
commands_router = APIRouter()


def _tenant_id(principal: CurrentPrincipal) -> str:
    if principal.tenant_id is None:
        raise AppError(
            "TENANT_REQUIRED",
            "A tenant-scoped identity is required.",
            status.HTTP_403_FORBIDDEN,
        )
    return principal.tenant_id


@router.get("")
async def list_devices(
    request: Request,
    store_id: Optional[str] = Query(default=None),
    room_id: Optional[str] = Query(default=None),
    device_type: Optional[str] = Query(default=None),
    principal: CurrentPrincipal = Depends(require_roles("merchant_admin", "clerk", "support")),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, object]:
    query = select(Device).where(Device.tenant_id == _tenant_id(principal))
    if store_id is not None:
        query = query.where(Device.store_id == store_id)
    if room_id is not None:
        query = query.where(Device.room_id == room_id)
    if device_type is not None:
        query = query.where(Device.device_type == device_type)
    rows = (await session.scalars(query.order_by(Device.created_at.desc()))).all()
    return ok([DeviceResponse.model_validate(row).model_dump(mode="json") for row in rows], request)


@router.post("")
async def create_device(
    payload: DeviceCreateRequest,
    request: Request,
    principal: CurrentPrincipal = Depends(require_roles("merchant_admin", "clerk")),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, object]:
    tenant_id = _tenant_id(principal)
    await validate_device_scope(
        session,
        tenant_id=tenant_id,
        store_id=payload.store_id,
        room_id=payload.room_id,
    )
    row = Device(tenant_id=tenant_id, **payload.model_dump())
    session.add(row)
    await session.flush()
    await write_audit_log(
        session,
        tenant_id=tenant_id,
        actor_id=principal.user_id,
        action="device.create",
        target_type="device",
        target_id=row.id,
        request_id=getattr(request.state, "request_id", None),
        ip_address=request.client.host if request.client else None,
        payload=payload.model_dump(mode="json"),
    )
    await session.commit()
    return ok(DeviceResponse.model_validate(row).model_dump(mode="json"), request)


async def _load_device(session: AsyncSession, *, device_id: str, tenant_id: str) -> Device:
    row = await session.get(Device, device_id)
    if row is None or row.tenant_id != tenant_id:
        raise AppError("DEVICE_NOT_FOUND", "Device was not found.", status.HTTP_404_NOT_FOUND)
    return row


async def _execute_admin_device_command(
    *,
    session: AsyncSession,
    request: Request,
    principal: CurrentPrincipal,
    device_id: str,
    payload: DeviceAdminCommandRequest,
    command: str,
    action: str,
) -> dict[str, object]:
    device = await _load_device(session, device_id=device_id, tenant_id=_tenant_id(principal))
    row = await execute_device_command(
        session,
        device=device,
        actor_id=principal.user_id,
        command=command,
        biz_type="device_admin",
        biz_id=device.id,
        idempotency_key=payload.idempotency_key,
        request_payload={"device_id": device.id, "command": command, "source": "admin"},
    )
    await write_audit_log(
        session,
        tenant_id=device.tenant_id,
        actor_id=principal.user_id,
        action=action,
        target_type="device_command",
        target_id=row.id,
        request_id=getattr(request.state, "request_id", None),
        ip_address=request.client.host if request.client else None,
        payload=payload.model_dump(mode="json"),
    )
    await session.commit()
    return ok(DeviceCommandResponse.model_validate(row).model_dump(mode="json"), request)


@router.post("/{device_id}/test")
async def test_device(
    device_id: str,
    payload: DeviceAdminCommandRequest,
    request: Request,
    principal: CurrentPrincipal = Depends(require_roles("merchant_admin", "clerk", "support")),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, object]:
    return await _execute_admin_device_command(
        session=session,
        request=request,
        principal=principal,
        device_id=device_id,
        payload=payload,
        command="test",
        action="device.test",
    )


@router.post("/{device_id}/open")
async def open_device(
    device_id: str,
    payload: DeviceAdminCommandRequest,
    request: Request,
    principal: CurrentPrincipal = Depends(require_roles("merchant_admin", "clerk", "support")),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, object]:
    return await _execute_admin_device_command(
        session=session,
        request=request,
        principal=principal,
        device_id=device_id,
        payload=payload,
        command="open",
        action="device.open",
    )


@router.post("/{device_id}/close")
async def close_device(
    device_id: str,
    payload: DeviceAdminCommandRequest,
    request: Request,
    principal: CurrentPrincipal = Depends(require_roles("merchant_admin", "clerk", "support")),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, object]:
    return await _execute_admin_device_command(
        session=session,
        request=request,
        principal=principal,
        device_id=device_id,
        payload=payload,
        command="close",
        action="device.close",
    )


@commands_router.get("")
async def list_device_commands(
    request: Request,
    device_id: Optional[str] = Query(default=None),
    status_value: Optional[str] = Query(default=None, alias="status"),
    principal: CurrentPrincipal = Depends(require_roles("merchant_admin", "clerk", "support")),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, object]:
    query = select(DeviceCommand).where(DeviceCommand.tenant_id == _tenant_id(principal))
    if device_id is not None:
        query = query.where(DeviceCommand.device_id == device_id)
    if status_value is not None:
        query = query.where(DeviceCommand.status == status_value)
    rows = (await session.scalars(query.order_by(DeviceCommand.created_at.desc()))).all()
    return ok(
        [DeviceCommandResponse.model_validate(row).model_dump(mode="json") for row in rows],
        request,
    )


@commands_router.post("/{command_id}/retry")
async def retry_command(
    command_id: str,
    request: Request,
    principal: CurrentPrincipal = Depends(require_roles("merchant_admin", "clerk", "support")),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, object]:
    row = await retry_device_command(
        session,
        command_id=command_id,
        tenant_id=_tenant_id(principal),
    )
    await write_audit_log(
        session,
        tenant_id=row.tenant_id,
        actor_id=principal.user_id,
        action="device_command.retry",
        target_type="device_command",
        target_id=row.id,
        request_id=getattr(request.state, "request_id", None),
        ip_address=request.client.host if request.client else None,
        payload={},
    )
    await session.commit()
    return ok(DeviceCommandResponse.model_validate(row).model_dump(mode="json"), request)
