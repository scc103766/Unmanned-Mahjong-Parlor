from typing import Any


async def check_redis(settings: Any) -> dict[str, str]:
    if not settings.health_check_redis:
        return {"status": "skipped"}

    try:
        from redis.asyncio import Redis

        client = Redis.from_url(settings.redis_url, encoding="utf-8", decode_responses=True)
        await client.ping()
    except ModuleNotFoundError as exc:
        return {"status": "unavailable", "error": exc.name or exc.__class__.__name__}
    except Exception as exc:  # pragma: no cover - depends on external service
        return {"status": "down", "error": exc.__class__.__name__}
    finally:
        if "client" in locals():
            await client.aclose()

    return {"status": "ok"}
