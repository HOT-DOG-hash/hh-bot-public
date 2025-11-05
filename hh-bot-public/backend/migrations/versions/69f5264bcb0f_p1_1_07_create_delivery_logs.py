"""Create campaign_delivery_logs table

Revision ID: 69f5264bcb0f
Revises: dde2e34cc17f
Create Date: 2025-10-28 23:12:27.199761

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "69f5264bcb0f"
down_revision: Union[str, Sequence[str], None] = "dde2e34cc17f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create campaign_delivery_logs (SCHEMA.md §DeliveryLogs)."""

    payload_type = sa.JSON().with_variant(
        postgresql.JSONB(astext_type=sa.Text()), "postgresql"
    )

    op.create_table(
        "campaign_delivery_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("campaign_id", sa.Integer(), nullable=False),
        sa.Column("campaign_run_id", sa.Integer(), nullable=True),
        sa.Column("step_id", sa.Integer(), nullable=True),
        sa.Column("vacancy_id", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("response_payload", payload_type, nullable=True),
        sa.Column("attempted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("error_code", sa.String(length=64), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.CheckConstraint(
            "status IN ('sent','failed','skipped')",
            name="delivery_logs_status_chk",
        ),
        sa.CheckConstraint(
            "status <> 'failed' OR error_code IS NOT NULL",
            name="delivery_logs_failed_error_chk",
        ),
    )

    op.create_index(
        "uniq_delivery_guard",
        "campaign_delivery_logs",
        ["campaign_id", "vacancy_id", "step_id"],
        unique=True,
    )
    op.create_index(
        "idx_delivery_attempted",
        "campaign_delivery_logs",
        ["campaign_id", "attempted_at"],
        unique=False,
    )
    op.create_index(
        "idx_delivery_status",
        "campaign_delivery_logs",
        ["status", "attempted_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("idx_delivery_status", table_name="campaign_delivery_logs")
    op.drop_index("idx_delivery_attempted", table_name="campaign_delivery_logs")
    op.drop_index("uniq_delivery_guard", table_name="campaign_delivery_logs")
    op.drop_table("campaign_delivery_logs")
