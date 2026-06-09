from fastapi import APIRouter, Depends, Request, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import CurrentPrincipal, get_db_session, require_roles
from app.core.errors import AppError
from app.core.responses import ok
from app.modules.audit.service import write_audit_log
from app.modules.cleaning.models import CleaningTask
from app.modules.cleaning.schemas import (
    CleaningSummaryResponse,
    CleaningTaskCancelRequest,
    CleaningTaskComplainRequest,
    CleaningTaskCompleteRequest,
    CleaningTaskReassignRequest,
    CleaningTaskResponse,
    CleaningTaskReviewRequest,
    CleaningTaskSettleRequest,
)
from app.modules.cleaning.service import (
    accept_cleaning_task,
    cancel_cleaning_task,
    complain_cleaning_task,
    complete_cleaning_task,
    execute_cleaning_open_door,
    is_cleaning_task_overdue,
    load_cleaning_task,
    mark_room_clean_after_approval,
    reassign_cleaning_task,
    review_cleaning_task,
    settle_cleaning_task,
    start_cleaning_task,
    unaccept_cleaning_task,
)
from app.modules.devices.schemas import DeviceCommandResponse, DeviceOrderCommandRequest

router = APIRouter()


def _tenant_id(principal: CurrentPrincipal) -> str:
    if principal.tenant_id is None:
        raise AppError(
            "TENANT_REQUIRED",
            "A tenant-scoped identity is required.",
            status.HTTP_403_FORBIDDEN,
        )
    return principal.tenant_id


def _can_manage_cleaning(principal: CurrentPrincipal) -> bool:
    return principal.has_any_role(["platform_admin", "merchant_admin", "clerk", "support"])


@router.get("/tasks")
async def list_tasks(
    request: Request,
    principal: CurrentPrincipal = Depends(
        require_roles("merchant_admin", "clerk", "cleaner", "support")
    ),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, object]:
    query = select(CleaningTask).where(CleaningTask.tenant_id == _tenant_id(principal))
    if not _can_manage_cleaning(principal):
        query = query.where(
            or_(
                CleaningTask.status == "pending",
                CleaningTask.cleaner_id == principal.user_id,
            )
        )
    rows = (await session.scalars(query.order_by(CleaningTask.created_at.desc()))).all()
    return ok(
        [CleaningTaskResponse.model_validate(row).model_dump(mode="json") for row in rows],
        request,
    )


@router.get("/summary")
async def cleaning_summary(
    request: Request,
    principal: CurrentPrincipal = Depends(require_roles("merchant_admin", "clerk", "support")),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, object]:
    rows = (
        await session.scalars(
            select(CleaningTask).where(CleaningTask.tenant_id == _tenant_id(principal))
        )
    ).all()
    overdue_task_ids = [row.id for row in rows if is_cleaning_task_overdue(row)]
    response = CleaningSummaryResponse(
        pending_count=sum(1 for row in rows if row.status == "pending"),
        overdue_count=len(overdue_task_ids),
        in_progress_count=sum(1 for row in rows if row.status == "in_progress"),
        complained_count=sum(1 for row in rows if row.status == "complained"),
        overdue_task_ids=overdue_task_ids,
    )
    return ok(response.model_dump(mode="json"), request)


@router.post("/tasks/{task_id}/accept")
async def accept_task(
    task_id: str,
    request: Request,
    principal: CurrentPrincipal = Depends(require_roles("cleaner")),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, object]:
    task = await load_cleaning_task(session, task_id=task_id, tenant_id=_tenant_id(principal))
    accept_cleaning_task(task, cleaner_id=principal.user_id)
    await write_audit_log(
        session,
        tenant_id=task.tenant_id,
        actor_id=principal.user_id,
        action="cleaning.accept",
        target_type="cleaning_task",
        target_id=task.id,
        request_id=getattr(request.state, "request_id", None),
        ip_address=request.client.host if request.client else None,
        payload={},
    )
    await session.commit()
    return ok(CleaningTaskResponse.model_validate(task).model_dump(mode="json"), request)


