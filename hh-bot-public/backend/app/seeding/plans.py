from __future__ import annotations

from decimal import Decimal

DEFAULT_PLANS = [
    {
        "code": "FREE_TRIAL",
        "name": "Free Trial",
        "description": "10 targeted invites for trial users",
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
        "description": "Weekly automation, 200 invites",
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
        "description": "Monthly automation, 800 invites",
        "amount_minor": 299_000,
        "amount": Decimal("2990"),
        "currency": "RUB",
        "duration_days": 30,
        "granted_quota": 800,
        "is_active": True,
        "sort_order": 20,
    },
]

__all__ = ["DEFAULT_PLANS"]
