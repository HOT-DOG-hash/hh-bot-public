"""Create campaign_runs table

Revision ID: dde2e34cc17f
Revises: 9d24fe35c583
Create Date: 2025-10-28 23:12:14.131635

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "dde2e34cc17f"
down_revision: Union[str, Sequence[str], None] = "9d24fe35c583"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create campaign_runs (SCHEMA.md §CampaignRuns)."""

    op.create_table(
        "campaign_runs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("campaign_id", sa.Integer(), nullable=False),
        sa.Column("run_started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("run_finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("scheduled_by", sa.String(length=16), nullable=False, server_default=sa.text("'system'")),
        sa.Column("status", sa.String(length=16), nullable=False, server_default=sa.text("'success'")),
        sa.Column("sent_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("error_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("skipped_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("delay_applied_ms", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.CheckConstraint(
            "run_finished_at IS NULL OR run_finished_at >= run_started_at",
            name="campaign_runs_time_order_chk",
        ),
        sa.CheckConstraint("sent_count >= 0", name="campaign_runs_sent_nonneg_chk"),
        sa.CheckConstraint("error_count >= 0", name="campaign_runs_error_nonneg_chk"),
        sa.CheckConstraint("skipped_count >= 0", name="campaign_runs_skipped_nonneg_chk"),
        sa.CheckConstraint(
            "scheduled_by IN ('system','user')",
            name="campaign_runs_scheduled_by_chk",
        ),
        sa.CheckConstraint(
            "status IN ('success','failed','skipped')",
            name="campaign_runs_status_chk",
        ),
    )

    op.create_index(
        "idx_runs_campaign_started",
        "campaign_runs",
        ["campaign_id", "run_started_at"],
        unique=False,
    )
    op.create_index(
        "idx_runs_status",
        "campaign_runs",
        ["status", "run_started_at"],
        unique=False,
    )
    op.create_index(
        "idx_runs_delay",
        "campaign_runs",
        ["campaign_id", "delay_applied_ms"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("idx_runs_delay", table_name="campaign_runs")
    op.drop_index("idx_runs_status", table_name="campaign_runs")
    op.drop_index("idx_runs_campaign_started", table_name="campaign_runs")
    op.drop_table("campaign_runs")
