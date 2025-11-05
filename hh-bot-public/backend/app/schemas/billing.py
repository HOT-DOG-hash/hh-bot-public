from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from backend.app.models.subscription import SubscriptionStatus
from backend.app.schemas.common import TelegramIdentityRequest
from backend.app.schemas.plan import PlanOut
from backend.app.schemas.quota import QuotaInfo


class TrialActivateRequest(TelegramIdentityRequest):
    plan_code: str = Field(default="FREE_TRIAL", max_length=50)


class SubscriptionInfo(BaseModel):
    status: SubscriptionStatus | None = None
    plan_code: str | None = None
    current_period_start: datetime | None = None
    current_period_end: datetime | None = None
    next_charge_at: datetime | None = None
    expires_in_days: int | None = None


class TrialActivateResponse(BaseModel):
    subscription: SubscriptionInfo
    quota: QuotaInfo


class SubscriptionQuery(TelegramIdentityRequest):
    pass


class SubscriptionExtendRequest(TelegramIdentityRequest):
    plan_code: str = Field(..., max_length=50)


class SubscriptionUpgradeRequest(SubscriptionExtendRequest):
    pass


class SubscriptionResponse(BaseModel):
    subscription: SubscriptionInfo


class PlansResponse(BaseModel):
    plans: list[PlanOut]
