from fastapi import APIRouter, Request

from app.api.tags import OPENAPI_TAGS
from app.core.responses import ok

router = APIRouter()


@router.get("/version")
async def version(request: Request) -> dict[str, object]:
    settings = request.app.state.settings
    return ok(
        {
            "name": settings.app_name,
            "version": settings.app_version,
            "environment": settings.env,
        },
        request,
    )


@router.get("/openapi-tags")
async def openapi_tags(request: Request) -> dict[str, object]:
    return ok(OPENAPI_TAGS, request)

