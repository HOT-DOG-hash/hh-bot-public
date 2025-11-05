from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from backend.app.schemas.common import TelegramIdentityRequest


class QuotaInfo(BaseModel):
    plan_code: str | None = None
    daily_limit: int = 0
    daily_used: int = 0
    trial_limit: int = 0
    trial_used: int = 0
    remaining_daily: int = Field(0, ge=0)
    remaining_trial: int = Field(0, ge=0)
    has_trial: bool = False
    trial_exhausted: bool = False

    model_config = ConfigDict(from_attributes=True)


class QuotaConsumeRequest(TelegramIdentityRequest):
    count: int = Field(..., gt=0, le=200)
