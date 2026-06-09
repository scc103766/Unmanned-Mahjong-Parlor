from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import CurrentPrincipal, get_current_principal, get_db_session
from app.core.responses import ok
from app.modules.auth.service import build_principal_response, load_principal

router = APIRouter()


@router.get("/me")
async def me(
    request: Request,
    principal: CurrentPrincipal = Depends(get_current_principal),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, object]:
    data = await load_principal(session, principal.user_id)
    return ok(build_principal_response(data).model_dump(), request)
