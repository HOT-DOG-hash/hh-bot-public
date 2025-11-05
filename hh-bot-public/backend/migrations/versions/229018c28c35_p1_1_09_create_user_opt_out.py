"""Create campaign_user_opt_out table

Revision ID: 229018c28c35
Revises: b6137c9a6ea7
Create Date: 2025-10-28 23:12:52.322040

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "229018c28c35"
down_revision: Union[str, Sequence[str], None] = "b6137c9a6ea7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create campaign_user_opt_out (SCHEMA.md §UserOptOut)."""

    op.create_table(
        "campaign_user_opt_out",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("owner_id", sa.Integer(), nullable=False),
        sa.Column("reason", sa.String(length=255), nullable=True),
        sa.Column("effective_from", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.CheckConstraint(
            "effective_from <= COALESCE(expires_at, effective_from)",
            name="user_opt_out_interval_chk",
        ),
    )

    op.create_index(
        "uniq_opt_out_revision",
        "campaign_user_opt_out",
        ["owner_id", "effective_from"],
        unique=True,
    )
    op.create_index(
        "uniq_opt_out_active",
        "campaign_user_opt_out",
        ["owner_id"],
        unique=True,
        postgresql_where=sa.text("expires_at IS NULL"),
        sqlite_where=sa.text("expires_at IS NULL"),
    )
    op.create_index(
        "idx_opt_out_active",
        "campaign_user_opt_out",
        ["owner_id", "expires_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("idx_opt_out_active", table_name="campaign_user_opt_out")
    op.drop_index("uniq_opt_out_active", table_name="campaign_user_opt_out")
    op.drop_index("uniq_opt_out_revision", table_name="campaign_user_opt_out")
    op.drop_table("campaign_user_opt_out")
