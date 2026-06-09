from app.api.v1.routers.meta import openapi_tags, version


async def test_version_endpoint(route_request) -> None:
    body = await version(route_request)
    assert body["code"] == 0
    assert body["data"]["name"] == "Qipaishi API"
    assert body["data"]["version"] == "0.1.0"


async def test_openapi_tags_endpoint(route_request) -> None:
    body = await openapi_tags(route_request)
    tag_names = {tag["name"] for tag in body["data"]}
    assert {"health", "meta", "auth", "tenancy", "orders", "devices", "cleaning"}.issubset(
        tag_names
    )
