from decimal import Decimal
from typing import Optional

from sqlalchemy import ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, IdMixin, TimestampMixin


class WalletAccount(IdMixin, TimestampMixin, Base):
    __tablename__ = "wallet_accounts"
    __table_args__ = (
        UniqueConstraint("tenant_id", "user_id", name="uq_wallet_accounts_tenant_user"),
    )

    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), index=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    cash_balance: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0.00"))
    gift_balance: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0.00"))
    status: Mapped[str] = mapped_column(String(32), default="active", index=True)


class WalletLedger(IdMixin, TimestampMixin, Base):
    __tablename__ = "wallet_ledgers"

    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), index=True)
    account_id: Mapped[str] = mapped_column(ForeignKey("wallet_accounts.id"), index=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    direction: Mapped[str] = mapped_column(String(16), index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    cash_balance_after: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    gift_balance_after: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    biz_type: Mapped[str] = mapped_column(String(64), index=True)
    biz_id: Mapped[Optional[str]] = mapped_column(String(64), index=True)
    remark: Mapped[Optional[str]] = mapped_column(String(256))
