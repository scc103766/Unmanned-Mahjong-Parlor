from typing import Any

from app.modules.devices.models import Device


class MockDeviceAdapter:
    async def execute(
        self,
        *,
        device: Device,
        command: str,
        payload: dict[str, object],
    ) -> dict[str, Any]:
        if device.external_id == "mock_fail":
            return {
                "ok": False,
                "provider": "mock",
                "external_id": device.external_id,
                "command": command,
                "error": "mock device failure",
            }
        return {
            "ok": True,
            "provider": "mock",
            "external_id": device.external_id,
            "command": command,
            "payload": payload,
        }
