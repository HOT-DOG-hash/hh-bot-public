"""billing indexes and plan column

Revision ID: 20251020_0002_billing_indexes
Revises: 20251020_0001_core_tables
Create Date: 2025-10-20 18:30:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20251020_0002_billing_indexes"
down_revision: str | Sequence[str] | None = "20251020_0001_core_tables"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name
    is_sqlite = dialect == "sqlite"

    op.add_column(
        "payments",
        sa.Column(
            "plan", sa.String(length=64), nullable=False, server_default=sa.text("'premium-month'")
        ),
    )
    op.execute("UPDATE payments SET plan = COALESCE(payload_json->>'plan', 'premium-month')")
    if not is_sqlite:
        op.alter_column("payments", "plan", server_default=None)

    # заменить ограничение на provider/external_id глобальным unique по external_id
    with op.batch_alter_table("payments") as batch_op:
        batch_op.drop_constraint("uq_payments_provider_external_id", type_="unique")
        batch_op.create_unique_constraint("uq_payments_external_id", ["external_id"])
    op.create_index(
        "ix_payments_user_status_created", "payments", ["user_id", "status", "created_at"]
    )

    with op.batch_alter_table("subscriptions") as batch_op:
        batch_op.drop_constraint("uq_subscriptions_user_plan", type_="unique")
    op.create_index("ix_subscriptions_user_status", "subscriptions", ["user_id", "status"])
    op.add_column(
        "subscriptions",
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )
    op.execute(
        "UPDATE subscriptions SET active = CASE WHEN status = 'active' THEN true ELSE false END"
    )
    if not is_sqlite:
        op.alter_column("subscriptions", "active", server_default=None)
    op.create_index(
        "uq_subscriptions_active_user_plan",
        "subscriptions",
        ["user_id", "plan", "active"],
        unique=True,
        postgresql_where=sa.text("active = true"),
    )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())

    if "subscriptions" in tables:
        if bind.dialect.name in {"postgresql", "postgres", "psycopg"}:
            op.execute(sa.text("DROP INDEX IF EXISTS uq_subscriptions_active_user_plan"))
            op.execute(sa.text("DROP INDEX IF EXISTS ix_subscriptions_user_status"))
        else:
            op.drop_index("uq_subscriptions_active_user_plan", table_name="subscriptions")
            op.drop_index("ix_subscriptions_user_status", table_name="subscriptions")
        with op.batch_alter_table("subscriptions") as batch_op:
            batch_op.create_unique_constraint("uq_subscriptions_user_plan", ["user_id", "plan"])
        op.drop_column("subscriptions", "active")

    if "payments" in tables:
        op.drop_index("ix_payments_user_status_created", table_name="payments")
        with op.batch_alter_table("payments") as batch_op:
            batch_op.drop_constraint("uq_payments_external_id", type_="unique")
            batch_op.create_unique_constraint(
                "uq_payments_provider_external_id", ["provider", "external_id"]
            )
        op.drop_column("payments", "plan")