@router.post("/tasks/{task_id}/unaccept")
async def unaccept_task(
    task_id: str,
    request: Request,
    principal: CurrentPrincipal = Depends(require_roles("cleaner")),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, object]:
    task = await load_cleaning_task(session, task_id=task_id, tenant_id=_tenant_id(principal))
    unaccept_cleaning_task(task, cleaner_id=principal.user_id)
    await write_audit_log(
        session,
        tenant_id=task.tenant_id,
        actor_id=principal.user_id,
        action="cleaning.unaccept",
        target_type="cleaning_task",
        target_id=task.id,
        request_id=getattr(request.state, "request_id", None),
        ip_address=request.client.host if request.client else None,
        payload={},
    )
    await session.commit()
    return ok(CleaningTaskResponse.model_validate(task).model_dump(mode="json"), request)


@router.post("/tasks/{task_id}/start")
async def start_task(
    task_id: str,
    request: Request,
    principal: CurrentPrincipal = Depends(require_roles("cleaner")),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, object]:
    task = await load_cleaning_task(session, task_id=task_id, tenant_id=_tenant_id(principal))
    start_cleaning_task(task, cleaner_id=principal.user_id)
    await write_audit_log(
        session,
        tenant_id=task.tenant_id,
        actor_id=principal.user_id,
        action="cleaning.start",
        target_type="cleaning_task",
        target_id=task.id,
        request_id=getattr(request.state, "request_id", None),
        ip_address=request.client.host if request.client else None,
        payload={},
    )
    await session.commit()
    return ok(CleaningTaskResponse.model_validate(task).model_dump(mode="json"), request)


@router.post("/tasks/{task_id}/open-door")
async def open_task_door(
    task_id: str,
    payload: DeviceOrderCommandRequest,
    request: Request,
    principal: CurrentPrincipal = Depends(require_roles("cleaner")),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, object]:
    task = await load_cleaning_task(session, task_id=task_id, tenant_id=_tenant_id(principal))
    command = await execute_cleaning_open_door(
        session,
        task=task,
        cleaner_id=principal.user_id,
        idempotency_key=payload.idempotency_key,
    )
    await write_audit_log(
        session,
        tenant_id=task.tenant_id,
        actor_id=principal.user_id,
        action="cleaning.open_door",
        target_type="device_command",
        target_id=command.id,
        request_id=getattr(request.state, "request_id", None),
        ip_address=request.client.host if request.client else None,
        payload={**payload.model_dump(mode="json"), "task_id": task.id},
    )
    await session.commit()
    return ok(DeviceCommandResponse.model_validate(command).model_dump(mode="json"), request)


@router.post("/tasks/{task_id}/complete")
async def complete_task(
    task_id: str,
    payload: CleaningTaskCompleteRequest,
    request: Request,
    principal: CurrentPrincipal = Depends(require_roles("cleaner")),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, object]:
    task = await load_cleaning_task(session, task_id=task_id, tenant_id=_tenant_id(principal))
    task = await complete_cleaning_task(
        session,
        task=task,
        cleaner_id=principal.user_id,
        image_urls=payload.image_urls,
        remark=payload.remark,
    )
    await write_audit_log(
        session,
        tenant_id=task.tenant_id,
        actor_id=principal.user_id,
        action="cleaning.complete",
        target_type="cleaning_task",
        target_id=task.id,
        request_id=getattr(request.state, "request_id", None),
        ip_address=request.client.host if request.client else None,
        payload=payload.model_dump(mode="json"),
    )
    await session.commit()
    return ok(CleaningTaskResponse.model_validate(task).model_dump(mode="json"), request)


@router.post("/tasks/{task_id}/review")
async def review_task(
    task_id: str,
    payload: CleaningTaskReviewRequest,
    request: Request,
    principal: CurrentPrincipal = Depends(require_roles("merchant_admin", "clerk", "support")),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, object]:
    task = await load_cleaning_task(session, task_id=task_id, tenant_id=_tenant_id(principal))
    review_cleaning_task(task, approved=payload.approved, note=payload.note)
    if payload.approved:
        await mark_room_clean_after_approval(session, task=task)
    await write_audit_log(
        session,
        tenant_id=task.tenant_id,
        actor_id=principal.user_id,
        action="cleaning.review",
        target_type="cleaning_task",
        target_id=task.id,
        request_id=getattr(request.state, "request_id", None),
        ip_address=request.client.host if request.client else None,
        payload=payload.model_dump(mode="json"),
    )
    await session.commit()
    return ok(CleaningTaskResponse.model_validate(task).model_dump(mode="json"), request)


