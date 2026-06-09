from typing import Optional

from sqlalchemy import JSON, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, IdMixin, TimestampMixin


class Store(IdMixin, TimestampMixin, Base):
    __tablename__ = "stores"

    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), index=True)
    name: Mapped[str] = mapped_column(String(120), index=True)
    address: Mapped[Optional[str]] = mapped_column(String(256))
    longitude: Mapped[Optional[float]] = mapped_column(Float)
    latitude: Mapped[Optional[float]] = mapped_column(Float)
    notice: Mapped[Optional[str]] = mapped_column(String(512))
    contact_phone: Mapped[Optional[str]] = mapped_column(String(32))
    wifi_ssid: Mapped[Optional[str]] = mapped_column(String(128))
    wifi_password: Mapped[Optional[str]] = mapped_column(String(128))
    images: Mapped[list[str]] = mapped_column(JSON, default=list)
    business_settings: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)
    cleaning_settings: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(32), default="active", index=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
