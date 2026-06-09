"""Complete cleaning workflow fields and room cleaning status.

Revision ID: 20260515_0010
Revises: 20260515_0009
Create Date: 2026-05-15
"""

import sqlalchemy as sa
from alembic import op

revision = "20260515_0010"
down_revision = "20260515_0009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("rooms") as batch_op:
        batch_op.add_column(
            sa.Column(
                "cleaning_status",
                sa.String(length=32),
                nullable=False,
                server_default="clean",
            )
        )
        batch_op.create_index("ix_rooms_cleaning_status", ["cleaning_status"])

    with op.batch_alter_table("cleaning_tasks") as batch_op:
        batch_op.add_column(sa.Column("complaint_reason", sa.String(length=256), nullable=True))
        batch_op.add_column(sa.Column("complained_at", sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(
            sa.Column(
                "settlement_amount",
                sa.Numeric(10, 2),
                nullable=False,
                server_default="0.00",
            )
        )


def downgrade() -> None:
    with op.batch_alter_table("cleaning_tasks") as batch_op:
        batch_op.drop_column("settlement_amount")
        batch_op.drop_column("complained_at")
        batch_op.drop_column("complaint_reason")

    with op.batch_alter_table("rooms") as batch_op:
        batch_op.drop_index("ix_rooms_cleaning_status")
        batch_op.drop_column("cleaning_status")
