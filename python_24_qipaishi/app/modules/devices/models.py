from datetime import datetime
from typing import Optional

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, IdMixin, TimestampMixin


class Device(IdMixin, TimestampMixin, Base):
    __tablename__ = "devices"
    __table_args__ = (
        UniqueConstraint("tenant_id", "provider", "external_id", name="uq_devices_provider_ref"),
    )

    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), index=True)
    store_id: Mapped[str] = mapped_column(ForeignKey("stores.id"), index=True)
    room_id: Mapped[Optional[str]] = mapped_column(ForeignKey("rooms.id"), index=True)
    name: Mapped[str] = mapped_column(String(120), index=True)
    device_type: Mapped[str] = mapped_column(String(32), index=True)
    provider: Mapped[str] = mapped_column(String(32), default="mock", index=True)
    external_id: Mapped[str] = mapped_column(String(128), index=True)
    status: Mapped[str] = mapped_column(String(32), default="active", index=True)
    capabilities: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)


class DeviceCommand(IdMixin, TimestampMixin, Base):
    __tablename__ = "device_commands"
    __table_args__ = (
        UniqueConstraint("tenant_id", "idempotency_key", name="uq_device_commands_tenant_idem"),
    )

    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), index=True)
    device_id: Mapped[str] = mapped_column(ForeignKey("devices.id"), index=True)
    actor_id: Mapped[Optional[str]] = mapped_column(ForeignKey("users.id"), index=True)
    command: Mapped[str] = mapped_column(String(64), index=True)
    biz_type: Mapped[str] = mapped_column(String(64), index=True)
    biz_id: Mapped[str] = mapped_column(String(64), index=True)
    status: Mapped[str] = mapped_column(String(32), default="pending", index=True)
    idempotency_key: Mapped[Optional[str]] = mapped_column(String(128), index=True)
    request_payload: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)
    response_payload: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)
    failure_reason: Mapped[Optional[str]] = mapped_column(String(256))
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    executed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), index=True)
