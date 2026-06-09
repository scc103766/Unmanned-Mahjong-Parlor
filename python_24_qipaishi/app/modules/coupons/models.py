from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, IdMixin, TimestampMixin


class CouponTemplate(IdMixin, TimestampMixin, Base):
    __tablename__ = "coupon_templates"

    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), index=True)
    name: Mapped[str] = mapped_column(String(120))
    coupon_type: Mapped[str] = mapped_column(String(32), default="amount", index=True)
    value: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    threshold: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0.00"))
    total_count: Mapped[int] = mapped_column(Integer, default=0)
    claimed_count: Mapped[int] = mapped_column(Integer, default=0)
    per_user_limit: Mapped[int] = mapped_column(Integer, default=1)
    valid_from: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    valid_to: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(32), default="active", index=True)


class Coupon(IdMixin, TimestampMixin, Base):
    __tablename__ = "coupons"

    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), index=True)
    template_id: Mapped[str] = mapped_column(ForeignKey("coupon_templates.id"), index=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    status: Mapped[str] = mapped_column(String(32), default="available", index=True)
    value: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    threshold: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0.00"))
    locked_order_id: Mapped[Optional[str]] = mapped_column(String(36), index=True)
    used_order_id: Mapped[Optional[str]] = mapped_column(String(36), index=True)
    valid_from: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    valid_to: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
