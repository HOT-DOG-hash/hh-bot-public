"""Finalize campaign indexes and foreign keys

Revision ID: 78948d3ca604
Revises: e7c8c9d945f0
Create Date: 2025-10-28 23:13:07.167204

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "78948d3ca604"
down_revision: Union[str, Sequence[str], None] = "e7c8c9d945f0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _fk_exists(inspector: sa.inspect, table: str, name: str) -> bool:
    return any(fk["name"] == name for fk in inspector.get_foreign_keys(table))


def upgrade() -> None:
    """Add deferrable foreign keys and final indexes (SCHEMA.md §Campaigns - finalize)."""

    bind = op.get_bind()
    inspector = sa.inspect(bind)
    is_sqlite = bind.dialect.name == "sqlite"

    fk_definitions = [
        ("fk_campaigns_owner", "campaigns", "users", ["owner_id"], ["id"], {"ondelete": "CASCADE", "deferrable": True, "initially": "DEFERRED"}),
        ("fk_campaigns_default_window", "campaigns", "campaign_delivery_windows", ["default_window_id"], ["id"], {"ondelete": "SET NULL", "deferrable": True, "initially": "IMMEDIATE"}),
        ("fk_campaigns_cooldown_policy", "campaigns", "campaign_cooldown_policies", ["cooldown_policy_id"], ["id"], {"ondelete": "SET NULL", "deferrable": True, "initially": "IMMEDIATE"}),
        ("fk_delivery_windows_campaign", "campaign_delivery_windows", "campaigns", ["campaign_id"], ["id"], {"ondelete": "CASCADE", "deferrable": True, "initially": "DEFERRED"}),
        ("fk_steps_campaign", "campaign_steps", "campaigns", ["campaign_id"], ["id"], {"ondelete": "CASCADE", "deferrable": True, "initially": "DEFERRED"}),
        ("fk_steps_delivery_window", "campaign_steps", "campaign_delivery_windows", ["delivery_window_id"], ["id"], {"ondelete": "RESTRICT", "deferrable": True, "initially": "DEFERRED"}),
        ("fk_frequency_caps_campaign", "campaign_frequency_caps", "campaigns", ["campaign_id"], ["id"], {"ondelete": "CASCADE", "deferrable": True, "initially": "DEFERRED"}),
        ("fk_cooldown_campaign", "campaign_cooldown_policies", "campaigns", ["campaign_id"], ["id"], {"ondelete": "CASCADE", "deferrable": True, "initially": "DEFERRED"}),
        ("fk_runs_campaign", "campaign_runs", "campaigns", ["campaign_id"], ["id"], {"ondelete": "CASCADE", "deferrable": True, "initially": "DEFERRED"}),
        ("fk_delivery_logs_campaign", "campaign_delivery_logs", "campaigns", ["campaign_id"], ["id"], {"ondelete": "CASCADE", "deferrable": True, "initially": "DEFERRED"}),
        ("fk_delivery_logs_run", "campaign_delivery_logs", "campaign_runs", ["campaign_run_id"], ["id"], {"ondelete": "CASCADE", "deferrable": True, "initially": "DEFERRED"}),
        ("fk_delivery_logs_step", "campaign_delivery_logs", "campaign_steps", ["step_id"], ["id"], {"ondelete": "SET NULL", "deferrable": True, "initially": "DEFERRED"}),
        ("fk_blacklist_owner", "campaign_company_blacklist", "users", ["owner_id"], ["id"], {"ondelete": "CASCADE", "deferrable": True, "initially": "DEFERRED"}),
        ("fk_opt_out_owner", "campaign_user_opt_out", "users", ["owner_id"], ["id"], {"ondelete": "CASCADE", "deferrable": True, "initially": "DEFERRED"}),
        ("fk_notifications_campaign", "campaign_notifications", "campaigns", ["campaign_id"], ["id"], {"ondelete": "CASCADE", "deferrable": True, "initially": "DEFERRED"}),
        ("fk_audit_log_campaign", "campaign_audit_log", "campaigns", ["campaign_id"], ["id"], {"ondelete": "CASCADE", "deferrable": True, "initially": "DEFERRED"}),
        ("fk_audit_log_actor", "campaign_audit_log", "users", ["actor_id"], ["id"], {"ondelete": "SET NULL", "deferrable": True, "initially": "DEFERRED"}),
    ]

    for name, source, target, local_cols, remote_cols, options in fk_definitions:
        if not _fk_exists(inspector, source, name):
            if is_sqlite:
                with op.batch_alter_table(source, recreate="auto") as batch_op:
                    batch_op.create_foreign_key(name, target, local_cols, remote_cols, **{k: v for k, v in options.items() if k in {"ondelete"}})
            else:
                op.create_foreign_key(name, source, target, local_cols, remote_cols, **options)

    # message_templates table присутствует не во всех окружениях; добавляем FK, если есть
    if "message_templates" in inspector.get_table_names():
        if not _fk_exists(inspector, "campaign_steps", "fk_steps_message_template"):
            if is_sqlite:
                with op.batch_alter_table("campaign_steps", recreate="auto") as batch_op:
                    batch_op.create_foreign_key(
                        "fk_steps_message_template",
                        "message_templates",
                        ["message_template_id"],
                        ["id"],
                        ondelete="RESTRICT",
                    )
            else:
                op.create_foreign_key(
                    "fk_steps_message_template",
                    "campaign_steps",
                    "message_templates",
                    ["message_template_id"],
                    ["id"],
                    ondelete="RESTRICT",
                    deferrable=True,
                    initially="DEFERRED",
                )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    is_sqlite = bind.dialect.name == "sqlite"

    fk_names = [
        "fk_steps_message_template",
        "fk_audit_log_actor",
        "fk_audit_log_campaign",
        "fk_notifications_campaign",
        "fk_opt_out_owner",
        "fk_blacklist_owner",
        "fk_delivery_logs_step",
        "fk_delivery_logs_run",
        "fk_delivery_logs_campaign",
        "fk_runs_campaign",
        "fk_cooldown_campaign",
        "fk_frequency_caps_campaign",
        "fk_steps_delivery_window",
        "fk_steps_campaign",
        "fk_delivery_windows_campaign",
        "fk_campaigns_cooldown_policy",
        "fk_campaigns_default_window",
        "fk_campaigns_owner",
    ]

    for name in fk_names:
        # drop only if constraint exists to keep downgrade idempotent
        source_table = None
        for table in inspector.get_table_names():
            if any(fk["name"] == name for fk in inspector.get_foreign_keys(table)):
                source_table = table
                break
        if source_table:
            if is_sqlite:
                with op.batch_alter_table(source_table, recreate="auto") as batch_op:
                    batch_op.drop_constraint(name, type_="foreignkey")
            else:
                op.drop_constraint(name, table_name=source_table, type_="foreignkey")
