from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from backend.app.models.payments import PaymentStatus, Provider


class PaymentInitiateRequest(BaseModel):
    user_id: Optional[int] = None
    telegram_id: Optional[str] = None
    plan_code: str
    idempotency_key: Optional[str] = None
    provider: Provider = Provider.YOOMONEY

    @model_validator(mode="after")
    def validate_identity(self):
        if not self.user_id and not self.telegram_id:
            raise ValueError("either user_id or telegram_id must be provided")
        return self


class PaymentInitiateResponse(BaseModel):
    payment_id: int
    status: PaymentStatus
    invoice_url: str
    amount_minor: int
    currency: str
    idempotency_key: str


class PaymentWebhookRequest(BaseModel):
    provider_event_id: str = Field(..., alias="event_id")
    status: PaymentStatus
    payment_id: Optional[int] = None
    provider_payment_id: Optional[str] = None
    occurred_at: Optional[datetime] = None
    raw: Optional[dict] = None

    model_config = ConfigDict(populate_by_name=True)


class PaymentWebhookResponse(BaseModel):
    payment_id: Optional[int]
    status: PaymentStatus
    deduplicated: bool
    processed: bool
