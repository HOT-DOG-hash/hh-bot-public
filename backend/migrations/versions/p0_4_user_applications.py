"""user applications idempotency registry

Revision ID: p0_4_user_applications
Revises: p0_3_billing_schema
Create Date: 2025-11-07 15:00:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "p0_4_user_applications"
down_revision: str | Sequence[str] | None = "p0_3_billing_schema"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "user_applications",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("vacancy_id", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.UniqueConstraint("user_id", "vacancy_id", name="uq_user_applications_user_vacancy"),
    )
    op.create_index(
        "ix_user_applications_created_at",
        "user_applications",
        ["created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_user_applications_created_at", table_name="user_applications")
    op.drop_table("user_applications")
