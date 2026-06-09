from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import JSON, DateTime, ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, IdMixin, TimestampMixin


class Payment(IdMixin, TimestampMixin, Base):
    __tablename__ = "payments"
    __table_args__ = (
        UniqueConstraint("tenant_id", "idempotency_key", name="uq_payments_tenant_idempotency"),
    )

    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), index=True)
    order_id: Mapped[str] = mapped_column(ForeignKey("orders.id"), index=True)
    channel: Mapped[str] = mapped_column(String(32), default="mock_wechat", index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    status: Mapped[str] = mapped_column(String(32), default="paying", index=True)
    transaction_id: Mapped[Optional[str]] = mapped_column(String(128), index=True)
    idempotency_key: Mapped[Optional[str]] = mapped_column(String(128), index=True)
    provider_payload: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)
    paid_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    closed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))


class PaymentEvent(IdMixin, TimestampMixin, Base):
    __tablename__ = "payment_events"
    __table_args__ = (
        UniqueConstraint("channel", "provider_event_id", name="uq_payment_events_provider_event"),
    )

    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), index=True)
    payment_id: Mapped[Optional[str]] = mapped_column(ForeignKey("payments.id"), index=True)
    channel: Mapped[str] = mapped_column(String(32), default="mock_wechat", index=True)
    event_type: Mapped[str] = mapped_column(String(64), index=True)
    provider_event_id: Mapped[str] = mapped_column(String(128), index=True)
    status: Mapped[str] = mapped_column(String(32), default="processed", index=True)
    payload: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)
    processed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class Refund(IdMixin, TimestampMixin, Base):
    __tablename__ = "refunds"
    __table_args__ = (
        UniqueConstraint("tenant_id", "idempotency_key", name="uq_refunds_tenant_idempotency"),
    )

    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), index=True)
    payment_id: Mapped[str] = mapped_column(ForeignKey("payments.id"), index=True)
    order_id: Mapped[str] = mapped_column(ForeignKey("orders.id"), index=True)
    refund_no: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    reason: Mapped[Optional[str]] = mapped_column(String(256))
    status: Mapped[str] = mapped_column(String(32), default="created", index=True)
    provider_refund_id: Mapped[Optional[str]] = mapped_column(String(128), index=True)
    idempotency_key: Mapped[Optional[str]] = mapped_column(String(128), index=True)
    provider_payload: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)
    refunded_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
