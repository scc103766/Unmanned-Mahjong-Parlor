from dataclasses import dataclass
from typing import Optional

from fastapi import status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.errors import AppError
from app.core.security import create_access_token
from app.modules.auth.schemas import (
    DevBootstrapRequest,
    PrincipalResponse,
    TokenResponse,
    WechatLoginRequest,
)
from app.modules.tenancy.models import Tenant, TenantApp
from app.modules.users.models import Role, User, UserRole, UserStoreScope

STANDARD_ROLES = {
    "platform_admin": "平台管理员",
    "merchant_admin": "商家管理员",
    "clerk": "店员",
    "cleaner": "保洁员",
    "customer": "顾客",
    "support": "客服",
}


@dataclass(frozen=True)
class PrincipalData:
    user: User
    roles: list[str]
    store_ids: list[str]


async def ensure_standard_roles(session: AsyncSession) -> None:
    existing = set((await session.scalars(select(Role.code))).all())
    for code, name in STANDARD_ROLES.items():
        if code not in existing:
            scope = "platform" if code == "platform_admin" else "tenant"
            session.add(Role(code=code, name=name, scope=scope))
    await session.flush()


async def _role_by_code(session: AsyncSession, code: str) -> Role:
    role = await session.scalar(select(Role).where(Role.code == code))
    if role is None:
        await ensure_standard_roles(session)
        role = await session.scalar(select(Role).where(Role.code == code))
    if role is None:
        raise AppError("ROLE_NOT_FOUND", f"Role {code} is not configured.")
    return role


async def grant_role(
    session: AsyncSession,
    *,
    tenant_id: Optional[str],
    user_id: str,
    role_code: str,
) -> None:
    role = await _role_by_code(session, role_code)
    existing = await session.scalar(
        select(UserRole).where(
            UserRole.tenant_id == tenant_id,
            UserRole.user_id == user_id,
            UserRole.role_id == role.id,
        )
    )
    if existing is None:
        session.add(UserRole(tenant_id=tenant_id, user_id=user_id, role_id=role.id))
        await session.flush()


async def replace_user_roles(
    session: AsyncSession,
    *,
    tenant_id: Optional[str],
    user_id: str,
    role_codes: list[str],
) -> None:
    roles = (await session.scalars(select(Role).where(Role.code.in_(role_codes)))).all()
    found_codes = {role.code for role in roles}
    missing_codes = set(role_codes) - found_codes
    if missing_codes:
        raise AppError(
            "ROLE_NOT_FOUND",
            "Some roles are not configured.",
            details={"roles": sorted(missing_codes)},
        )

    existing = (
        await session.scalars(
            select(UserRole).where(UserRole.tenant_id == tenant_id, UserRole.user_id == user_id)
        )
    ).all()
    for row in existing:
        await session.delete(row)
    for role in roles:
        session.add(UserRole(tenant_id=tenant_id, user_id=user_id, role_id=role.id))
    await session.flush()


async def replace_store_scopes(
    session: AsyncSession,
    *,
    tenant_id: str,
    user_id: str,
    store_ids: list[str],
) -> None:
    existing = (
        await session.scalars(
            select(UserStoreScope).where(
                UserStoreScope.tenant_id == tenant_id,
                UserStoreScope.user_id == user_id,
            )
        )
    ).all()
    for row in existing:
        await session.delete(row)
    for store_id in sorted(set(store_ids)):
        session.add(UserStoreScope(tenant_id=tenant_id, user_id=user_id, store_id=store_id))
    await session.flush()


async def load_principal(session: AsyncSession, user_id: str) -> PrincipalData:
    user = await session.get(User, user_id)
    if user is None or user.status != "active":
        raise AppError("AUTH_USER_DISABLED", "User is not available.", status.HTTP_401_UNAUTHORIZED)

    role_rows = (
        await session.execute(
            select(Role.code)
            .join(UserRole, UserRole.role_id == Role.id)
            .where(UserRole.user_id == user.id)
            .where((UserRole.tenant_id == user.tenant_id) | (UserRole.tenant_id.is_(None)))
        )
    ).all()
    scope_rows = (
        await session.execute(
            select(UserStoreScope.store_id).where(
                UserStoreScope.tenant_id == user.tenant_id,
                UserStoreScope.user_id == user.id,
            )
        )
    ).all()
    return PrincipalData(
        user=user,
        roles=sorted({row[0] for row in role_rows}),
        store_ids=sorted({row[0] for row in scope_rows}),
    )