@router.post("/tasks/{task_id}/cancel")
async def cancel_task(
    task_id: str,
    payload: CleaningTaskCancelRequest,
    request: Request,
    principal: CurrentPrincipal = Depends(require_roles("merchant_admin", "clerk", "support")),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, object]:
    task = await load_cleaning_task(session, task_id=task_id, tenant_id=_tenant_id(principal))
    cancel_cleaning_task(task, reason=payload.reason)
    await write_audit_log(
        session,
        tenant_id=task.tenant_id,
        actor_id=principal.user_id,
        action="cleaning.cancel",
        target_type="cleaning_task",
        target_id=task.id,
        request_id=getattr(request.state, "request_id", None),
        ip_address=request.client.host if request.client else None,
        payload=payload.model_dump(mode="json"),
    )
    await session.commit()
    return ok(CleaningTaskResponse.model_validate(task).model_dump(mode="json"), request)


@router.post("/tasks/{task_id}/reassign")
async def reassign_task(
    task_id: str,
    payload: CleaningTaskReassignRequest,
    request: Request,
    principal: CurrentPrincipal = Depends(require_roles("merchant_admin", "clerk", "support")),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, object]:
    task = await load_cleaning_task(session, task_id=task_id, tenant_id=_tenant_id(principal))
    reassign_cleaning_task(task, note=payload.note)
    await write_audit_log(
        session,
        tenant_id=task.tenant_id,
        actor_id=principal.user_id,
        action="cleaning.reassign",
        target_type="cleaning_task",
        target_id=task.id,
        request_id=getattr(request.state, "request_id", None),
        ip_address=request.client.host if request.client else None,
        payload=payload.model_dump(mode="json"),
    )
    await session.commit()
    return ok(CleaningTaskResponse.model_validate(task).model_dump(mode="json"), request)


@router.post("/tasks/{task_id}/complain")
async def complain_task(
    task_id: str,
    payload: CleaningTaskComplainRequest,
    request: Request,
    principal: CurrentPrincipal = Depends(require_roles("merchant_admin", "clerk", "support")),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, object]:
    task = await load_cleaning_task(session, task_id=task_id, tenant_id=_tenant_id(principal))
    complain_cleaning_task(task, reason=payload.reason)
    await write_audit_log(
        session,
        tenant_id=task.tenant_id,
        actor_id=principal.user_id,
        action="cleaning.complain",
        target_type="cleaning_task",
        target_id=task.id,
        request_id=getattr(request.state, "request_id", None),
        ip_address=request.client.host if request.client else None,
        payload=payload.model_dump(mode="json"),
    )
    await session.commit()
    return ok(CleaningTaskResponse.model_validate(task).model_dump(mode="json"), request)


@router.post("/tasks/{task_id}/settle")
async def settle_task(
    task_id: str,
    payload: CleaningTaskSettleRequest,
    request: Request,
    principal: CurrentPrincipal = Depends(require_roles("merchant_admin", "clerk", "support")),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, object]:
    task = await load_cleaning_task(session, task_id=task_id, tenant_id=_tenant_id(principal))
    settle_cleaning_task(task, amount=payload.amount, note=payload.note)
    await write_audit_log(
        session,
        tenant_id=task.tenant_id,
        actor_id=principal.user_id,
        action="cleaning.settle",
        target_type="cleaning_task",
        target_id=task.id,
        request_id=getattr(request.state, "request_id", None),
        ip_address=request.client.host if request.client else None,
        payload=payload.model_dump(mode="json"),
    )
    await session.commit()
    return ok(CleaningTaskResponse.model_validate(task).model_dump(mode="json"), request)
