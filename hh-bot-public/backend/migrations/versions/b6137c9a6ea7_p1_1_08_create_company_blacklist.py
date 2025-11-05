"""Create campaign_company_blacklist table

Revision ID: b6137c9a6ea7
Revises: 69f5264bcb0f
Create Date: 2025-10-28 23:12:40.181364

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b6137c9a6ea7"
down_revision: Union[str, Sequence[str], None] = "69f5264bcb0f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create campaign_company_blacklist (SCHEMA.md §CompanyBlacklist)."""

    op.create_table(
        "campaign_company_blacklist",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("owner_id", sa.Integer(), nullable=False),
        sa.Column("company_name", sa.String(length=255), nullable=False),
        sa.Column("company_id_external", sa.String(length=255), nullable=True),
        sa.Column("reason", sa.String(length=255), nullable=True),
        sa.Column(
            "added_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column("removed_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "company_name <> '' OR company_id_external IS NOT NULL",
            name="company_blacklist_identifier_chk",
        ),
        sa.CheckConstraint(
            "removed_at IS NULL OR removed_at >= added_at",
            name="company_blacklist_removed_at_chk",
        ),
    )

    op.create_index(
        "uniq_blacklist_name",
        "campaign_company_blacklist",
        ["owner_id", "company_name"],
        unique=True,
    )
    op.create_index(
        "uniq_blacklist_external",
        "campaign_company_blacklist",
        ["owner_id", "company_id_external"],
        unique=True,
        postgresql_where=sa.text("company_id_external IS NOT NULL"),
        sqlite_where=sa.text("company_id_external IS NOT NULL"),
    )
    op.create_index(
        "idx_blacklist_owner",
        "campaign_company_blacklist",
        ["owner_id", "added_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("idx_blacklist_owner", table_name="campaign_company_blacklist")
    op.drop_index("uniq_blacklist_external", table_name="campaign_company_blacklist")
    op.drop_index("uniq_blacklist_name", table_name="campaign_company_blacklist")
    op.drop_table("campaign_company_blacklist")