def build_principal_response(data: PrincipalData) -> PrincipalResponse:
    return PrincipalResponse(
        user_id=data.user.id,
        tenant_id=data.user.tenant_id,
        phone=data.user.phone,
        nickname=data.user.nickname,
        roles=data.roles,
        store_ids=data.store_ids,
    )


def issue_token(data: PrincipalData, settings: Settings) -> TokenResponse:
    access_token = create_access_token(
        user_id=data.user.id,
        tenant_id=data.user.tenant_id,
        roles=data.roles,
        store_ids=data.store_ids,
        secret=settings.token_secret,
        ttl_seconds=settings.access_token_ttl_seconds,
    )
    return TokenResponse(
        access_token=access_token,
        expires_in=settings.access_token_ttl_seconds,
        user=build_principal_response(data),
    )


async def login_with_wechat_mock(
    session: AsyncSession,
    *,
    payload: WechatLoginRequest,
    settings: Settings,
) -> TokenResponse:
    tenant_app = await session.scalar(
        select(TenantApp).where(
            TenantApp.client_type == payload.client_type,
            TenantApp.app_id == payload.app_id,
            TenantApp.status == "active",
        )
    )
    if tenant_app is None:
        raise AppError(
            "TENANT_APP_NOT_FOUND",
            "Tenant application binding was not found.",
            status.HTTP_404_NOT_FOUND,
        )

    await ensure_standard_roles(session)
    openid = f"mock:{payload.app_id}:{payload.code}"
    user = await session.scalar(
        select(User).where(User.tenant_id == tenant_app.tenant_id, User.openid == openid)
    )
    if user is None:
        user = User(
            tenant_id=tenant_app.tenant_id,
            openid=openid,
            phone=payload.phone,
            nickname=payload.nickname,
            avatar_url=payload.avatar_url,
        )
        session.add(user)
        await session.flush()
        await grant_role(
            session,
            tenant_id=tenant_app.tenant_id,
            user_id=user.id,
            role_code="customer",
        )
    else:
        user.phone = payload.phone or user.phone
        user.nickname = payload.nickname or user.nickname
        user.avatar_url = payload.avatar_url or user.avatar_url

    await session.commit()
    data = await load_principal(session, user.id)
    return issue_token(data, settings)


async def dev_bootstrap(
    session: AsyncSession,
    *,
    payload: DevBootstrapRequest,
    settings: Settings,
) -> TokenResponse:
    if settings.env == "prod":
        raise AppError(
            "BOOTSTRAP_DISABLED",
            "Development bootstrap is disabled in production.",
            status.HTTP_403_FORBIDDEN,
        )

    await ensure_standard_roles(session)
    tenant_app = await session.scalar(
        select(TenantApp).where(
            TenantApp.client_type == payload.client_type,
            TenantApp.app_id == payload.app_id,
        )
    )
    if tenant_app is None:
        tenant = Tenant(name=payload.tenant_name, plan="dev", settings={})
        session.add(tenant)
        await session.flush()
        tenant_app = TenantApp(
            tenant_id=tenant.id,
            client_type=payload.client_type,
            app_id=payload.app_id,
            status="active",
        )
        session.add(tenant_app)
        await session.flush()
    else:
        existing_tenant = await session.get(Tenant, tenant_app.tenant_id)
        if existing_tenant is None:
            raise AppError("TENANT_NOT_FOUND", "Tenant application points to a missing tenant.")

    openid = f"dev:{payload.app_id}:{payload.phone or payload.nickname or 'admin'}"
    user = await session.scalar(
        select(User).where(User.tenant_id == tenant_app.tenant_id, User.openid == openid)
    )
    if user is None:
        user = User(
            tenant_id=tenant_app.tenant_id,
            openid=openid,
            phone=payload.phone,
            nickname=payload.nickname,
        )
        session.add(user)
        await session.flush()

    await grant_role(session, tenant_id=None, user_id=user.id, role_code="platform_admin")
    await grant_role(
        session,
        tenant_id=tenant_app.tenant_id,
        user_id=user.id,
        role_code="merchant_admin",
    )
    await session.commit()

    data = await load_principal(session, user.id)
    return issue_token(data, settings)
