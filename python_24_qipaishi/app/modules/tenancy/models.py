from typing import Optional

from sqlalchemy import JSON, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, IdMixin, TimestampMixin


class Tenant(IdMixin, TimestampMixin, Base):
    __tablename__ = "tenants"

    name: Mapped[str] = mapped_column(String(120))
    status: Mapped[str] = mapped_column(String(32), default="active", index=True)
    plan: Mapped[Optional[str]] = mapped_column(String(64))
    settings: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)


class TenantApp(IdMixin, TimestampMixin, Base):
    __tablename__ = "tenant_apps"
    __table_args__ = (
        UniqueConstraint("tenant_id", "client_type", "app_id", name="uq_tenant_apps_client_app"),
    )

    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), index=True)
    client_type: Mapped[str] = mapped_column(String(32))
    app_id: Mapped[str] = mapped_column(String(128))
    mch_id: Mapped[Optional[str]] = mapped_column(String(128))
    secret_ref: Mapped[Optional[str]] = mapped_column(String(256))
    status: Mapped[str] = mapped_column(String(32), default="active")
