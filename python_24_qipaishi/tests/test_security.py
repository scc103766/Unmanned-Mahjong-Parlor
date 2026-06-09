import time

import pytest

from app.core.errors import AppError
from app.core.security import create_access_token, decode_access_token


def test_access_token_round_trip() -> None:
    token = create_access_token(
        user_id="user_1",
        tenant_id="tenant_1",
        roles=["customer", "merchant_admin"],
        store_ids=["store_2", "store_1"],
        secret="secret",
        ttl_seconds=60,
    )

    claims = decode_access_token(token, secret="secret")

    assert claims.subject == "user_1"
    assert claims.tenant_id == "tenant_1"
    assert claims.roles == ["customer", "merchant_admin"]
    assert claims.store_ids == ["store_1", "store_2"]
    assert claims.expires_at > int(time.time())


def test_access_token_rejects_tampering() -> None:
    token = create_access_token(
        user_id="user_1",
        tenant_id=None,
        roles=["platform_admin"],
        store_ids=[],
        secret="secret",
        ttl_seconds=60,
    )
    tampered = token[:-1] + ("a" if token[-1] != "a" else "b")

    with pytest.raises(AppError) as exc_info:
        decode_access_token(tampered, secret="secret")

    assert exc_info.value.code == "AUTH_TOKEN_INVALID"


def test_access_token_rejects_expired_token() -> None:
    token = create_access_token(
        user_id="user_1",
        tenant_id=None,
        roles=["platform_admin"],
        store_ids=[],
        secret="secret",
        ttl_seconds=-1,
    )

    with pytest.raises(AppError) as exc_info:
        decode_access_token(token, secret="secret")

    assert exc_info.value.code == "AUTH_TOKEN_EXPIRED"
