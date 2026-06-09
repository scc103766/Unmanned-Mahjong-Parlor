"""Create cleaning workflow tables.

Revision ID: 20260515_0009
Revises: 20260515_0008
Create Date: 2026-05-15
"""

import sqlalchemy as sa
from alembic import op

revision = "20260515_0009"
down_revision = "20260515_0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "cleaning_tasks",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("tenant_id", sa.String(length=36), nullable=False),
        sa.Column("store_id", sa.String(length=36), nullable=False),
        sa.Column("room_id", sa.String(length=36), nullable=False),
        sa.Column("order_id", sa.String(length=36), nullable=False),
        sa.Column("cleaner_id", sa.String(length=36), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="pending"),
        sa.Column("scheduled_start_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("scheduled_end_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("settled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("review_note", sa.String(length=256), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["store_id"], ["stores.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["room_id"], ["rooms.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["cleaner_id"], ["users.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("tenant_id", "order_id", name="uq_cleaning_tasks_tenant_order"),
    )
    op.create_index("ix_cleaning_tasks_tenant_id", "cleaning_tasks", ["tenant_id"])
    op.create_index("ix_cleaning_tasks_store_id", "cleaning_tasks", ["store_id"])
    op.create_index("ix_cleaning_tasks_room_id", "cleaning_tasks", ["room_id"])
    op.create_index("ix_cleaning_tasks_order_id", "cleaning_tasks", ["order_id"])
    op.create_index("ix_cleaning_tasks_cleaner_id", "cleaning_tasks", ["cleaner_id"])
    op.create_index("ix_cleaning_tasks_status", "cleaning_tasks", ["status"])

    op.create_table(
        "cleaning_proofs",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("tenant_id", sa.String(length=36), nullable=False),
        sa.Column("task_id", sa.String(length=36), nullable=False),
        sa.Column("uploaded_by", sa.String(length=36), nullable=False),
        sa.Column("image_urls", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column("remark", sa.String(length=256), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["task_id"], ["cleaning_tasks.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["uploaded_by"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_cleaning_proofs_tenant_id", "cleaning_proofs", ["tenant_id"])
    op.create_index("ix_cleaning_proofs_task_id", "cleaning_proofs", ["task_id"])


def downgrade() -> None:
    op.drop_table("cleaning_proofs")
    op.drop_table("cleaning_tasks")
