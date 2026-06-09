from fastapi import APIRouter, Depends, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import CurrentPrincipal, get_db_session, require_roles
from app.core.errors import AppError
from app.core.responses import ok
from app.modules.audit.service import write_audit_log
from app.modules.auth.service import (
    load_principal,
    replace_store_scopes,
    replace_user_roles,
)
from app.modules.users.models import Role, User
from app.modules.users.schemas import (
    RoleAssignmentRequest,
    RoleResponse,
    StoreScopeAssignmentRequest,
    UserResponse,
)

roles_router = APIRouter()
users_router = APIRouter()


@roles_router.get("")
async def list_roles(
    request: Request,
    _: CurrentPrincipal = Depends(
        require_roles("platform_admin", "merchant_admin", "support")
    ),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, object]:
    roles = (await session.scalars(select(Role).order_by(Role.code))).all()
    return ok([RoleResponse.model_validate(role).model_dump() for role in roles], request)


@users_router.get("")
async def list_users(
    request: Request,
    principal: CurrentPrincipal = Depends(
        require_roles("platform_admin", "merchant_admin", "support")
    ),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, object]:
    query = select(User).order_by(User.created_at.desc())
    if not principal.has_role("platform_admin"):
        query = query.where(User.tenant_id == principal.tenant_id)
    users = (await session.scalars(query)).all()

    rows = []
    for user in users:
        data = await load_principal(session, user.id)
        response = UserResponse.model_validate(user).model_copy(
            update={"roles": data.roles, "store_ids": data.store_ids}
        )
        rows.append(response.model_dump())
    return ok(rows, request)


@users_router.get("/{user_id}")
async def get_user(
    user_id: str,
    request: Request,
    principal: CurrentPrincipal = Depends(
        require_roles("platform_admin", "merchant_admin", "support")
    ),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, object]:
    user = await session.get(User, user_id)
    if user is None:
        raise AppError("USER_NOT_FOUND", "User was not found.", status.HTTP_404_NOT_FOUND)
    if not principal.has_role("platform_admin") and principal.tenant_id != user.tenant_id:
        raise AppError("FORBIDDEN", "Cannot access another tenant user.", status.HTTP_403_FORBIDDEN)
    data = await load_principal(session, user.id)
    response = UserResponse.model_validate(user).model_copy(
        update={"roles": data.roles, "store_ids": data.store_ids}
    )
    return ok(response.model_dump(), request)


@users_router.put("/{user_id}/roles")
async def set_user_roles(
    user_id: str,
    payload: RoleAssignmentRequest,
    request: Request,
    principal: CurrentPrincipal = Depends(require_roles("platform_admin", "merchant_admin")),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, object]:
    user = await session.get(User, user_id)
    if user is None:
        raise AppError("USER_NOT_FOUND", "User was not found.", status.HTTP_404_NOT_FOUND)
    if not principal.has_role("platform_admin") and principal.tenant_id != user.tenant_id:
        raise AppError("FORBIDDEN", "Cannot modify another tenant user.", status.HTTP_403_FORBIDDEN)

    role_tenant_id = None if "platform_admin" in payload.role_codes else user.tenant_id
    await replace_user_roles(
        session,
        tenant_id=role_tenant_id,
        user_id=user.id,
        role_codes=payload.role_codes,
    )
    await write_audit_log(
        session,
        tenant_id=user.tenant_id,
        actor_id=principal.user_id,
        action="user.roles.replace",
        target_type="user",
        target_id=user.id,
        request_id=getattr(request.state, "request_id", None),
        ip_address=request.client.host if request.client else None,
        payload=payload.model_dump(),
    )
    await session.commit()
    data = await load_principal(session, user.id)
    return ok(
        UserResponse.model_validate(user)
        .model_copy(update={"roles": data.roles, "store_ids": data.store_ids})
        .model_dump(),
        request,
    )


@users_router.put("/{user_id}/store-scopes")
async def set_user_store_scopes(
    user_id: str,
    payload: StoreScopeAssignmentRequest,
    request: Request,
    principal: CurrentPrincipal = Depends(require_roles("platform_admin", "merchant_admin")),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, object]:
    user = await session.get(User, user_id)
    if user is None:
        raise AppError("USER_NOT_FOUND", "User was not found.", status.HTTP_404_NOT_FOUND)
    if user.tenant_id is None:
        raise AppError(
            "TENANT_REQUIRED",
            "Store scopes require a tenant user.",
            status.HTTP_400_BAD_REQUEST,
        )
    if not principal.has_role("platform_admin") and principal.tenant_id != user.tenant_id:
        raise AppError("FORBIDDEN", "Cannot modify another tenant user.", status.HTTP_403_FORBIDDEN)

    await replace_store_scopes(
        session,
        tenant_id=user.tenant_id,
        user_id=user.id,
        store_ids=payload.store_ids,
    )
    await write_audit_log(
        session,
        tenant_id=user.tenant_id,
        actor_id=principal.user_id,
        action="user.store_scopes.replace",
        target_type="user",
        target_id=user.id,
        request_id=getattr(request.state, "request_id", None),
        ip_address=request.client.host if request.client else None,
        payload=payload.model_dump(),
    )
    await session.commit()
    data = await load_principal(session, user.id)
    return ok(
        UserResponse.model_validate(user)
        .model_copy(update={"roles": data.roles, "store_ids": data.store_ids})
        .model_dump(),
        request,
    )
