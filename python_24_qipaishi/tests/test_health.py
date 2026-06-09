from app.api.v1 import dependencies
from app.api.v1.routers.health import health


async def test_health_returns_service_checks(route_request) -> None:
    body = await health(route_request)
    assert body["code"] == 0
    assert body["data"]["checks"]["api"]["status"] == "ok"
    assert body["data"]["checks"]["database"]["status"] == "skipped"
    assert body["data"]["checks"]["redis"]["status"] == "skipped"
    assert body["request_id"] == "req_test"


async def test_get_db_session_opens_session_from_factory(monkeypatch) -> None:
    events = []

    class DummySession:
        async def __aenter__(self):
            events.append("enter")
            return self

        async def __aexit__(self, exc_type, exc, tb):
            events.append("exit")

    class DummyFactory:
        def __call__(self):
            events.append("call")
            return DummySession()

    monkeypatch.setattr(dependencies, "async_session", lambda: DummyFactory())

    generator = dependencies.get_db_session()
    session = await generator.__anext__()
    await generator.aclose()

    assert isinstance(session, DummySession)
    assert events == ["call", "enter", "exit"]
