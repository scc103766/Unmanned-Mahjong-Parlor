"""Add cleaning cancellation fields.

Revision ID: 20260515_0011
Revises: 20260515_0010
Create Date: 2026-05-15
"""

import sqlalchemy as sa
from alembic import op

revision = "20260515_0011"
down_revision = "20260515_0010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("cleaning_tasks") as batch_op:
        batch_op.add_column(sa.Column("canceled_at", sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column("cancel_reason", sa.String(length=256), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("cleaning_tasks") as batch_op:
        batch_op.drop_column("cancel_reason")
        batch_op.drop_column("canceled_at")
