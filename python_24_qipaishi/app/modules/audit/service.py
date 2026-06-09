from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.audit.models import AuditLog


async def write_audit_log(
    session: AsyncSession,
    *,
    action: str,
    target_type: str,
    tenant_id: Optional[str] = None,
    actor_id: Optional[str] = None,
    target_id: Optional[str] = None,
    request_id: Optional[str] = None,
    ip_address: Optional[str] = None,
    payload: Optional[dict[str, object]] = None,
) -> AuditLog:
    row = AuditLog(
        tenant_id=tenant_id,
        actor_id=actor_id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        request_id=request_id,
        ip_address=ip_address,
        payload=payload or {},
    )
    session.add(row)
    await session.flush()
    return row
