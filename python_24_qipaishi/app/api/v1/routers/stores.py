from typing import Optional

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import CurrentPrincipal, get_db_session, require_roles
from app.core.errors import AppError
from app.core.responses import ok
from app.modules.audit.service import write_audit_log
from app.modules.stores.models import Store
from app.modules.stores.schemas import StoreCreateRequest, StoreResponse, StoreUpdateRequest

router = APIRouter()


def _resolve_read_tenant(principal: CurrentPrincipal, tenant_id: Optional[str]) -> Optional[str]:
    if principal.has_role("platform_admin"):
        return tenant_id
    return principal.tenant_id


def _require_tenant(principal: CurrentPrincipal) -> str:
    if principal.tenant_id is None:
        raise AppError(
            "TENANT_REQUIRED",
            "A tenant-scoped identity is required.",
            status.HTTP_403_FORBIDDEN,
        )
    return principal.tenant_id


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


@router.get("")
async def list_stores(
    request: Request,
    tenant_id: Optional[str] = Query(default=None),
    principal: CurrentPrincipal = Depends(
        require_roles("merchant_admin", "clerk", "cleaner", "customer", "support")
    ),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, object]:
    query = select(Store).order_by(Store.sort_order, Store.created_at.desc())
    resolved_tenant_id = _resolve_read_tenant(principal, tenant_id)
    if resolved_tenant_id is not None:
        query = query.where(Store.tenant_id == resolved_tenant_id)
    stores = (await session.scalars(query)).all()
    return ok(
        [StoreResponse.model_validate(store).model_dump(mode="json") for store in stores],
        request,
    )


@router.post("")
async def create_store(
    payload: StoreCreateRequest,
    request: Request,
    principal: CurrentPrincipal = Depends(require_roles("merchant_admin")),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, object]:
    tenant_id = _require_tenant(principal)
    store = Store(tenant_id=tenant_id, **payload.model_dump())
    session.add(store)
    await session.flush()
    await write_audit_log(
        session,
        tenant_id=tenant_id,
        actor_id=principal.user_id,
        action="store.create",
        target_type="store",
        target_id=store.id,
        request_id=getattr(request.state, "request_id", None),
        ip_address=request.client.host if request.client else None,
        payload=payload.model_dump(),
    )
    await session.commit()
    return ok(StoreResponse.model_validate(store).model_dump(mode="json"), request)


@router.get("/{store_id}")
async def get_store(
    store_id: str,
    request: Request,
    principal: CurrentPrincipal = Depends(
        require_roles("merchant_admin", "clerk", "cleaner", "customer", "support")
    ),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, object]:
    store = await _load_store(session, store_id, principal)
    return ok(StoreResponse.model_validate(store).model_dump(mode="json"), request)


@router.patch("/{store_id}")
async def update_store(
    store_id: str,
    payload: StoreUpdateRequest,
    request: Request,
    principal: CurrentPrincipal = Depends(require_roles("merchant_admin")),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, object]:
    store = await _load_store(session, store_id, principal)
    changes = payload.model_dump(exclude_unset=True)
    for key, value in changes.items():
        setattr(store, key, value)

    await write_audit_log(
        session,
        tenant_id=store.tenant_id,
        actor_id=principal.user_id,
        action="store.update",
        target_type="store",
        target_id=store.id,
        request_id=getattr(request.state, "request_id", None),
        ip_address=request.client.host if request.client else None,
        payload=changes,
    )
    await session.commit()
    return ok(StoreResponse.model_validate(store).model_dump(mode="json"), request)
