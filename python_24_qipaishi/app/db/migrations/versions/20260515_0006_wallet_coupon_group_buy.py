"""Create wallet, coupon, and group-buy tables.

Revision ID: 20260515_0006
Revises: 20260514_0005
Create Date: 2026-05-15
"""

import sqlalchemy as sa
from alembic import op

revision = "20260515_0006"
down_revision = "20260514_0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "wallet_accounts",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("tenant_id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("cash_balance", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("gift_balance", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("tenant_id", "user_id", name="uq_wallet_accounts_tenant_user"),
    )
    op.create_index("ix_wallet_accounts_tenant_id", "wallet_accounts", ["tenant_id"])
    op.create_index("ix_wallet_accounts_user_id", "wallet_accounts", ["user_id"])
    op.create_index("ix_wallet_accounts_status", "wallet_accounts", ["status"])

    op.create_table(
        "wallet_ledgers",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("tenant_id", sa.String(length=36), nullable=False),
        sa.Column("account_id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("direction", sa.String(length=16), nullable=False),
        sa.Column("amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("cash_balance_after", sa.Numeric(10, 2), nullable=False),
        sa.Column("gift_balance_after", sa.Numeric(10, 2), nullable=False),
        sa.Column("biz_type", sa.String(length=64), nullable=False),
        sa.Column("biz_id", sa.String(length=64), nullable=True),
        sa.Column("remark", sa.String(length=256), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["account_id"], ["wallet_accounts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_wallet_ledgers_tenant_id", "wallet_ledgers", ["tenant_id"])
    op.create_index("ix_wallet_ledgers_account_id", "wallet_ledgers", ["account_id"])
    op.create_index("ix_wallet_ledgers_user_id", "wallet_ledgers", ["user_id"])
    op.create_index("ix_wallet_ledgers_direction", "wallet_ledgers", ["direction"])
    op.create_index("ix_wallet_ledgers_biz_type", "wallet_ledgers", ["biz_type"])
    op.create_index("ix_wallet_ledgers_biz_id", "wallet_ledgers", ["biz_id"])

    op.create_table(
        "coupon_templates",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("tenant_id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("coupon_type", sa.String(length=32), nullable=False, server_default="amount"),
        sa.Column("value", sa.Numeric(10, 2), nullable=False),
        sa.Column("threshold", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("total_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("claimed_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("per_user_limit", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("valid_from", sa.DateTime(timezone=True), nullable=True),
        sa.Column("valid_to", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_coupon_templates_tenant_id", "coupon_templates", ["tenant_id"])
    op.create_index("ix_coupon_templates_coupon_type", "coupon_templates", ["coupon_type"])
    op.create_index("ix_coupon_templates_status", "coupon_templates", ["status"])

    op.create_table(
        "coupons",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("tenant_id", sa.String(length=36), nullable=False),
        sa.Column("template_id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="available"),
        sa.Column("value", sa.Numeric(10, 2), nullable=False),
        sa.Column("threshold", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("locked_order_id", sa.String(length=36), nullable=True),
        sa.Column("used_order_id", sa.String(length=36), nullable=True),
        sa.Column("valid_from", sa.DateTime(timezone=True), nullable=True),
        sa.Column("valid_to", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["template_id"], ["coupon_templates.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_coupons_tenant_id", "coupons", ["tenant_id"])
    op.create_index("ix_coupons_template_id", "coupons", ["template_id"])
    op.create_index("ix_coupons_user_id", "coupons", ["user_id"])
    op.create_index("ix_coupons_status", "coupons", ["status"])
    op.create_index("ix_coupons_locked_order_id", "coupons", ["locked_order_id"])
    op.create_index("ix_coupons_used_order_id", "coupons", ["used_order_id"])

    op.create_table(
        "group_buy_codes",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("tenant_id", sa.String(length=36), nullable=False),
        sa.Column("store_id", sa.String(length=36), nullable=False),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="available"),
        sa.Column("locked_order_id", sa.String(length=36), nullable=True),
        sa.Column("verified_order_id", sa.String(length=36), nullable=True),
        sa.Column("valid_from", sa.DateTime(timezone=True), nullable=True),
        sa.Column("valid_to", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["store_id"], ["stores.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("tenant_id", "code", name="uq_group_buy_codes_tenant_code"),
    )
    op.create_index("ix_group_buy_codes_tenant_id", "group_buy_codes", ["tenant_id"])
    op.create_index("ix_group_buy_codes_store_id", "group_buy_codes", ["store_id"])
    op.create_index("ix_group_buy_codes_code", "group_buy_codes", ["code"])
    op.create_index("ix_group_buy_codes_status", "group_buy_codes", ["status"])
    op.create_index("ix_group_buy_codes_locked_order_id", "group_buy_codes", ["locked_order_id"])
    op.create_index("ix_group_buy_codes_verified_order_id", "group_buy_codes", ["verified_order_id"])


def downgrade() -> None:
    op.drop_table("group_buy_codes")
    op.drop_table("coupons")
    op.drop_table("coupon_templates")
    op.drop_table("wallet_ledgers")
    op.drop_table("wallet_accounts")
