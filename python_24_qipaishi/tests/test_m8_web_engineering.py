import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "web"


def test_m8_web_uses_vite_vue_typescript_stack() -> None:
    package = json.loads((WEB / "package.json").read_text(encoding="utf-8"))

    assert package["scripts"]["dev"].startswith("vite")
    assert package["scripts"]["build"] == "vue-tsc --noEmit && vite build"
    assert package["scripts"]["typecheck"] == "vue-tsc --noEmit"
    assert package["dependencies"]["vue"].startswith("^3.")
    assert "vue-router" in package["dependencies"]
    assert "pinia" in package["dependencies"]
    assert "axios" in package["dependencies"]
    assert "vite" in package["devDependencies"]
    assert "typescript" in package["devDependencies"]
    assert (WEB / "src" / "main.ts").exists()
    assert not (WEB / "src" / "main.js").exists()


def test_m8_web_has_formal_app_layers() -> None:
    expected_files = [
        "src/app/router/index.ts",
        "src/app/stores/session.ts",
        "src/app/permissions/guards.ts",
        "src/core/api/client.ts",
        "src/core/api/types.ts",
        "src/layouts/merchant/MerchantLayout.vue",
        "src/modules/merchant/views/DashboardView.vue",
        "src/modules/merchant/views/OrdersView.vue",
        "src/modules/merchant/views/MembersView.vue",
        "src/modules/merchant/views/WithdrawalsView.vue",
        "src/modules/merchant/views/ExceptionsView.vue",
        "src/modules/merchant/views/SettingsView.vue",
        "src/shared/utils/format.ts",
    ]

    for relative_path in expected_files:
        assert (WEB / relative_path).exists(), relative_path


def test_m8_web_routes_and_api_cover_merchant_operations() -> None:
    router_source = (WEB / "src" / "app" / "router" / "index.ts").read_text(encoding="utf-8")
    api_source = (WEB / "src" / "core" / "api" / "client.ts").read_text(encoding="utf-8")

    for route_name in ["dashboard", "orders", "members", "withdrawals", "exceptions", "settings"]:
        assert f'name: "{route_name}"' in router_source

    for endpoint in [
        "/api/v1/auth/dev-bootstrap",
        "/api/v1/analytics/dashboard",
        "/api/v1/analytics/rooms/usage",
        "/api/v1/operations/exceptions",
        "/api/v1/operations/compensations",
        "/api/v1/withdrawals",
        "/api/v1/members",
        "/api/v1/orders",
        "/reschedule/quote",
    ]:
        assert endpoint in api_source
