"""Create campaign_cooldown_policies table

Revision ID: 9d24fe35c583
Revises: a03371008559
Create Date: 2025-10-28 23:12:01.618600

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "9d24fe35c583"
down_revision: Union[str, Sequence[str], None] = "a03371008559"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create campaign_cooldown_policies (SCHEMA.md §CooldownPolicies)."""

    op.create_table(
        "campaign_cooldown_policies",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("campaign_id", sa.Integer(), nullable=False),
        sa.Column("base_delay_ms", sa.Integer(), nullable=False, server_default=sa.text("60000")),
        sa.Column("max_delay_ms", sa.Integer(), nullable=False, server_default=sa.text("900000")),
        sa.Column("strategy", sa.String(length=16), nullable=False, server_default=sa.text("'exp'")),
        sa.Column("error_streak_limit", sa.Integer(), nullable=False, server_default=sa.text("5")),
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
        sa.CheckConstraint("base_delay_ms > 0", name="cooldown_base_delay_chk"),
        sa.CheckConstraint("max_delay_ms >= base_delay_ms", name="cooldown_max_delay_chk"),
        sa.CheckConstraint("strategy IN ('exp','linear')", name="cooldown_strategy_chk"),
        sa.CheckConstraint("error_streak_limit BETWEEN 1 AND 10", name="cooldown_error_limit_chk"),
    )

    op.create_index(
        "uniq_cooldown_per_campaign",
        "campaign_cooldown_policies",
        ["campaign_id"],
        unique=True,
    )
    op.create_index(
        "idx_cooldown_campaign",
        "campaign_cooldown_policies",
        ["campaign_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("idx_cooldown_campaign", table_name="campaign_cooldown_policies")
    op.drop_index("uniq_cooldown_per_campaign", table_name="campaign_cooldown_policies")
    op.drop_table("campaign_cooldown_policies")
