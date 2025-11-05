"""create payment schema

Revision ID: p0_3
Revises: 20250924_unify_schema
Create Date: 2025-10-24 13:35:48.896251

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "p0_3"
down_revision: Union[str, Sequence[str], None] = "20250924_unify_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


CURRENT_TS = sa.text("CURRENT_TIMESTAMP")


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "plans",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("amount_minor", sa.Integer(), nullable=False),
        sa.Column("amount", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default="RUB"),
        sa.Column("duration_days", sa.SmallInteger(), nullable=False, server_default=sa.text("0")),
        sa.Column("granted_quota", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=CURRENT_TS),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True, server_default=CURRENT_TS),
    )
    op.create_index("ix_plans_code", "plans", ["code"], unique=True)

    op.create_table(
        "subscriptions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column(
            "plan_code",
            sa.String(length=50),
            sa.ForeignKey("plans.code", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Enum("trial", "active", "grace", "expired", "canceled", name="subscription_status"),
            nullable=False,
            server_default=sa.text("'trial'"),
        ),
        sa.Column("current_period_start", sa.DateTime(timezone=True), nullable=False, server_default=CURRENT_TS),
        sa.Column("current_period_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("next_charge_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancel_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancel_at_period_end", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=CURRENT_TS),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True, server_default=CURRENT_TS),
    )
    op.create_index("ix_subscriptions_user_id", "subscriptions", ["user_id"])
    op.create_index("ix_subscriptions_plan_code", "subscriptions", ["plan_code"])

    op.create_table(
        "users_trials",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column(
            "plan_code",
            sa.String(length=50),
            sa.ForeignKey("plans.code", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("activated_at", sa.DateTime(timezone=True), nullable=False, server_default=CURRENT_TS),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("granted_quota", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("consumed_quota", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=CURRENT_TS),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True, server_default=CURRENT_TS),
    )

    op.create_table(
        "payment_methods",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column(
            "provider",
            sa.Enum("yoomoney", name="payment_method_provider"),
            nullable=False,
            server_default=sa.text("'yoomoney'"),
        ),
        sa.Column("external_id", sa.String(length=128), nullable=False),
        sa.Column("masked_pan", sa.String(length=32), nullable=True),
        sa.Column("is_default", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("raw", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=CURRENT_TS),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True, server_default=CURRENT_TS),
        sa.UniqueConstraint("external_id", name="uq_payment_methods_external_id"),
    )
    op.create_index("ix_payment_methods_user_id", "payment_methods", ["user_id"])

    op.create_table(
        "payments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column(
            "plan_code",
            sa.String(length=50),
            sa.ForeignKey("plans.code", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "provider",
            sa.Enum("yoomoney", name="payment_provider"),
            nullable=False,
            server_default=sa.text("'yoomoney'"),
        ),
        sa.Column("payment_method_id", sa.Integer(), sa.ForeignKey("payment_methods.id", ondelete="SET NULL"), nullable=True),
        sa.Column("subscription_id", sa.Integer(), sa.ForeignKey("subscriptions.id", ondelete="SET NULL"), nullable=True),
        sa.Column("idempotency_key", sa.String(length=64), nullable=False, unique=True),
        sa.Column("provider_payment_id", sa.String(length=128), nullable=True, unique=True),
        sa.Column("amount_minor", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default="RUB"),
        sa.Column(
            "status",
            sa.Enum("initiated", "pending", "succeeded", "failed", "canceled", "expired", name="payment_status"),
            nullable=False,
            server_default=sa.text("'initiated'"),
        ),
        sa.Column("invoice_pdf_url", sa.String(length=1024), nullable=True),
        sa.Column("raw", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=CURRENT_TS),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True, server_default=CURRENT_TS),
    )
    op.create_index("ix_payments_user_id", "payments", ["user_id"])
    op.create_index("ix_payments_plan_code", "payments", ["plan_code"])

    op.create_table(
        "payment_attempts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("payment_id", sa.Integer(), sa.ForeignKey("payments.id", ondelete="CASCADE"), nullable=False),
        sa.Column(
            "provider",
            sa.Enum("yoomoney", name="payment_attempt_provider"),
            nullable=False,
            server_default=sa.text("'yoomoney'"),
        ),
        sa.Column(
            "status",
            sa.Enum("initiated", "pending", "succeeded", "failed", "canceled", "expired", name="payment_attempt_status"),
            nullable=False,
            server_default=sa.text("'initiated'"),
        ),
        sa.Column("idempotency_key", sa.String(length=64), nullable=False),
        sa.Column("attempt_number", sa.Integer(), nullable=False, server_default=sa.text("1")),
        sa.Column("next_retry_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("raw", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=CURRENT_TS),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True, server_default=CURRENT_TS),
        sa.UniqueConstraint("payment_id", "attempt_number", name="uq_payment_attempt_idx"),
    )
    op.create_index("ix_payment_attempts_payment_id", "payment_attempts", ["payment_id"])

    op.create_table(
        "payment_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("payment_id", sa.Integer(), sa.ForeignKey("payments.id", ondelete="CASCADE"), nullable=False),
        sa.Column("provider_event_id", sa.String(length=128), nullable=False),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=True),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False, server_default=CURRENT_TS),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=CURRENT_TS),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True, server_default=CURRENT_TS),
        sa.UniqueConstraint("provider_event_id", name="uq_payment_events_provider_event_id"),
    )
    op.create_index("ix_payment_events_payment_id", "payment_events", ["payment_id"])

    op.create_table(
        "application_quotas",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column(
            "plan_code",
            sa.String(length=50),
            sa.ForeignKey("plans.code", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("daily_limit", sa.Integer(), nullable=False, server_default=sa.text("200")),
        sa.Column("daily_used", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("trial_limit", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("trial_used", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=CURRENT_TS),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True, server_default=CURRENT_TS),
    )

    op.create_table(
        "settings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("strict_mode", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("workday_start_hour", sa.SmallInteger(), nullable=False, server_default=sa.text("6")),
        sa.Column("workday_end_hour", sa.SmallInteger(), nullable=False, server_default=sa.text("24")),
        sa.Column("preferred_gender", sa.String(length=10), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=CURRENT_TS),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True, server_default=CURRENT_TS),
    )

    op.create_table(
        "companies_blacklist",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("company_name", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=CURRENT_TS),
    )
    op.create_index("ix_companies_blacklist_user_id", "companies_blacklist", ["user_id"])

    op.add_column(
        "search_queries",
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True, server_default=CURRENT_TS),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("search_queries", "updated_at")
    op.drop_index("ix_companies_blacklist_user_id", table_name="companies_blacklist")
    op.drop_table("companies_blacklist")
    op.drop_table("settings")
    op.drop_table("application_quotas")
    op.drop_index("ix_payment_events_payment_id", table_name="payment_events")
    op.drop_table("payment_events")
    op.drop_index("ix_payment_attempts_payment_id", table_name="payment_attempts")
    op.drop_table("payment_attempts")
    op.drop_index("ix_payments_plan_code", table_name="payments")
    op.drop_index("ix_payments_user_id", table_name="payments")
    op.drop_table("payments")
    op.drop_table("payment_methods")
    op.drop_table("users_trials")
    op.drop_index("ix_subscriptions_plan_code", table_name="subscriptions")
    op.drop_index("ix_subscriptions_user_id", table_name="subscriptions")
    op.drop_table("subscriptions")
    op.drop_index("ix_plans_code", table_name="plans")
    op.drop_table("plans")

    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        # Remove ENUM types so subsequent upgrades can recreate them cleanly.
        for enum_name in (
            "payment_attempt_status",
            "payment_attempt_provider",
            "payment_status",
            "payment_provider",
            "payment_method_provider",
            "subscription_status",
        ):
            op.execute(sa.text(f'DROP TYPE IF EXISTS "{enum_name}"'))
