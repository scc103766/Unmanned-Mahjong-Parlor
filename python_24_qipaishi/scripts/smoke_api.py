import sys
import asyncio
from types import SimpleNamespace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.main import app
from app.api.v1.routers.health import health
from app.api.v1.routers.meta import openapi_tags, version


class SmokeRequest:
    def __init__(self) -> None:
        self.app = app
        self.state = SimpleNamespace(request_id="req_smoke")


async def main() -> None:
    request = SmokeRequest()

    health_body = await health(request)  # type: ignore[arg-type]
    assert health_body["code"] == 0
    assert health_body["data"]["checks"]["api"]["status"] == "ok"

    version_body = await version(request)  # type: ignore[arg-type]
    assert version_body["data"]["name"] == "Qipaishi API"

    tags_body = await openapi_tags(request)  # type: ignore[arg-type]
    tag_names = {tag["name"] for tag in tags_body["data"]}
    assert {"health", "meta", "orders", "devices", "cleaning"}.issubset(tag_names)

    print("smoke ok")


if __name__ == "__main__":
    asyncio.run(main())
