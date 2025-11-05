"""Create campaign_audit_log table

Revision ID: e7c8c9d945f0
Revises: b3b827c4bc53
Create Date: 2025-10-28 23:13:16.466532

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "e7c8c9d945f0"
down_revision: Union[str, Sequence[str], None] = "b3b827c4bc53"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create campaign_audit_log (SCHEMA.md §CampaignAuditLog)."""

    payload_type = sa.JSON().with_variant(
        postgresql.JSONB(astext_type=sa.Text()), "postgresql"
    )

    op.create_table(
        "campaign_audit_log",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("campaign_id", sa.Integer(), nullable=True),
        sa.Column("actor_id", sa.Integer(), nullable=True),
        sa.Column("action", sa.String(length=64), nullable=False),
        sa.Column("payload", payload_type, nullable=False),
        sa.Column("idempotency_key", sa.String(length=128), nullable=True),
        sa.Column("request_hash", sa.String(length=128), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.CheckConstraint(
            "action IN ('campaign.create','campaign.update','campaign.activate','campaign.pause','campaign.resume','campaign.stop','step.upsert','window.upsert','caps.upsert','cooldown.upsert','run.schedule','opt_out.create','notification.send')",
            name="campaign_audit_action_chk",
        ),
    )

    op.create_index(
        "uniq_audit_idempotency",
        "campaign_audit_log",
        ["campaign_id", "action", "idempotency_key"],
        unique=True,
        postgresql_where=sa.text("idempotency_key IS NOT NULL"),
        sqlite_where=sa.text("idempotency_key IS NOT NULL"),
    )
    op.create_index(
        "idx_audit_created",
        "campaign_audit_log",
        ["campaign_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "idx_audit_action",
        "campaign_audit_log",
        ["action", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("idx_audit_action", table_name="campaign_audit_log")
    op.drop_index("idx_audit_created", table_name="campaign_audit_log")
    op.drop_index("uniq_audit_idempotency", table_name="campaign_audit_log")
    op.drop_table("campaign_audit_log")
