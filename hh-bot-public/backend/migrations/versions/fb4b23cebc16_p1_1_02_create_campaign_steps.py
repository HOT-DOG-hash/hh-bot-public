"""Create campaign_steps table

Revision ID: fb4b23cebc16
Revises: p1_1_01
Create Date: 2025-10-28 23:11:12.906648

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "fb4b23cebc16"
down_revision: Union[str, Sequence[str], None] = "p1_1_01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create campaign_steps (SCHEMA.md §CampaignSteps)."""

    vacancy_filter_type = sa.JSON().with_variant(
        postgresql.JSONB(astext_type=sa.Text()), "postgresql"
    )

    op.create_table(
        "campaign_steps",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("campaign_id", sa.Integer(), nullable=False),
        sa.Column("step_order", sa.Integer(), nullable=False),
        sa.Column("vacancy_filter", vacancy_filter_type, nullable=False),
        sa.Column("message_template_id", sa.Integer(), nullable=False),
        sa.Column("delivery_window_id", sa.Integer(), nullable=False),
        sa.Column(
            "skip_policy",
            sa.String(length=16),
            nullable=False,
            server_default=sa.text("'manual'"),
        ),
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
        sa.CheckConstraint(
            "step_order BETWEEN 1 AND 999", name="campaign_steps_order_range_chk"
        ),
        sa.CheckConstraint(
            "skip_policy IN ('manual','auto')", name="campaign_steps_skip_policy_chk"
        ),
    )

    op.create_index(
        "uniq_steps_per_campaign",
        "campaign_steps",
        ["campaign_id", "step_order"],
        unique=True,
    )
    op.create_index(
        "idx_campaign_steps_order",
        "campaign_steps",
        ["campaign_id", "step_order"],
        unique=False,
    )
    op.create_index(
        "idx_campaign_steps_template",
        "campaign_steps",
        ["campaign_id", "message_template_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("idx_campaign_steps_template", table_name="campaign_steps")
    op.drop_index("idx_campaign_steps_order", table_name="campaign_steps")
    op.drop_index("uniq_steps_per_campaign", table_name="campaign_steps")
    op.drop_table("campaign_steps")
