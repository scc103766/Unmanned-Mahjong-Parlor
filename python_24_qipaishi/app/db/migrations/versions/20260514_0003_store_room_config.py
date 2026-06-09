"""Create store and room configuration tables.

Revision ID: 20260514_0003
Revises: 20260514_0002
Create Date: 2026-05-14
"""

import sqlalchemy as sa
from alembic import op

revision = "20260514_0003"
down_revision = "20260514_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "stores",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("tenant_id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("address", sa.String(length=256), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("notice", sa.String(length=512), nullable=True),
        sa.Column("contact_phone", sa.String(length=32), nullable=True),
        sa.Column("wifi_ssid", sa.String(length=128), nullable=True),
        sa.Column("wifi_password", sa.String(length=128), nullable=True),
        sa.Column("images", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column("business_settings", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("cleaning_settings", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="active"),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_stores_tenant_id", "stores", ["tenant_id"])
    op.create_index("ix_stores_name", "stores", ["name"])
    op.create_index("ix_stores_status", "stores", ["status"])

    op.create_table(
        "rooms",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("tenant_id", sa.String(length=36), nullable=False),
        sa.Column("store_id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("room_type", sa.String(length=64), nullable=True),
        sa.Column("capacity", sa.Integer(), nullable=False, server_default="4"),
        sa.Column("tags", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column("images", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="active"),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["store_id"], ["stores.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_rooms_tenant_id", "rooms", ["tenant_id"])
    op.create_index("ix_rooms_store_id", "rooms", ["store_id"])
    op.create_index("ix_rooms_name", "rooms", ["name"])
    op.create_index("ix_rooms_room_type", "rooms", ["room_type"])
    op.create_index("ix_rooms_status", "rooms", ["status"])

    op.create_table(
        "room_price_rules",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("tenant_id", sa.String(length=36), nullable=False),
        sa.Column("room_id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False, server_default="default"),
        sa.Column("base_price", sa.Numeric(10, 2), nullable=False),
        sa.Column("weekday_prices", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("night_price", sa.Numeric(10, 2), nullable=True),
        sa.Column("min_hours", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("advance_booking_days", sa.Integer(), nullable=False, server_default="14"),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["room_id"], ["rooms.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_room_price_rules_tenant_id", "room_price_rules", ["tenant_id"])
    op.create_index("ix_room_price_rules_room_id", "room_price_rules", ["room_id"])
    op.create_index("ix_room_price_rules_status", "room_price_rules", ["status"])

    op.create_table(
        "room_blocked_slots",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("tenant_id", sa.String(length=36), nullable=False),
        sa.Column("room_id", sa.String(length=36), nullable=False),
        sa.Column("start_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("reason", sa.String(length=256), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["room_id"], ["rooms.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_room_blocked_slots_tenant_id", "room_blocked_slots", ["tenant_id"])
    op.create_index("ix_room_blocked_slots_room_id", "room_blocked_slots", ["room_id"])
    op.create_index("ix_room_blocked_slots_start_at", "room_blocked_slots", ["start_at"])
    op.create_index("ix_room_blocked_slots_end_at", "room_blocked_slots", ["end_at"])
    op.create_index("ix_room_blocked_slots_status", "room_blocked_slots", ["status"])


def downgrade() -> None:
    op.drop_table("room_blocked_slots")
    op.drop_table("room_price_rules")
    op.drop_table("rooms")
    op.drop_table("stores")
