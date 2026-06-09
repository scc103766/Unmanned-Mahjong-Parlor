"""Seed standard identity roles.

Revision ID: 20260514_0002
Revises: 20260513_0001
Create Date: 2026-05-14
"""

import sqlalchemy as sa
from alembic import op

revision = "20260514_0002"
down_revision = "20260513_0001"
branch_labels = None
depends_on = None

ROLE_ROWS = [
    {
        "id": "00000000-0000-4000-8000-000000000001",
        "code": "platform_admin",
        "name": "平台管理员",
        "scope": "platform",
    },
    {
        "id": "00000000-0000-4000-8000-000000000002",
        "code": "merchant_admin",
        "name": "商家管理员",
        "scope": "tenant",
    },
    {
        "id": "00000000-0000-4000-8000-000000000003",
        "code": "clerk",
        "name": "店员",
        "scope": "tenant",
    },
    {
        "id": "00000000-0000-4000-8000-000000000004",
        "code": "cleaner",
        "name": "保洁员",
        "scope": "tenant",
    },
    {
        "id": "00000000-0000-4000-8000-000000000005",
        "code": "customer",
        "name": "顾客",
        "scope": "tenant",
    },
    {
        "id": "00000000-0000-4000-8000-000000000006",
        "code": "support",
        "name": "客服",
        "scope": "tenant",
    },
]


def upgrade() -> None:
    roles = sa.table(
        "roles",
        sa.column("id", sa.String),
        sa.column("code", sa.String),
        sa.column("name", sa.String),
        sa.column("scope", sa.String),
    )
    bind = op.get_bind()
    existing = {
        row[0]
        for row in bind.execute(
            sa.text("select code from roles where code in :codes").bindparams(
                sa.bindparam("codes", [row["code"] for row in ROLE_ROWS], expanding=True)
            )
        )
    }
    new_rows = [row for row in ROLE_ROWS if row["code"] not in existing]
    if new_rows:
        op.bulk_insert(roles, new_rows)


def downgrade() -> None:
    op.execute(
        sa.text("delete from roles where code in :codes").bindparams(
            sa.bindparam("codes", [row["code"] for row in ROLE_ROWS], expanding=True)
        )
    )
