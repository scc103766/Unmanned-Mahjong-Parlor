from collections.abc import Sequence
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import false, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.audit.models import AuditLog
from app.modules.availability.service import utc_now
from app.modules.cleaning.models import CleaningTask
from app.modules.cleaning.service import is_cleaning_task_overdue
from app.modules.devices.models import Device, DeviceCommand
from app.modules.operations.schemas import AuditLogResponse, OperationExceptionResponse
from app.modules.payments.models import Payment, Refund
from app.modules.withdrawals.models import Withdrawal

PAYMENT_STUCK_MINUTES = 30
REFUND_STUCK_MINUTES = 60
WITHDRAWAL_STUCK_HOURS = 24


def build_operation_exceptions(
    *,
    payments: Sequence[Payment],
    refunds: Sequence[Refund],
    withdrawals: Sequence[Withdrawal],
    device_commands: Sequence[DeviceCommand],
    devices: Sequence[Device],
    cleaning_tasks: Sequence[CleaningTask],
    now: Optional[datetime] = None,
) -> list[OperationExceptionResponse]:
    now = now or utc_now()
    device_store_by_id = {device.id: device.store_id for device in devices}
    exceptions: list[OperationExceptionResponse] = []
    for payment in payments:
        if payment.status == "paying" and payment.created_at <= now - timedelta(
            minutes=PAYMENT_STUCK_MINUTES
        ):
            exceptions.append(
                OperationExceptionResponse(
                    id=f"payment:{payment.id}",
                    tenant_id=payment.tenant_id,
                    source="payment",
                    severity="warning",
                    entity_type="payment",
                    entity_id=payment.id,
                    status=payment.status,
                    message="Payment has stayed in paying status too long.",
                    occurred_at=payment.created_at,
                    payload={"order_id": payment.order_id, "amount": str(payment.amount)},
                )
            )
    for refund in refunds:
        if refund.status == "failed" or (
            refund.status == "created"
            and refund.created_at <= now - timedelta(minutes=REFUND_STUCK_MINUTES)
        ):
            exceptions.append(
                OperationExceptionResponse(
                    id=f"refund:{refund.id}",
                    tenant_id=refund.tenant_id,
                    source="refund",
                    severity="error" if refund.status == "failed" else "warning",
                    entity_type="refund",
                    entity_id=refund.id,
                    status=refund.status,
                    message="Refund requires manual attention.",
                    occurred_at=refund.created_at,
                    payload={"order_id": refund.order_id, "amount": str(refund.amount)},
                )
            )
    for withdrawal in withdrawals:
        is_stuck = withdrawal.created_at <= now - timedelta(hours=WITHDRAWAL_STUCK_HOURS)
        if withdrawal.status in {"pending", "approved"} and is_stuck:
            exceptions.append(
                OperationExceptionResponse(
                    id=f"withdrawal:{withdrawal.id}",
                    tenant_id=withdrawal.tenant_id,
                    source="withdrawal",
                    severity="warning",
                    entity_type="withdrawal",
                    entity_id=withdrawal.id,
                    status=withdrawal.status,
                    message="Withdrawal requires manual follow-up.",
                    occurred_at=withdrawal.created_at,
                    payload={"user_id": withdrawal.user_id, "amount": str(withdrawal.amount)},
                )
            )
    for command in device_commands:
        if command.status == "failed":
            exceptions.append(
                OperationExceptionResponse(
                    id=f"device_command:{command.id}",
                    tenant_id=command.tenant_id,
                    store_id=device_store_by_id.get(command.device_id),
                    source="device",
                    severity="error",
                    entity_type="device_command",
                    entity_id=command.id,
                    status=command.status,
                    message=command.failure_reason or "Device command failed.",
                    occurred_at=command.executed_at or command.created_at,
                    payload={
                        "device_id": command.device_id,
                        "command": command.command,
                        "biz_type": command.biz_type,
                        "biz_id": command.biz_id,
                    },
                )
            )
    for task in cleaning_tasks:
        if is_cleaning_task_overdue(task, now=now):
            exceptions.append(
                OperationExceptionResponse(
                    id=f"cleaning_task:{task.id}",
                    tenant_id=task.tenant_id,
                    store_id=task.store_id,
                    source="cleaning",
                    severity="warning",
                    entity_type="cleaning_task",
                    entity_id=task.id,
                    status=task.status,
                    message="Cleaning task is overdue.",
                    occurred_at=task.scheduled_end_at or task.created_at,
                    payload={"room_id": task.room_id, "order_id": task.order_id},
                )
            )
        if task.status == "complained":
            exceptions.append(
                OperationExceptionResponse(
                    id=f"cleaning_complaint:{task.id}",
                    tenant_id=task.tenant_id,
                    store_id=task.store_id,
                    source="cleaning",
                    severity="error",
                    entity_type="cleaning_task",
                    entity_id=task.id,
                    status=task.status,
                    message=task.complaint_reason or "Cleaning task was complained.",
                    occurred_at=task.complained_at or task.created_at,
                    payload={"room_id": task.room_id, "order_id": task.order_id},
                )
            )
    return sorted(exceptions, key=lambda item: item.occurred_at, reverse=True)


