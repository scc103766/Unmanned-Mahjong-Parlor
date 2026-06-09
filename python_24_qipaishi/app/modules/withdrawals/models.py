from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import JSON, DateTime, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, IdMixin, TimestampMixin


class Withdrawal(IdMixin, TimestampMixin, Base):
    __tablename__ = "withdrawals"

    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), index=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    requested_by: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    status: Mapped[str] = mapped_column(String(32), default="pending", index=True)
    remark: Mapped[Optional[str]] = mapped_column(String(256))
    review_note: Mapped[Optional[str]] = mapped_column(String(256))
    reject_reason: Mapped[Optional[str]] = mapped_column(String(256))
    payout_ref: Mapped[Optional[str]] = mapped_column(String(128), index=True)
    payout_payload: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)
    requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    reviewed_by: Mapped[Optional[str]] = mapped_column(ForeignKey("users.id"), index=True)
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    paid_by: Mapped[Optional[str]] = mapped_column(ForeignKey("users.id"), index=True)
    paid_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    rejected_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
