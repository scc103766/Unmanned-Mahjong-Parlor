from typing import Optional

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, IdMixin, TimestampMixin


class User(IdMixin, TimestampMixin, Base):
    __tablename__ = "users"

    tenant_id: Mapped[Optional[str]] = mapped_column(ForeignKey("tenants.id"), index=True)
    phone: Mapped[Optional[str]] = mapped_column(String(32), index=True)
    openid: Mapped[Optional[str]] = mapped_column(String(128), index=True)
    unionid: Mapped[Optional[str]] = mapped_column(String(128), index=True)
    nickname: Mapped[Optional[str]] = mapped_column(String(128))
    avatar_url: Mapped[Optional[str]] = mapped_column(String(512))
    status: Mapped[str] = mapped_column(String(32), default="active", index=True)


class Role(IdMixin, TimestampMixin, Base):
    __tablename__ = "roles"
    __table_args__ = (UniqueConstraint("code", name="uq_roles_code"),)

    code: Mapped[str] = mapped_column(String(64))
    name: Mapped[str] = mapped_column(String(120))
    scope: Mapped[str] = mapped_column(String(32), default="tenant")


class UserRole(IdMixin, TimestampMixin, Base):
    __tablename__ = "user_roles"
    __table_args__ = (
        UniqueConstraint("tenant_id", "user_id", "role_id", name="uq_user_roles_tenant_user_role"),
    )

    tenant_id: Mapped[Optional[str]] = mapped_column(ForeignKey("tenants.id"), index=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    role_id: Mapped[str] = mapped_column(ForeignKey("roles.id"), index=True)


class UserStoreScope(IdMixin, TimestampMixin, Base):
    __tablename__ = "user_store_scopes"
    __table_args__ = (
        UniqueConstraint("tenant_id", "user_id", "store_id", name="uq_user_store_scopes"),
    )

    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), index=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    store_id: Mapped[str] = mapped_column(String(36), index=True)
