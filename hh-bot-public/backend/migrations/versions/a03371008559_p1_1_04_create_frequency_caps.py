"""Create campaign_frequency_caps table

Revision ID: a03371008559
Revises: 11ad69c2dba7
Create Date: 2025-10-28 23:11:48.934346

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a03371008559"
down_revision: Union[str, Sequence[str], None] = "11ad69c2dba7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create campaign_frequency_caps (SCHEMA.md §FrequencyCaps)."""

    op.create_table(
        "campaign_frequency_caps",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("campaign_id", sa.Integer(), nullable=False),
        sa.Column("per_day", sa.Integer(), nullable=False, server_default=sa.text("10")),
        sa.Column("per_week", sa.Integer(), nullable=False, server_default=sa.text("50")),
        sa.Column("per_company", sa.Integer(), nullable=False, server_default=sa.text("2")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.CheckConstraint("per_day BETWEEN 0 AND 10", name="freq_caps_per_day_chk"),
        sa.CheckConstraint("per_week BETWEEN 0 AND 50", name="freq_caps_per_week_chk"),
        sa.CheckConstraint("per_company BETWEEN 0 AND 2", name="freq_caps_per_company_chk"),
    )

    op.create_index(
        "uniq_caps_per_campaign",
        "campaign_frequency_caps",
        ["campaign_id"],
        unique=True,
    )
    op.create_index(
        "idx_caps_campaign",
        "campaign_frequency_caps",
        ["campaign_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("idx_caps_campaign", table_name="campaign_frequency_caps")
    op.drop_index("uniq_caps_per_campaign", table_name="campaign_frequency_caps")
    op.drop_table("campaign_frequency_caps")
