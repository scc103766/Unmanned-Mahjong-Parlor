from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, IdMixin, TimestampMixin


class Room(IdMixin, TimestampMixin, Base):
    __tablename__ = "rooms"

    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), index=True)
    store_id: Mapped[str] = mapped_column(ForeignKey("stores.id"), index=True)
    name: Mapped[str] = mapped_column(String(120), index=True)
    room_type: Mapped[Optional[str]] = mapped_column(String(64), index=True)
    capacity: Mapped[int] = mapped_column(Integer, default=4)
    tags: Mapped[list[str]] = mapped_column(JSON, default=list)
    images: Mapped[list[str]] = mapped_column(JSON, default=list)
    status: Mapped[str] = mapped_column(String(32), default="active", index=True)
    cleaning_status: Mapped[str] = mapped_column(String(32), default="clean", index=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)


class RoomPriceRule(IdMixin, TimestampMixin, Base):
    __tablename__ = "room_price_rules"

    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), index=True)
    room_id: Mapped[str] = mapped_column(ForeignKey("rooms.id"), index=True)
    name: Mapped[str] = mapped_column(String(120), default="default")
    base_price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    weekday_prices: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)
    night_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))
    min_hours: Mapped[int] = mapped_column(Integer, default=1)
    advance_booking_days: Mapped[int] = mapped_column(Integer, default=14)
    status: Mapped[str] = mapped_column(String(32), default="active", index=True)


class RoomBlockedSlot(IdMixin, TimestampMixin, Base):
    __tablename__ = "room_blocked_slots"

    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), index=True)
    room_id: Mapped[str] = mapped_column(ForeignKey("rooms.id"), index=True)
    start_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    end_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    reason: Mapped[Optional[str]] = mapped_column(String(256))
    status: Mapped[str] = mapped_column(String(32), default="active", index=True)
