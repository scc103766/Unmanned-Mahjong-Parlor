from fastapi import APIRouter, Depends, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import CurrentPrincipal, get_db_session, require_roles
from app.core.errors import AppError
from app.core.responses import ok
from app.modules.audit.service import write_audit_log
from app.modules.tenancy.models import Tenant, TenantApp
from app.modules.tenancy.schemas import (
    TenantAppCreateRequest,
    TenantAppResponse,
    TenantCreateRequest,
    TenantResponse,
    TenantUpdateRequest,
)

router = APIRouter()


@router.get("")
async def list_tenants(
    request: Request,
    _: CurrentPrincipal = Depends(require_roles("platform_admin", "support")),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, object]:
    tenants = (await session.scalars(select(Tenant).order_by(Tenant.created_at.desc()))).all()
    return ok([TenantResponse.model_validate(row).model_dump() for row in tenants], request)


@router.post("")
async def create_tenant(
    payload: TenantCreateRequest,
    request: Request,
    principal: CurrentPrincipal = Depends(require_roles("platform_admin")),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, object]:
    tenant = Tenant(
        name=payload.name,
        status=payload.status,
        plan=payload.plan,
        settings=payload.settings,
    )
    session.add(tenant)
    await session.flush()
    await write_audit_log(
        session,
        tenant_id=tenant.id,
        actor_id=principal.user_id,
        action="tenant.create",
        target_type="tenant",
        target_id=tenant.id,
        request_id=getattr(request.state, "request_id", None),
        ip_address=request.client.host if request.client else None,
        payload=payload.model_dump(),
    )
    await session.commit()
    return ok(TenantResponse.model_validate(tenant).model_dump(), request)


@router.get("/current")
async def current_tenant(
    request: Request,
    principal: CurrentPrincipal = Depends(
        require_roles("merchant_admin", "clerk", "cleaner", "customer")
    ),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, object]:
    if principal.tenant_id is None:
        raise AppError(
            "TENANT_REQUIRED",
            "A tenant-scoped identity is required.",
            status.HTTP_403_FORBIDDEN,
        )
    tenant = await session.get(Tenant, principal.tenant_id)
    if tenant is None:
        raise AppError("TENANT_NOT_FOUND", "Tenant was not found.", status.HTTP_404_NOT_FOUND)
    return ok(TenantResponse.model_validate(tenant).model_dump(), request)


@router.get("/{tenant_id}")
async def get_tenant(
    tenant_id: str,
    request: Request,
    principal: CurrentPrincipal = Depends(
        require_roles("platform_admin", "merchant_admin", "support")
    ),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, object]:
    if not principal.has_role("platform_admin") and principal.tenant_id != tenant_id:
        raise AppError("FORBIDDEN", "Cannot access another tenant.", status.HTTP_403_FORBIDDEN)
    tenant = await session.get(Tenant, tenant_id)
    if tenant is None:
        raise AppError("TENANT_NOT_FOUND", "Tenant was not found.", status.HTTP_404_NOT_FOUND)
    return ok(TenantResponse.model_validate(tenant).model_dump(), request)


@router.patch("/{tenant_id}")
async def update_tenant(
    tenant_id: str,
    payload: TenantUpdateRequest,
    request: Request,
    principal: CurrentPrincipal = Depends(require_roles("platform_admin", "merchant_admin")),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, object]:
    if not principal.has_role("platform_admin") and principal.tenant_id != tenant_id:
        raise AppError("FORBIDDEN", "Cannot update another tenant.", status.HTTP_403_FORBIDDEN)
    tenant = await session.get(Tenant, tenant_id)
    if tenant is None:
        raise AppError("TENANT_NOT_FOUND", "Tenant was not found.", status.HTTP_404_NOT_FOUND)

    changes = payload.model_dump(exclude_unset=True)
    for key, value in changes.items():
        setattr(tenant, key, value)

    await write_audit_log(
        session,
        tenant_id=tenant.id,
        actor_id=principal.user_id,
        action="tenant.update",
        target_type="tenant",
        target_id=tenant.id,
        request_id=getattr(request.state, "request_id", None),
        ip_address=request.client.host if request.client else None,
        payload=changes,
    )
    await session.commit()
    return ok(TenantResponse.model_validate(tenant).model_dump(), request)


@router.get("/{tenant_id}/apps")
async def list_tenant_apps(
    tenant_id: str,
    request: Request,
    principal: CurrentPrincipal = Depends(
        require_roles("platform_admin", "merchant_admin", "support")
    ),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, object]:
    if not principal.has_role("platform_admin") and principal.tenant_id != tenant_id:
        raise AppError("FORBIDDEN", "Cannot access another tenant.", status.HTTP_403_FORBIDDEN)
    apps = (
        await session.scalars(
            select(TenantApp)
            .where(TenantApp.tenant_id == tenant_id)
            .order_by(TenantApp.created_at.desc())
        )
    ).all()
    return ok([TenantAppResponse.model_validate(row).model_dump() for row in apps], request)


@router.post("/{tenant_id}/apps")
async def create_tenant_app(
    tenant_id: str,
    payload: TenantAppCreateRequest,
    request: Request,
    principal: CurrentPrincipal = Depends(require_roles("platform_admin", "merchant_admin")),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, object]:
    if not principal.has_role("platform_admin") and principal.tenant_id != tenant_id:
        raise AppError("FORBIDDEN", "Cannot update another tenant.", status.HTTP_403_FORBIDDEN)
    tenant = await session.get(Tenant, tenant_id)
    if tenant is None:
        raise AppError("TENANT_NOT_FOUND", "Tenant was not found.", status.HTTP_404_NOT_FOUND)

    app = TenantApp(
        tenant_id=tenant_id,
        client_type=payload.client_type,
        app_id=payload.app_id,
        mch_id=payload.mch_id,
        secret_ref=payload.secret_ref,
        status=payload.status,
    )
    session.add(app)
    await session.flush()
    await write_audit_log(
        session,
        tenant_id=tenant_id,
        actor_id=principal.user_id,
        action="tenant_app.create",
        target_type="tenant_app",
        target_id=app.id,
        request_id=getattr(request.state, "request_id", None),
        ip_address=request.client.host if request.client else None,
        payload=payload.model_dump(),
    )
    await session.commit()
    return ok(TenantAppResponse.model_validate(app).model_dump(), request)
