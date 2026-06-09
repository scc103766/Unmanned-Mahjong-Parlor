"""Harden payment callback and refund idempotency.

Revision ID: 20260515_0007
Revises: 20260515_0006
Create Date: 2026-05-15
"""

import sqlalchemy as sa
from alembic import op

revision = "20260515_0007"
down_revision = "20260515_0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("refunds") as batch_op:
        batch_op.add_column(sa.Column("idempotency_key", sa.String(length=128), nullable=True))
        batch_op.create_index("ix_refunds_idempotency_key", ["idempotency_key"])
        batch_op.create_unique_constraint(
            "uq_refunds_tenant_idempotency",
            ["tenant_id", "idempotency_key"],
        )


def downgrade() -> None:
    with op.batch_alter_table("refunds") as batch_op:
        batch_op.drop_constraint("uq_refunds_tenant_idempotency", type_="unique")
        batch_op.drop_index("ix_refunds_idempotency_key")
        batch_op.drop_column("idempotency_key")
