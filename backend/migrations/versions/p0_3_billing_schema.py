"""billing core schema for plans, subscriptions, payments, quotas

Revision ID: p0_3_billing_schema
Revises: 20251020_0002_billing_indexes
Create Date: 2025-11-07 12:00:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "p0_3_billing_schema"
down_revision: str | Sequence[str] | None = "20251020_0002_billing_indexes"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _drop_table_if_exists(table_name: str) -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if table_name in inspector.get_table_names():
        op.drop_table(table_name)


def _create_enums() -> tuple[sa.Enum, sa.Enum, sa.Enum, sa.Enum]:
    bind = op.get_bind()
    dialect = bind.dialect.name
    is_postgres = dialect in {"postgresql", "postgres", "psycopg"}

    plan_period_enum = sa.Enum("trial", "week", "month", name="plan_period_enum")
    subscription_status_enum = sa.Enum(
        "trialing", "active", "past_due", "canceled", "expired", name="subscription_status_enum"
    )
    payment_status_enum = sa.Enum(
        "pending", "succeeded", "canceled", "expired", "failed", name="payment_status_enum"
    )
    provider_enum = sa.Enum("yoomoney", name="provider_enum")

    if is_postgres:
        plan_period_enum.create(bind, checkfirst=True)
        subscription_status_enum.create(bind, checkfirst=True)
        payment_status_enum.create(bind, checkfirst=True)
        provider_enum.create(bind, checkfirst=True)

    return plan_period_enum, subscription_status_enum, payment_status_enum, provider_enum


def _drop_enums() -> None:
    bind = op.get_bind()
    if bind.dialect.name in {"postgresql", "postgres", "psycopg"}:
        for enum_name in (
            "provider_enum",
            "payment_status_enum",
            "subscription_status_enum",
            "plan_period_enum",
        ):
            op.execute(sa.text(f"DROP TYPE IF EXISTS {enum_name}"))


def upgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name
    is_postgres = dialect in {"postgresql", "postgres", "psycopg"}

    _drop_table_if_exists("payments")
    _drop_table_if_exists("subscriptions")
    _drop_table_if_exists("application_quotas")
    _drop_table_if_exists("plans")

    (
        plan_period_enum,
        subscription_status_enum,
        payment_status_enum,
        provider_enum,
    ) = _create_enums()

    op.create_table(
        "plans",
        sa.Column("code", sa.Text(), primary_key=True),
        sa.Column("period", plan_period_enum, nullable=False),
        sa.Column("is_recurring", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("amount_minor", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default=sa.text("'RUB'")),
        sa.Column("granted_quota", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("non_renewable", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("display_name", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("provider_product_id", sa.Text(), nullable=True),
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
    )
    op.create_index("ix_plans_period", "plans", ["period"])  # type: ignore[arg-type]
    op.create_index("ix_plans_is_recurring", "plans", ["is_recurring"])

    if is_postgres:
        uuid_type: sa.TypeEngine = sa.dialects.postgresql.UUID(as_uuid=True)
        json_type: sa.TypeEngine = sa.dialects.postgresql.JSONB(astext_type=sa.Text())
    else:
        uuid_type = sa.String(length=36)
        json_type = sa.JSON()

    uuid_default = sa.text("gen_random_uuid()") if is_postgres else None
    user_fk_type = sa.Integer()

    op.create_table(
        "subscriptions",
        sa.Column(
            "id",
            uuid_type,
            primary_key=True,
            nullable=False,
            server_default=uuid_default,
        ),
        sa.Column(
            "user_id",
            user_fk_type,
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "plan_code",
            sa.Text(),
            sa.ForeignKey("plans.code", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("status", subscription_status_enum, nullable=False),
        sa.Column(
            "current_period_start",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column("current_period_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("next_charge_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancel_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "cancel_at_period_end",
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
            server_onupdate=sa.text("CURRENT_TIMESTAMP"),
        ),
    )
    op.create_index("ix_subscriptions_user_status", "subscriptions", ["user_id", "status"])
    op.create_index(
        "ix_subscriptions_user_next_charge", "subscriptions", ["user_id", "next_charge_at"]
    )

    op.create_table(
        "payments",
        sa.Column(
            "id",
            uuid_type,
            primary_key=True,
            nullable=False,
            server_default=uuid_default,
        ),
        sa.Column(
            "user_id",
            user_fk_type,
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "subscription_id",
            uuid_type,
            sa.ForeignKey("subscriptions.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "plan_code",
            sa.Text(),
            sa.ForeignKey("plans.code", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("provider", provider_enum, nullable=False),
        sa.Column("provider_payment_id", sa.Text(), nullable=True),
        sa.Column("idempotency_key", sa.Text(), nullable=False),
        sa.Column("amount_minor", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default=sa.text("'RUB'")),
        sa.Column("status", payment_status_enum, nullable=False),
        sa.Column("raw", json_type, nullable=True),
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
        sa.UniqueConstraint("provider_payment_id", name="uq_payments_provider_payment_id"),
        sa.UniqueConstraint("idempotency_key", name="uq_payments_idempotency_key"),
    )
    op.create_index("ix_payments_user_created", "payments", ["user_id", "created_at"])
    op.create_index("ix_payments_status_created", "payments", ["status", "created_at"])

    op.create_table(
        "application_quotas",
        sa.Column(
            "id",
            uuid_type,
            primary_key=True,
            nullable=False,
            server_default=uuid_default,
        ),
        sa.Column(
            "user_id",
            user_fk_type,
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "plan_code",
            sa.Text(),
            sa.ForeignKey("plans.code", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("granted", sa.Integer(), nullable=False),
        sa.Column("consumed", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column(
            "non_renewable",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column("activated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("exhausted_at", sa.DateTime(timezone=True), nullable=True),
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
        sa.CheckConstraint(
            "consumed >= 0 AND consumed <= granted",
            name="ck_application_quotas_consumed_range",
        ),
    )
    op.create_index("ix_application_quotas_user_id", "application_quotas", ["user_id"])
    op.create_index("ix_application_quotas_exhausted", "application_quotas", ["exhausted_at"])
    op.create_index(
        "uq_application_quotas_trial_once_per_user",
        "application_quotas",
        ["user_id"],
        unique=True,
        postgresql_where=sa.text("plan_code = 'FREE_TRIAL'"),
    )

    op.execute(
        sa.text(
            """
            INSERT INTO plans (
                code, period, is_recurring, amount_minor, currency,
                granted_quota, non_renewable, display_name, description, provider_product_id
            ) VALUES
                ('FREE_TRIAL', 'trial', false, 0, 'RUB', 10, true, 'Free Trial', 'Trial plan with 10 applications.', NULL),
                ('WEEKLY', 'week', true, 69000, 'RUB', 0, false, 'Weekly Premium', 'Weekly recurring premium plan.', NULL),
                ('MONTHLY', 'month', true, 190000, 'RUB', 0, false, 'Monthly Premium', 'Monthly recurring premium plan.', NULL)
            ON CONFLICT (code) DO NOTHING
            """
        )
    )


def downgrade() -> None:
    op.drop_index("uq_application_quotas_trial_once_per_user", table_name="application_quotas")
    op.drop_index("ix_application_quotas_exhausted", table_name="application_quotas")
    op.drop_index("ix_application_quotas_user_id", table_name="application_quotas")
    op.drop_table("application_quotas")

    op.drop_index("ix_payments_status_created", table_name="payments")
    op.drop_index("ix_payments_user_created", table_name="payments")
    op.drop_table("payments")

    op.drop_index("ix_subscriptions_user_next_charge", table_name="subscriptions")
    op.drop_index("ix_subscriptions_user_status", table_name="subscriptions")
    op.drop_table("subscriptions")

    op.drop_index("ix_plans_is_recurring", table_name="plans")
    op.drop_index("ix_plans_period", table_name="plans")
    op.drop_table("plans")

    _drop_enums()
