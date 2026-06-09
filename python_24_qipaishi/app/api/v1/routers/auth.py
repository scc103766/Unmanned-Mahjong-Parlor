from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import (
    CurrentPrincipal,
    get_app_settings,
    get_current_principal,
    get_db_session,
)
from app.core.config import Settings
from app.core.responses import ok
from app.modules.audit.service import write_audit_log
from app.modules.auth.schemas import DevBootstrapRequest, WechatLoginRequest
from app.modules.auth.service import (
    build_principal_response,
    dev_bootstrap,
    load_principal,
    login_with_wechat_mock,
)

router = APIRouter()


@router.post("/wechat-login")
async def wechat_login(
    payload: WechatLoginRequest,
    request: Request,
    settings: Settings = Depends(get_app_settings),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, object]:
    token = await login_with_wechat_mock(session, payload=payload, settings=settings)
    await write_audit_log(
        session,
        tenant_id=token.user.tenant_id,
        actor_id=token.user.user_id,
        action="auth.wechat_login",
        target_type="user",
        target_id=token.user.user_id,
        request_id=getattr(request.state, "request_id", None),
        ip_address=request.client.host if request.client else None,
        payload={"client_type": payload.client_type, "app_id": payload.app_id},
    )
    await session.commit()
    return ok(token.model_dump(), request)


@router.post("/dev-bootstrap")
async def bootstrap_dev_identity(
    payload: DevBootstrapRequest,
    request: Request,
    settings: Settings = Depends(get_app_settings),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, object]:
    token = await dev_bootstrap(session, payload=payload, settings=settings)
    await write_audit_log(
        session,
        tenant_id=token.user.tenant_id,
        actor_id=token.user.user_id,
        action="auth.dev_bootstrap",
        target_type="tenant",
        target_id=token.user.tenant_id,
        request_id=getattr(request.state, "request_id", None),
        ip_address=request.client.host if request.client else None,
        payload={"client_type": payload.client_type, "app_id": payload.app_id},
    )
    await session.commit()
    return ok(token.model_dump(), request)


@router.get("/me")
async def me(
    request: Request,
    principal: CurrentPrincipal = Depends(get_current_principal),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, object]:
    data = await load_principal(session, principal.user_id)
    return ok(build_principal_response(data).model_dump(), request)
