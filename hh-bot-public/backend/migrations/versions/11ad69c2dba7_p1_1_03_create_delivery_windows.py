"""Create campaign_delivery_windows table

Revision ID: 11ad69c2dba7
Revises: fb4b23cebc16
Create Date: 2025-10-28 23:11:34.449801

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "11ad69c2dba7"
down_revision: Union[str, Sequence[str], None] = "fb4b23cebc16"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create campaign_delivery_windows (SCHEMA.md §DeliveryWindows)."""

    op.create_table(
        "campaign_delivery_windows",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("campaign_id", sa.Integer(), nullable=False),
        sa.Column("start_utc", sa.Time(), nullable=False),
        sa.Column("end_utc", sa.Time(), nullable=False),
        sa.Column("days_mask", sa.String(length=7), nullable=False),
        sa.Column(
            "is_default",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
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
        sa.CheckConstraint("start_utc < end_utc", name="delivery_windows_time_range_chk"),
        sa.CheckConstraint("length(days_mask) = 7", name="delivery_windows_days_mask_len_chk"),
    )

    op.create_index(
        "uniq_windows_signature",
        "campaign_delivery_windows",
        ["campaign_id", "start_utc", "end_utc", "days_mask"],
        unique=True,
    )
    op.create_index(
        "uniq_windows_default",
        "campaign_delivery_windows",
        ["campaign_id"],
        unique=True,
        postgresql_where=sa.text("is_default"),
        sqlite_where=sa.text("is_default"),
    )
    op.create_index(
        "idx_windows_campaign",
        "campaign_delivery_windows",
        ["campaign_id", "start_utc"],
        unique=False,
    )

    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("CREATE EXTENSION IF NOT EXISTS btree_gist")
        op.execute(
            """
            ALTER TABLE campaign_delivery_windows
            ADD CONSTRAINT campaign_delivery_windows_no_overlap
            EXCLUDE USING gist (
                campaign_id WITH =,
                int4range(
                    (EXTRACT(EPOCH FROM start_utc)::int),
                    (EXTRACT(EPOCH FROM end_utc)::int),
                    '[)'
                ) WITH &&
            )
            """
        )


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute(
            "ALTER TABLE campaign_delivery_windows DROP CONSTRAINT IF EXISTS campaign_delivery_windows_no_overlap"
        )

    op.drop_index("idx_windows_campaign", table_name="campaign_delivery_windows")
    op.drop_index("uniq_windows_default", table_name="campaign_delivery_windows")
    op.drop_index("uniq_windows_signature", table_name="campaign_delivery_windows")
    op.drop_table("campaign_delivery_windows")
