from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.db import get_db
from backend.app.services.billing import (
    BillingPlanNotFoundError,
    BillingProviderFailure,
    PaymentNotFoundError,
)
from backend.app.services.payments import (
    PaymentInitiationError,
    PaymentInitiationResult,
    get_payment_status,
    initiate_payment,
    process_webhook,
)

router = APIRouter(prefix="/api/v1/payments", tags=["payments"])


class InitiatePaymentRequest(BaseModel):
    plan_code: str = Field(..., min_length=1)
    idempotency_key: str | None = Field(None, min_length=1, max_length=128)


def _user_token_header(raw_token: str | None) -> str:
    token = (raw_token or "").strip()
    if not token:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="X-User-Id is required")
    return token


def _format_initiation_result(result: PaymentInitiationResult) -> dict[str, Any]:
    payment = result.payment
    provider_value = payment.provider.value if hasattr(payment.provider, "value") else str(payment.provider)
    status_value = payment.status.value if hasattr(payment.status, "value") else str(payment.status)
    return {
        "payment_id": str(payment.id),
        "provider": provider_value,
        "provider_payment_id": payment.provider_payment_id,
        "plan_code": payment.plan_code,
        "status": status_value,
        "idempotency_key": result.idempotency_key,
        "confirmation_url": result.confirmation_url,
    }


@router.post("/initiate")
async def initiate_payment_endpoint(
    payload: InitiatePaymentRequest,
    session: AsyncSession = Depends(get_db),
    user_token: str = Header(..., alias="X-User-Id"),
) -> dict[str, Any]:
    token = _user_token_header(user_token)
    try:
        result = await initiate_payment(
            session,
            user_token=token,
            plan_code=payload.plan_code,
            idempotency_key=payload.idempotency_key,
        )
    except BillingPlanNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except PaymentInitiationError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
    return _format_initiation_result(result)


@router.post("/webhook")
async def payment_webhook(
    request: Request,
    session: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    try:
        return await process_webhook(session, request)
    except BillingProviderFailure as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/{payment_id}/status")
async def payment_status_endpoint(
    payment_id: str,
    session: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    try:
        return await get_payment_status(session, payment_id)
    except PaymentNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
