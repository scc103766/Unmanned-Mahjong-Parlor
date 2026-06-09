from typing import Optional

from sqlalchemy import JSON, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, IdMixin, TimestampMixin


class AuditLog(IdMixin, TimestampMixin, Base):
    __tablename__ = "audit_logs"

    tenant_id: Mapped[Optional[str]] = mapped_column(ForeignKey("tenants.id"), index=True)
    actor_id: Mapped[Optional[str]] = mapped_column(String(36), index=True)
    action: Mapped[str] = mapped_column(String(128), index=True)
    target_type: Mapped[str] = mapped_column(String(64), index=True)
    target_id: Mapped[Optional[str]] = mapped_column(String(64), index=True)
    request_id: Mapped[Optional[str]] = mapped_column(String(128), index=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(64))
    payload: Mapped[dict[str, object]] = mapped_column(JSON, default=dict)
