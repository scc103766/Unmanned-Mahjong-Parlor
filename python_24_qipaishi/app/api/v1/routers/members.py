from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import CurrentPrincipal, get_db_session, require_roles
from app.core.errors import AppError
from app.core.responses import ok
from app.modules.members.schemas import MemberListResponse
from app.modules.members.service import list_member_summaries, load_member_detail
from app.modules.users.models import User

router = APIRouter()


def _tenant_id(principal: CurrentPrincipal) -> str:
    if principal.tenant_id is None:
        raise AppError(
            "TENANT_REQUIRED",
            "A tenant-scoped identity is required.",
            status.HTTP_403_FORBIDDEN,
        )
    return principal.tenant_id


@router.get("")
async def list_members(
    request: Request,
    limit: int = Query(default=100, ge=1, le=500),
    principal: CurrentPrincipal = Depends(require_roles("merchant_admin", "clerk", "support")),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, object]:
    rows = await list_member_summaries(session, tenant_id=_tenant_id(principal), limit=limit)
    return ok(MemberListResponse(members=rows).model_dump(mode="json"), request)


@router.get("/{user_id}")
async def get_member(
    user_id: str,
    request: Request,
    principal: CurrentPrincipal = Depends(require_roles("merchant_admin", "clerk", "support")),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, object]:
    user = await session.get(User, user_id)
    if user is None or user.tenant_id != _tenant_id(principal):
        raise AppError("USER_NOT_FOUND", "User was not found.", status.HTTP_404_NOT_FOUND)
    response = await load_member_detail(session, tenant_id=_tenant_id(principal), user=user)
    return ok(response.model_dump(mode="json"), request)
