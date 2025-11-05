"""Declarative seed data used across development helpers."""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import List


@dataclass(frozen=True)
class PlanSeed:
    code: str
    name: str
    description: str
    amount_minor: int
    amount: Decimal
    currency: str
    duration_days: int
    granted_quota: int
    sort_order: int


DEFAULT_PLANS: List[PlanSeed] = [
    PlanSeed(
        code="FREE_TRIAL",
        name="Free Trial",
        description="10 бесплатных откликов без оплаты",
        amount_minor=0,
        amount=Decimal("0"),
        currency="RUB",
        duration_days=7,
        granted_quota=10,
        sort_order=0,
    ),
    PlanSeed(
        code="WEEKLY",
        name="Weekly",
        description="Недельная подписка с квотой 200 откликов",
        amount_minor=99_000,
        amount=Decimal("990"),
        currency="RUB",
        duration_days=7,
        granted_quota=200,
        sort_order=10,
    ),
    PlanSeed(
        code="MONTHLY",
        name="Monthly",
        description="Месячная подписка с квотой 800 откликов",
        amount_minor=299_000,
        amount=Decimal("2990"),
        currency="RUB",
        duration_days=30,
        granted_quota=800,
        sort_order=20,
    ),
]
