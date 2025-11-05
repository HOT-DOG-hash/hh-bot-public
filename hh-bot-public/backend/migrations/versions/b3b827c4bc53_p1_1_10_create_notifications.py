"""Create campaign_notifications table

Revision ID: b3b827c4bc53
Revises: 229018c28c35
Create Date: 2025-10-28 23:13:04.978799

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b3b827c4bc53"
down_revision: Union[str, Sequence[str], None] = "229018c28c35"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create campaign_notifications (SCHEMA.md §CampaignNotifications)."""

    op.create_table(
        "campaign_notifications",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("campaign_id", sa.Integer(), nullable=False),
        sa.Column("type", sa.String(length=32), nullable=False),
        sa.Column("channel", sa.String(length=16), nullable=False),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("delivery_status", sa.String(length=32), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.CheckConstraint(
            "type IN ('started','finished','empty','paused','limit_reached','resumed')",
            name="campaign_notifications_type_chk",
        ),
        sa.CheckConstraint(
            "channel IN ('bot','email')",
            name="campaign_notifications_channel_chk",
        ),
    )

    op.create_index(
        "uniq_notifications_dedup",
        "campaign_notifications",
        ["campaign_id", "type", "sent_at", "channel"],
        unique=True,
    )
    op.create_index(
        "idx_notifications_campaign",
        "campaign_notifications",
        ["campaign_id", "sent_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("idx_notifications_campaign", table_name="campaign_notifications")
    op.drop_index("uniq_notifications_dedup", table_name="campaign_notifications")
    op.drop_table("campaign_notifications")
