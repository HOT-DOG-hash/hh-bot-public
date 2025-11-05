from __future__ import annotations

from decimal import Decimal
from pydantic import BaseModel, ConfigDict


class PlanOut(BaseModel):
    code: str
    name: str
    description: str | None = None
    amount_minor: int
    amount: Decimal
    currency: str
    duration_days: int
    granted_quota: int
    sort_order: int

    model_config = ConfigDict(from_attributes=True)
