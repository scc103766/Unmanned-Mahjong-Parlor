import sys
from collections.abc import Generator
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.core.config import get_settings
from app.main import create_app


class RouteRequest:
    def __init__(self) -> None:
        self.app = create_app()
        self.state = SimpleNamespace(request_id="req_test")


@pytest.fixture(autouse=True)
def clear_settings_cache() -> Generator[None, None, None]:
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
def route_request() -> RouteRequest:
    return RouteRequest()
