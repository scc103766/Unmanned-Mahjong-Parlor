from fastapi import APIRouter, Request

from app.core.responses import ok
from app.db.session import check_database
from app.providers.redis_client import check_redis

router = APIRouter()


@router.get("/health")
async def health(request: Request) -> dict[str, object]:
    settings = request.app.state.settings
    checks = {
        "api": {"status": "ok"},
        "database": await check_database(settings),
        "redis": await check_redis(settings),
    }
    overall = "ok"
    if any(check["status"] == "down" for check in checks.values()):
        overall = "degraded"

    return ok(
        {
            "status": overall,
            "service": settings.app_name,
            "version": settings.app_version,
            "environment": settings.env,
            "checks": checks,
        },
        request,
    )