async def list_operation_exceptions(
    session: AsyncSession,
    *,
    tenant_id: Optional[str],
    store_id: Optional[str],
    source: Optional[str],
    start_at: datetime,
    end_at: datetime,
) -> list[OperationExceptionResponse]:
    payment_query = select(Payment).where(
        Payment.created_at >= start_at,
        Payment.created_at < end_at,
    )
    refund_query = select(Refund).where(Refund.created_at >= start_at, Refund.created_at < end_at)
    withdrawal_query = select(Withdrawal).where(
        Withdrawal.created_at >= start_at,
        Withdrawal.created_at < end_at,
    )
    device_query = select(DeviceCommand).where(
        DeviceCommand.created_at >= start_at,
        DeviceCommand.created_at < end_at,
    )
    cleaning_query = select(CleaningTask).where(
        CleaningTask.created_at >= start_at,
        CleaningTask.created_at < end_at,
    )
    device_meta_query = select(Device)
    if tenant_id is not None:
        payment_query = payment_query.where(Payment.tenant_id == tenant_id)
        refund_query = refund_query.where(Refund.tenant_id == tenant_id)
        withdrawal_query = withdrawal_query.where(Withdrawal.tenant_id == tenant_id)
        device_query = device_query.where(DeviceCommand.tenant_id == tenant_id)
        cleaning_query = cleaning_query.where(CleaningTask.tenant_id == tenant_id)
        device_meta_query = device_meta_query.where(Device.tenant_id == tenant_id)
    if store_id is not None:
        cleaning_query = cleaning_query.where(CleaningTask.store_id == store_id)
        device_meta_query = device_meta_query.where(Device.store_id == store_id)

    devices = list((await session.scalars(device_meta_query)).all())
    if store_id is not None:
        device_ids = [device.id for device in devices]
        if device_ids:
            device_query = device_query.where(DeviceCommand.device_id.in_(device_ids))
        else:
            device_query = device_query.where(false())

    payments = []
    refunds = []
    withdrawals = []
    device_commands = []
    cleaning_tasks = []
    if source in {None, "payment"}:
        payments = list((await session.scalars(payment_query)).all())
    if source in {None, "refund"}:
        refunds = list((await session.scalars(refund_query)).all())
    if source in {None, "withdrawal"}:
        withdrawals = list((await session.scalars(withdrawal_query)).all())
    if source in {None, "device"}:
        device_commands = list((await session.scalars(device_query)).all())
    if source in {None, "cleaning"}:
        cleaning_tasks = list((await session.scalars(cleaning_query)).all())

    exceptions = build_operation_exceptions(
        payments=payments,
        refunds=refunds,
        withdrawals=withdrawals,
        device_commands=device_commands,
        devices=devices,
        cleaning_tasks=cleaning_tasks,
    )
    return exceptions


async def list_audit_logs(
    session: AsyncSession,
    *,
    tenant_id: Optional[str],
    actor_id: Optional[str],
    action: Optional[str],
    target_type: Optional[str],
    start_at: datetime,
    end_at: datetime,
    limit: int,
) -> list[AuditLogResponse]:
    query = select(AuditLog).where(AuditLog.created_at >= start_at, AuditLog.created_at < end_at)
    if tenant_id is not None:
        query = query.where(AuditLog.tenant_id == tenant_id)
    if actor_id is not None:
        query = query.where(AuditLog.actor_id == actor_id)
    if action is not None:
        query = query.where(AuditLog.action == action)
    if target_type is not None:
        query = query.where(AuditLog.target_type == target_type)
    rows = (
        await session.scalars(query.order_by(AuditLog.created_at.desc()).limit(limit))
    ).all()
    return [AuditLogResponse.model_validate(row) for row in rows]
