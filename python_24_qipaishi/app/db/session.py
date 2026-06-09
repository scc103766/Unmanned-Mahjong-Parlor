from functools import lru_cache
from typing import Any

from app.core.config import get_settings


@lru_cache
def get_engine(database_url: str) -> Any:
    from sqlalchemy.ext.asyncio import create_async_engine

    return create_async_engine(database_url, pool_pre_ping=True)


def async_session() -> Any:
    from sqlalchemy.ext.asyncio import async_sessionmaker

    settings = get_settings()
    return async_sessionmaker(get_engine(settings.database_url), expire_on_commit=False)


async def check_database(settings: Any) -> dict[str, str]:
    if not settings.health_check_database:
        return {"status": "skipped"}

    try:
        from sqlalchemy import text

        engine = get_engine(settings.database_url)
        async with engine.connect() as connection:
            await connection.execute(text("select 1"))
    except ModuleNotFoundError as exc:
        return {"status": "unavailable", "error": exc.name or exc.__class__.__name__}
    except Exception as exc:  # pragma: no cover - depends on external service
        return {"status": "down", "error": exc.__class__.__name__}

    return {"status": "ok"}
