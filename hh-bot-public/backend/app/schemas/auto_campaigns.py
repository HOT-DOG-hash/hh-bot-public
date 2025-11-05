from __future__ import annotations

import hashlib
import json
from datetime import datetime, time
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from backend.app.models.auto_campaigns import (
    CampaignMode,
    CampaignStatus,
    CooldownStrategy,
    DeliveryLogStatus,
    SkipPolicy,
)


def _hash_payload(payload: Any) -> str:
    normalized = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


class DeliveryWindowInput(BaseModel):
    client_token: str
    start_utc: time
    end_utc: time
    days_mask: str
    is_default: bool = False

    @field_validator("days_mask")
    @classmethod
    def validate_days_mask(cls, value: str) -> str:
        if len(value) != 7 or any(ch not in {"0", "1"} for ch in value):
            raise ValueError("days_mask must consist of 7 characters containing only 0 or 1")
        if value.count("1") == 0:
            raise ValueError("days_mask must enable at least one day")
        return value

    @model_validator(mode="after")
    def validate_window(self) -> "DeliveryWindowInput":
        if self.start_utc >= self.end_utc:
            raise ValueError("start_utc must be less than end_utc")
        start_minutes = self.start_utc.hour * 60 + self.start_utc.minute
        end_minutes = self.end_utc.hour * 60 + self.end_utc.minute
        if start_minutes < 3 * 60 or end_minutes > 21 * 60:
            raise ValueError("windows must be within 03:00–21:00 UTC")
        return self


class CampaignStepInput(BaseModel):
    client_token: Optional[str] = None
    step_order: int = Field(ge=1, le=999)
    vacancy_filter: dict[str, Any]
    delivery_window_token: str = Field(alias="delivery_window_id")
    message_template_id: int
    skip_policy: SkipPolicy = SkipPolicy.MANUAL

    model_config = ConfigDict(populate_by_name=True)


class FrequencyCapsInput(BaseModel):
    per_day: int = Field(default=10, ge=0, le=10)
    per_week: int = Field(default=50, ge=0, le=50)
    per_company: int = Field(default=2, ge=0, le=2)


class CooldownPolicyInput(BaseModel):
    base_delay_ms: int = Field(default=60_000, ge=1)
    max_delay_ms: int = Field(default=900_000, ge=1)
    strategy: CooldownStrategy = CooldownStrategy.EXP
    error_streak_limit: int = Field(default=5, ge=1, le=10)

    @model_validator(mode="after")
    def validate_delays(self) -> "CooldownPolicyInput":
        if self.max_delay_ms < self.base_delay_ms:
            raise ValueError("max_delay_ms must be greater or equal to base_delay_ms")
        return self


class CampaignCreateRequest(BaseModel):
    owner_id: int
    mode: CampaignMode
    daily_quota_target: int = Field(ge=1, le=100)
    default_window_token: Optional[str] = Field(default=None, alias="default_window_id")
    windows: list[DeliveryWindowInput]
    steps: list[CampaignStepInput]
    frequency_caps: Optional[FrequencyCapsInput] = None
    cooldown_policy: Optional[CooldownPolicyInput] = None

    model_config = ConfigDict(populate_by_name=True)

    @model_validator(mode="after")
    def ensure_defaults(self) -> "CampaignCreateRequest":
        if not self.windows:
            raise ValueError("at least one window is required")
        if not self.steps:
            raise ValueError("at least one step is required")
        if self.default_window_token is None:
            default_tokens = [w.client_token for w in self.windows if w.is_default]
            if default_tokens:
                self.default_window_token = default_tokens[0]
        return self


class CampaignStartRequest(BaseModel):
    force: bool = False

    model_config = ConfigDict(extra="forbid")


class CampaignCreatedResponse(BaseModel):
    id: int
    status: CampaignStatus
    revision: int
    default_window_id: int


class CampaignResource(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    owner_id: int
    status: CampaignStatus
    mode: CampaignMode
    daily_quota_target: int
    default_window_id: Optional[int] = None
    cooldown_policy_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime


class DeliveryWindowResource(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    campaign_id: int
    start_utc: time
    end_utc: time
    days_mask: str
    is_default: bool
    created_at: datetime
    updated_at: datetime


class CampaignStepResource(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    campaign_id: int
    step_order: int
    delivery_window_id: int
    message_template_id: int
    skip_policy: SkipPolicy
    vacancy_filter: dict[str, Any]
    created_at: datetime
    updated_at: datetime


class FrequencyCapsResource(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    per_day: int
    per_week: int
    per_company: int


class CooldownPolicyResource(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    base_delay_ms: int
    max_delay_ms: int
    strategy: CooldownStrategy
    error_streak_limit: int


class CampaignRunResource(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    campaign_id: int
    run_started_at: datetime
    run_finished_at: Optional[datetime] = None
    scheduled_by: str
    status: str
    sent_count: int
    error_count: int
    skipped_count: int
    delay_applied_ms: Optional[int] = None


class CampaignFullResponse(BaseModel):
    campaign: CampaignResource
    windows: list[DeliveryWindowResource]
    steps: list[CampaignStepResource]
    frequency_caps: Optional[FrequencyCapsResource] = None
    cooldown_policy: Optional[CooldownPolicyResource] = None
    runs: list[CampaignRunResource] = Field(default_factory=list)
    blacklist_sample: list["CompanyBlacklistItem"] = Field(default_factory=list)


class CampaignStartResponse(BaseModel):
    campaign_id: int
    scheduled_at: datetime
    delay_ms: Optional[int] = None
    status_after: CampaignStatus


class CampaignStatusResponse(BaseModel):
    campaign_id: int
    status: CampaignStatus
    updated_at: datetime


class PauseRequest(BaseModel):
    reason: str = Field(max_length=255)
    until: Optional[datetime] = None


class SkipRequest(BaseModel):
    vacancy_id: str
    step_id: Optional[int] = None
    reason: str = Field(max_length=255)
    note: Optional[str] = Field(default=None, max_length=1024)


class SkipResult(BaseModel):
    delivery_log_id: int
    status: DeliveryLogStatus
    attempted_at: datetime


class CompanyBlacklistCreate(BaseModel):
    company_name: str = Field(min_length=1, max_length=255)
    company_id_external: Optional[str] = Field(default=None, max_length=255)
    reason: Optional[str] = Field(default=None, max_length=255)


class CompanyBlacklistItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    owner_id: int
    company_name: str
    company_id_external: Optional[str] = None
    reason: Optional[str] = None
    added_at: datetime
    removed_at: Optional[datetime] = None


class CompanyBlacklistPage(BaseModel):
    items: list[CompanyBlacklistItem]
    next_cursor: Optional[str] = None


class IdempotencyRecord(BaseModel):
    action: str
    idempotency_key: str
    request_hash: str
    response: dict[str, Any]

    @classmethod
    def from_payload(cls, action: str, key: str, payload: dict[str, Any]) -> "IdempotencyRecord":
        return cls(
            action=action,
            idempotency_key=key,
            request_hash=_hash_payload(payload.get("request")),
            response=payload.get("response", {}),
        )
