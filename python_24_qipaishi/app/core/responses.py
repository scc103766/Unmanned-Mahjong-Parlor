from typing import Any

from fastapi import Request


def ok(data: Any, request: Request, message: str = "ok") -> dict[str, Any]:
    return {
        "code": 0,
        "message": message,
        "data": data,
        "request_id": getattr(request.state, "request_id", None),
    }

