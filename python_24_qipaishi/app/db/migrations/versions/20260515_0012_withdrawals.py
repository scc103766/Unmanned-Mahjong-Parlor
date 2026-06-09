"""Create withdrawal workflow table.

Revision ID: 20260515_0012
Revises: 20260515_0011
Create Date: 2026-05-15
"""

import sqlalchemy as sa
from alembic import op

revision = "20260515_0012"
down_revision = "20260515_0011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "withdrawals",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("tenant_id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("requested_by", sa.String(length=36), nullable=False),
        sa.Column("amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("remark", sa.String(length=256), nullable=True),
        sa.Column("review_note", sa.String(length=256), nullable=True),
        sa.Column("reject_reason", sa.String(length=256), nullable=True),
        sa.Column("payout_ref", sa.String(length=128), nullable=True),
        sa.Column("payout_payload", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("requested_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("reviewed_by", sa.String(length=36), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("paid_by", sa.String(length=36), nullable=True),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("rejected_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["requested_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["reviewed_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["paid_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_withdrawals_tenant_id", "withdrawals", ["tenant_id"])
    op.create_index("ix_withdrawals_user_id", "withdrawals", ["user_id"])
    op.create_index("ix_withdrawals_requested_by", "withdrawals", ["requested_by"])
    op.create_index("ix_withdrawals_status", "withdrawals", ["status"])
    op.create_index("ix_withdrawals_payout_ref", "withdrawals", ["payout_ref"])
    op.create_index("ix_withdrawals_requested_at", "withdrawals", ["requested_at"])
    op.create_index("ix_withdrawals_reviewed_by", "withdrawals", ["reviewed_by"])
    op.create_index("ix_withdrawals_paid_by", "withdrawals", ["paid_by"])


def downgrade() -> None:
    op.drop_table("withdrawals")
