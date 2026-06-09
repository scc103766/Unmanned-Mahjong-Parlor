import hashlib
import hmac
import json
import time
from collections.abc import Mapping
from typing import Any, Optional

from fastapi import status

from app.core.errors import AppError


def canonical_callback_payload(payload: Mapping[str, Any]) -> str:
    data = {
        key: value
        for key, value in payload.items()
        if key != "signature" and value is not None
    }
    return json.dumps(data, separators=(",", ":"), sort_keys=True, ensure_ascii=True)


def sign_callback_payload(payload: Mapping[str, Any], *, secret: str) -> str:
    message = canonical_callback_payload(payload).encode("utf-8")
    return hmac.new(secret.encode("utf-8"), message, hashlib.sha256).hexdigest()


def verify_callback_signature(
    payload: Mapping[str, Any],
    *,
    secret: str,
    required: bool,
    tolerance_seconds: int,
    now: Optional[int] = None,
) -> None:
    signature = payload.get("signature")
    if signature is None and not required:
        return
    if not isinstance(signature, str) or not signature:
        raise AppError(
            "CALLBACK_SIGNATURE_REQUIRED",
            "Payment callback signature is required.",
            status.HTTP_401_UNAUTHORIZED,
        )

    timestamp = payload.get("timestamp")
    if not isinstance(timestamp, int):
        raise AppError(
            "CALLBACK_TIMESTAMP_REQUIRED",
            "Payment callback timestamp is required.",
            status.HTTP_401_UNAUTHORIZED,
        )
    current = now if now is not None else int(time.time())
    if abs(current - timestamp) > tolerance_seconds:
        raise AppError(
            "CALLBACK_TIMESTAMP_EXPIRED",
            "Payment callback timestamp is outside the allowed window.",
            status.HTTP_401_UNAUTHORIZED,
        )

    expected = sign_callback_payload(payload, secret=secret)
    if not hmac.compare_digest(expected, signature):
        raise AppError(
            "CALLBACK_SIGNATURE_INVALID",
            "Payment callback signature is invalid.",
            status.HTTP_401_UNAUTHORIZED,
        )
