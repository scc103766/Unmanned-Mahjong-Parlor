from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, IdMixin, TimestampMixin


class GroupBuyCode(IdMixin, TimestampMixin, Base):
    __tablename__ = "group_buy_codes"
    __table_args__ = (UniqueConstraint("tenant_id", "code", name="uq_group_buy_codes_tenant_code"),)

    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), index=True)
    store_id: Mapped[str] = mapped_column(ForeignKey("stores.id"), index=True)
    code: Mapped[str] = mapped_column(String(64), index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    status: Mapped[str] = mapped_column(String(32), default="available", index=True)
    locked_order_id: Mapped[Optional[str]] = mapped_column(String(36), index=True)
    verified_order_id: Mapped[Optional[str]] = mapped_column(String(36), index=True)
    valid_from: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    valid_to: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
