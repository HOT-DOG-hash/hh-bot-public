"""create payment_events table

Revision ID: p1_0_payment_events
Revises: p0_4_user_applications
Create Date: 2025-10-22 10:00:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from backend.app.models.base import UUIDType

revision: str = "p1_0_payment_events"
down_revision: str | Sequence[str] | None = "p0_4_user_applications"
branch_labels = None
depends_on = None

EVENT_TYPE_VALUES = ['payment.waiting_for_capture', 'payment.pending', 'payment.succeeded', 'payment.canceled', 'payment.failed']

def _is_postgres() -> bool:
    bind = op.get_bind()
    return bind.dialect.name in {"postgresql", "postgres", "psycopg"}

def _create_pg_enum(name: str, values: list[str]) -> None:
    if not _is_postgres():
        return
    values_sql = ", ".join(f"'{value}'" for value in values)
    dollar = chr(36)
    sql = (
        f"DO {dollar}{dollar}
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
        f"{dollar}{dollar};"
    )
    op.execute(sql)

def _drop_pg_enum(name: str) -> None:
    if not _is_postgres():
        return
    dollar = chr(36)
    sql = (
        f"DO {dollar}{dollar}
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
        f"{dollar}{dollar};"
    )
    op.execute(sql)

def upgrade() -> None:
    _create_pg_enum("payment_event_type_enum", EVENT_TYPE_VALUES)

    op.create_table(
        "payment_events",
        sa.Column("id", UUIDType(), primary_key=True),
        sa.Column(
            "payment_id",
            UUIDType(),
            sa.ForeignKey("payments.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("provider_event_id", sa.Text(), nullable=False),
        sa.Column(
            "event_type",
            sa.Enum(
                *EVENT_TYPE_VALUES,
                name="payment_event_type_enum",
                native_enum=False,
            ),
            nullable=False,
        ),
        sa.Column("payload", sa.JSON(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.UniqueConstraint("provider_event_id", name="uq_payment_events_provider_event_id"),
    )

    op.create_index(
        "ix_payment_events_payment_created",
        "payment_events",
        ["payment_id", "created_at"],
        unique=False,
    )

def downgrade() -> None:
    op.drop_index("ix_payment_events_payment_created", table_name="payment_events")
    op.drop_table("payment_events")
    _drop_pg_enum("payment_event_type_enum")
