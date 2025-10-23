"""create payment_attempts table

Revision ID: p1_1_payment_attempts
Revises: p1_0_payment_events
Create Date: 2025-10-22 10:05:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from backend.app.models.base import UUIDType

revision: str = "p1_1_payment_attempts"
down_revision: str | Sequence[str] | None = "p1_0_payment_events"
branch_labels = None
depends_on = None

PHASE_VALUES = ['init', 'provider_call', 'webhook', 'retry', 'final']


def _is_postgres() -> bool:
    bind = op.get_bind()
    return bind.dialect.name in {"postgresql", "postgres", "psycopg"}


def _create_pg_enum(name: str, values: list[str]) -> None:
    if not _is_postgres():
        return
    values_sql = ", ".join(f"'{value}'" for value in values)
    op.execute(
        f"DO $$
"
        "BEGIN
"
        f"    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = '{name}') THEN
"
        f"        CREATE TYPE {name} AS ENUM ({values_sql});
"
        "    END IF;
"
        "END
"
        f"$$;"
    )


def _drop_pg_enum(name: str) -> None:
    if not _is_postgres():
        return
    op.execute(
        f"DO $$
"
        "BEGIN
"
        f"    IF EXISTS (SELECT 1 FROM pg_type WHERE typname = '{name}') THEN
"
        f"        DROP TYPE {name};
"
        "    END IF;
"
        "END
"
        f"$$;"
    )


def upgrade() -> None:
    _create_pg_enum("payment_attempt_phase_enum", PHASE_VALUES)

    op.create_table(
        "payment_attempts",
        sa.Column("id", UUIDType(), primary_key=True),
        sa.Column(
            "payment_id",
            UUIDType(),
            sa.ForeignKey("payments.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "phase",
            sa.Enum(
                *PHASE_VALUES,
                name="payment_attempt_phase_enum",
                native_enum=False,
            ),
            nullable=False,
        ),
        sa.Column("attempt_no", sa.Integer(), nullable=False),
        sa.Column("ok", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=False),
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
            server_onupdate=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.UniqueConstraint(
            "payment_id",
            "phase",
            "attempt_no",
            name="uq_payment_attempts_phase_order",
        ),
    )

    op.create_index(
        "ix_payment_attempts_payment_phase",
        "payment_attempts",
        ["payment_id", "phase"],
        unique=False,
    )
    op.create_index(
        "ix_payment_attempts_phase_updated",
        "payment_attempts",
        ["phase", "updated_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_payment_attempts_phase_updated", table_name="payment_attempts")
    op.drop_index("ix_payment_attempts_payment_phase", table_name="payment_attempts")
    op.drop_table("payment_attempts")
    _drop_pg_enum("payment_attempt_phase_enum")
