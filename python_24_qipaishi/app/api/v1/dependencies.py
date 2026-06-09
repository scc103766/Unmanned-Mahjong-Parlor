from collections.abc import AsyncGenerator
from dataclasses import dataclass
from typing import Any, Callable, Optional

from fastapi import Depends, Header, Path, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.errors import AppError
from app.core.security import decode_access_token
from app.db.session import async_session
from app.modules.auth.service import load_principal


def get_app_settings() -> Settings:
    return get_settings()


async def get_db_session() -> AsyncGenerator[Any, None]:
    session_factory = async_session()
    async with session_factory() as session:
        yield session


@dataclass(frozen=True)
class CurrentPrincipal:
    user_id: str
    tenant_id: Optional[str]
    roles: list[str]
    store_ids: list[str]

    def has_role(self, role_code: str) -> bool:
        return role_code in self.roles

    def has_any_role(self, role_codes: list[str]) -> bool:
        return bool(set(role_codes) & set(self.roles))


async def get_current_principal(
    authorization: Optional[str] = Header(default=None),
    settings: Settings = Depends(get_app_settings),
    session: AsyncSession = Depends(get_db_session),
) -> CurrentPrincipal:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise AppError(
            "AUTH_REQUIRED",
            "Authorization bearer token is required.",
            status.HTTP_401_UNAUTHORIZED,
        )

    token = authorization.split(" ", 1)[1].strip()
    claims = decode_access_token(token, secret=settings.token_secret)
    principal_data = await load_principal(session, claims.subject)
    user = principal_data.user
    if claims.tenant_id != user.tenant_id:
        raise AppError(
            "AUTH_TOKEN_INVALID",
            "Access token tenant does not match the current user.",
            status.HTTP_401_UNAUTHORIZED,
        )

    return CurrentPrincipal(
        user_id=user.id,
        tenant_id=user.tenant_id,
        roles=principal_data.roles,
        store_ids=principal_data.store_ids,
    )


def require_roles(*role_codes: str, allow_platform_admin: bool = True) -> Callable[..., Any]:
    async def dependency(
        principal: CurrentPrincipal = Depends(get_current_principal),
    ) -> CurrentPrincipal:
        if allow_platform_admin and principal.has_role("platform_admin"):
            return principal
        if not principal.has_any_role(list(role_codes)):
            raise AppError(
                "FORBIDDEN",
                "Current user does not have permission for this operation.",
                status.HTTP_403_FORBIDDEN,
                details={"required_roles": list(role_codes)},
            )
        return principal

    return dependency


async def require_tenant_principal(
    principal: CurrentPrincipal = Depends(get_current_principal),
) -> CurrentPrincipal:
    if principal.tenant_id is None:
        raise AppError(
            "TENANT_REQUIRED",
            "A tenant-scoped identity is required.",
            status.HTTP_403_FORBIDDEN,
        )
    return principal


async def require_store_scope(
    store_id: str = Path(...),
    principal: CurrentPrincipal = Depends(require_roles("merchant_admin", "clerk", "cleaner")),
) -> CurrentPrincipal:
    if principal.has_role("platform_admin") or principal.has_role("merchant_admin"):
        return principal
    if store_id not in principal.store_ids:
        raise AppError(
            "STORE_SCOPE_FORBIDDEN",
            "Current user is not allowed to access this store.",
            status.HTTP_403_FORBIDDEN,
            details={"store_id": store_id},
        )
    return principal
