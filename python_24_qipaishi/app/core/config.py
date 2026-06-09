import os
from dataclasses import dataclass, field
from functools import lru_cache


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.lower() in {"1", "true", "yes", "on"}


def _env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    return int(value)


def _env_list(name: str) -> list[str]:
    value = os.getenv(name, "")
    return [item.strip() for item in value.split(",") if item.strip()]


def _default_callback_signature_required() -> bool:
    return os.getenv("QIPAISHI_ENV", "dev").lower() not in {"dev", "local", "test"}


@dataclass(frozen=True)
class Settings:
    app_name: str = field(default_factory=lambda: os.getenv("QIPAISHI_APP_NAME", "Qipaishi API"))
    app_version: str = field(default_factory=lambda: os.getenv("QIPAISHI_APP_VERSION", "0.1.0"))
    env: str = field(default_factory=lambda: os.getenv("QIPAISHI_ENV", "dev"))
    api_v1_prefix: str = field(
        default_factory=lambda: os.getenv("QIPAISHI_API_V1_PREFIX", "/api/v1")
    )
    database_url: str = field(
        default_factory=lambda: os.getenv(
            "QIPAISHI_DATABASE_URL",
            "postgresql+asyncpg://qipaishi:qipaishi@localhost:5432/qipaishi",
        )
    )
    redis_url: str = field(
        default_factory=lambda: os.getenv("QIPAISHI_REDIS_URL", "redis://localhost:6379/0")
    )
    token_secret: str = field(
        default_factory=lambda: os.getenv("QIPAISHI_TOKEN_SECRET", "qipaishi-dev-token-secret")
    )
    access_token_ttl_seconds: int = field(
        default_factory=lambda: int(os.getenv("QIPAISHI_ACCESS_TOKEN_TTL_SECONDS", "86400"))
    )
    health_check_database: bool = field(
        default_factory=lambda: _env_bool("QIPAISHI_HEALTH_CHECK_DATABASE", False)
    )
    health_check_redis: bool = field(
        default_factory=lambda: _env_bool("QIPAISHI_HEALTH_CHECK_REDIS", False)
    )
    payment_callback_secret: str = field(
        default_factory=lambda: os.getenv(
            "QIPAISHI_PAYMENT_CALLBACK_SECRET",
            "qipaishi-dev-payment-callback-secret",
        )
    )
    payment_callback_signature_required: bool = field(
        default_factory=lambda: _env_bool(
            "QIPAISHI_PAYMENT_CALLBACK_SIGNATURE_REQUIRED",
            _default_callback_signature_required(),
        )
    )
    payment_callback_tolerance_seconds: int = field(
        default_factory=lambda: _env_int("QIPAISHI_PAYMENT_CALLBACK_TOLERANCE_SECONDS", 300)
    )
    cors_origins: list[str] = field(default_factory=lambda: _env_list("QIPAISHI_CORS_ORIGINS"))
    log_level: str = field(default_factory=lambda: os.getenv("QIPAISHI_LOG_LEVEL", "INFO"))


@lru_cache
def get_settings() -> Settings:
    return Settings()
