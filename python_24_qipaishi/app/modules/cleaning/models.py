from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import JSON, DateTime, ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, IdMixin, TimestampMixin


class CleaningTask(IdMixin, TimestampMixin, Base):
    __tablename__ = "cleaning_tasks"
    __table_args__ = (
        UniqueConstraint("tenant_id", "order_id", name="uq_cleaning_tasks_tenant_order"),
    )

    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), index=True)
    store_id: Mapped[str] = mapped_column(ForeignKey("stores.id"), index=True)
    room_id: Mapped[str] = mapped_column(ForeignKey("rooms.id"), index=True)
    order_id: Mapped[str] = mapped_column(ForeignKey("orders.id"), index=True)
    cleaner_id: Mapped[Optional[str]] = mapped_column(ForeignKey("users.id"), index=True)
    status: Mapped[str] = mapped_column(String(32), default="pending", index=True)
    scheduled_start_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    scheduled_end_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    accepted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    settled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    canceled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    review_note: Mapped[Optional[str]] = mapped_column(String(256))
    cancel_reason: Mapped[Optional[str]] = mapped_column(String(256))
    complaint_reason: Mapped[Optional[str]] = mapped_column(String(256))
    complained_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    settlement_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0.00"))


class CleaningProof(IdMixin, TimestampMixin, Base):
    __tablename__ = "cleaning_proofs"

    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), index=True)
    task_id: Mapped[str] = mapped_column(ForeignKey("cleaning_tasks.id"), index=True)
    uploaded_by: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    image_urls: Mapped[list[str]] = mapped_column(JSON, default=list)
    remark: Mapped[Optional[str]] = mapped_column(String(256))
