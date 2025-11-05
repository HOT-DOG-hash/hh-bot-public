"""create campaigns table

Revision ID: p1_1_01
Revises: p1_1
Create Date: 2025-10-28 22:30:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "p1_1_01"
down_revision: Union[str, Sequence[str], None] = "p1_1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Создаёт таблицу campaigns в соответствии с SCHEMA.md (Campaigns — P1.1).
    На этом шаге фиксируются базовые поля кампании и инварианты статусов/лимитов.
    FK на delivery windows / cooldown policies будут добавлены в завершающей ревизии.
    """
    op.create_table(
        "campaigns",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("owner_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("mode", sa.String(length=16), nullable=False),
        sa.Column("daily_quota_target", sa.Integer(), nullable=False, server_default=sa.text("10")),
        sa.Column("default_window_id", sa.Integer(), nullable=True),
        sa.Column("cooldown_policy_id", sa.Integer(), nullable=True),
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
            "status IN ('draft','active','paused','archived')",
            name="campaigns_status_chk",
        ),
        sa.CheckConstraint("mode IN ('strict','wide')", name="campaigns_mode_chk"),
        sa.CheckConstraint("daily_quota_target >= 1", name="campaigns_daily_quota_chk"),
    )

    op.create_index(
        "idx_campaigns_owner_status",
        "campaigns",
        ["owner_id", "status"],
        unique=False,
    )
    op.create_index(
        "idx_campaigns_owner_updated",
        "campaigns",
        ["owner_id", "updated_at"],
        unique=False,
    )
    op.create_index(
        "uniq_campaign_owner_active",
        "campaigns",
        ["owner_id"],
        unique=True,
        postgresql_where=sa.text("status = 'active'"),
        sqlite_where=sa.text("status = 'active'"),
    )


def downgrade() -> None:
    """
    Удаляет таблицу campaigns и связанные индексы.
    """
    op.drop_index("uniq_campaign_owner_active", table_name="campaigns")
    op.drop_index("idx_campaigns_owner_updated", table_name="campaigns")
    op.drop_index("idx_campaigns_owner_status", table_name="campaigns")
    op.drop_table("campaigns")
