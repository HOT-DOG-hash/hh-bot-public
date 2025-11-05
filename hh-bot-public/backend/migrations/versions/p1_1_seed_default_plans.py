"""seed default plans

Revision ID: p1_1
Revises: p1_0
Create Date: 2025-10-24 15:10:00.000000

"""
from __future__ import annotations

from decimal import Decimal
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "p1_1"
down_revision: Union[str, Sequence[str], None] = "p1_0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

PLANS = (
    {
        "code": "FREE_TRIAL",
        "name": "Free Trial",
        "description": "10 бесплатных откликов без оплаты",
        "amount_minor": 0,
        "amount": Decimal("0"),
        "currency": "RUB",
        "duration_days": 7,
        "granted_quota": 10,
        "is_active": True,
        "sort_order": 0,
    },
    {
        "code": "WEEKLY",
        "name": "Weekly",
        "description": "Недельная подписка с квотой 200 откликов",
        "amount_minor": 99_000,
        "amount": Decimal("990"),
        "currency": "RUB",
        "duration_days": 7,
        "granted_quota": 200,
        "is_active": True,
        "sort_order": 10,
    },
    {
        "code": "MONTHLY",
        "name": "Monthly",
        "description": "Месячная подписка с квотой 800 откликов",
        "amount_minor": 299_000,
        "amount": Decimal("2990"),
        "currency": "RUB",
        "duration_days": 30,
        "granted_quota": 800,
        "is_active": True,
        "sort_order": 20,
    },
)

plans_table = sa.table(
    "plans",
    sa.column("code", sa.String),
    sa.column("name", sa.String),
    sa.column("description", sa.Text),
    sa.column("amount_minor", sa.Integer),
    sa.column("amount", sa.Numeric(10, 2)),
    sa.column("currency", sa.String),
    sa.column("duration_days", sa.SmallInteger),
    sa.column("granted_quota", sa.Integer),
    sa.column("is_active", sa.Boolean),
    sa.column("sort_order", sa.Integer),
)


def _build_params(codes: list[str]) -> tuple[str, dict[str, str]]:
    placeholders = []
    params: dict[str, str] = {}
    for idx, code in enumerate(codes):
        key = f"code_{idx}"
        placeholders.append(f":{key}")
        params[key] = code
    return ", ".join(placeholders), params


def upgrade() -> None:
    """Insert default plan rows if missing."""
    bind = op.get_bind()
    codes: list[str] = [str(plan["code"]) for plan in PLANS]
    if not codes:
        return
    placeholder_sql, params = _build_params(codes)
    existing = {
        row[0]
        for row in bind.execute(
            sa.text(f"SELECT code FROM plans WHERE code IN ({placeholder_sql})"),
            params,
        )
    }
    to_insert = [plan for plan in PLANS if plan["code"] not in existing]
    if to_insert:
        op.bulk_insert(plans_table, to_insert)


def downgrade() -> None:
    """Remove seeded plans."""
    op.execute("DELETE FROM plans WHERE code IN ('FREE_TRIAL', 'WEEKLY', 'MONTHLY')")
