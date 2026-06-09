import base64
import hashlib
import hmac
import json
import time
from dataclasses import dataclass
from typing import Any, Optional

from fastapi import status

from app.core.errors import AppError


@dataclass(frozen=True)
class TokenClaims:
    subject: str
    tenant_id: Optional[str]
    roles: list[str]
    store_ids: list[str]
    issued_at: int
    expires_at: int


def _b64encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _b64decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode((value + padding).encode("ascii"))


def _json_b64(data: dict[str, Any]) -> str:
    return _b64encode(json.dumps(data, separators=(",", ":"), sort_keys=True).encode("utf-8"))


def _signature(signing_input: str, secret: str) -> str:
    digest = hmac.new(
        secret.encode("utf-8"),
        signing_input.encode("ascii"),
        hashlib.sha256,
    ).digest()
    return _b64encode(digest)


def create_access_token(
    *,
    user_id: str,
    tenant_id: Optional[str],
    roles: list[str],
    store_ids: list[str],
    secret: str,
    ttl_seconds: int,
) -> str:
    issued_at = int(time.time())
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "sub": user_id,
        "tenant_id": tenant_id,
        "roles": sorted(set(roles)),
        "store_ids": sorted(set(store_ids)),
        "iat": issued_at,
        "exp": issued_at + ttl_seconds,
        "typ": "access",
    }
    signing_input = f"{_json_b64(header)}.{_json_b64(payload)}"
    return f"{signing_input}.{_signature(signing_input, secret)}"


def decode_access_token(token: str, *, secret: str) -> TokenClaims:
    try:
        header_part, payload_part, signature_part = token.split(".")
    except ValueError as exc:
        raise AppError(
            "AUTH_TOKEN_INVALID",
            "Access token format is invalid.",
            status.HTTP_401_UNAUTHORIZED,
        ) from exc

    signing_input = f"{header_part}.{payload_part}"
    expected_signature = _signature(signing_input, secret)
    if not hmac.compare_digest(expected_signature, signature_part):
        raise AppError(
            "AUTH_TOKEN_INVALID",
            "Access token signature is invalid.",
            status.HTTP_401_UNAUTHORIZED,
        )

    try:
        header = json.loads(_b64decode(header_part))
        payload = json.loads(_b64decode(payload_part))
    except (ValueError, json.JSONDecodeError) as exc:
        raise AppError(
            "AUTH_TOKEN_INVALID",
            "Access token payload is invalid.",
            status.HTTP_401_UNAUTHORIZED,
        ) from exc

    if header.get("alg") != "HS256" or payload.get("typ") != "access":
        raise AppError(
            "AUTH_TOKEN_INVALID",
            "Access token type is invalid.",
            status.HTTP_401_UNAUTHORIZED,
        )

    expires_at = int(payload.get("exp") or 0)
    if expires_at < int(time.time()):
        raise AppError(
            "AUTH_TOKEN_EXPIRED",
            "Access token has expired.",
            status.HTTP_401_UNAUTHORIZED,
        )

    subject = payload.get("sub")
    if not isinstance(subject, str) or not subject:
        raise AppError(
            "AUTH_TOKEN_INVALID",
            "Access token subject is invalid.",
            status.HTTP_401_UNAUTHORIZED,
        )

    return TokenClaims(
        subject=subject,
        tenant_id=payload.get("tenant_id"),
        roles=list(payload.get("roles") or []),
        store_ids=list(payload.get("store_ids") or []),
        issued_at=int(payload.get("iat") or 0),
        expires_at=expires_at,
    )
