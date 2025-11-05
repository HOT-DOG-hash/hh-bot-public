from __future__ import annotations

import logging
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import cast

from backend.app.core.db import get_db
from backend.app.schemas.payments import (
    PaymentInitiateRequest,
    PaymentInitiateResponse,
    PaymentWebhookRequest,
    PaymentWebhookResponse,
)
from backend.app.services.billing import initiate_payment, process_webhook_event
from backend.app.services.users import ensure_user

router = APIRouter(prefix="/api/v1/payments", tags=["payments"])
_LOGGER = logging.getLogger(__name__)


def _build_invoice_url(payment) -> str:
    return payment.invoice_pdf_url or f"https://pay.yoomoney.test/invoice/{payment.id}"


@router.post("/initiate", response_model=PaymentInitiateResponse)
async def initiate_payment_endpoint(
    payload: PaymentInitiateRequest,
    db: AsyncSession = Depends(get_db),
) -> PaymentInitiateResponse:
    idempotency_key: str = payload.idempotency_key or str(uuid4())
    user_id = payload.user_id
    if user_id is None:
        if payload.telegram_id is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="user_id or telegram_id is required")
        user = await ensure_user(db, telegram_id=payload.telegram_id)
        user_id = cast(int, user.id)
    try:
        payment = await initiate_payment(
            db,
            user_id=user_id,
            plan_code=payload.plan_code,
            idempotency_key=idempotency_key,
            provider=payload.provider,
        )
        await db.commit()
        await db.refresh(payment)
    except ValueError as exc:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover - defensive
        await db.rollback()
        _LOGGER.exception("payment initiation failed: %s", exc)
        raise HTTPException(status_code=500, detail="payment initiation failed") from exc

    return PaymentInitiateResponse(
        payment_id=payment.id,
        status=payment.status,
        invoice_url=_build_invoice_url(payment),
        amount_minor=payment.amount_minor,
        currency=payment.currency,
        idempotency_key=payment.idempotency_key,
    )


@router.post("/webhook", response_model=PaymentWebhookResponse)
async def payments_webhook(
    payload: PaymentWebhookRequest,
    db: AsyncSession = Depends(get_db),
) -> PaymentWebhookResponse:
    try:
        payment, created = await process_webhook_event(
            db,
            provider_event_id=payload.provider_event_id,
            status=payload.status,
            payment_id=payload.payment_id,
            provider_payment_id=payload.provider_payment_id,
            raw_payload=payload.raw,
            occurred_at=payload.occurred_at,
        )
        await db.commit()
        if payment is not None:
            await db.refresh(payment)
    except ValueError as exc:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover - defensive
        await db.rollback()
        _LOGGER.exception("webhook processing failed: %s", exc)
        raise HTTPException(status_code=500, detail="webhook processing failed") from exc

    deduplicated = payment is not None and not created
    processed = payment is not None and created
    status_out = payment.status if payment is not None else payload.status

    return PaymentWebhookResponse(
        payment_id=payment.id if payment else None,
        status=status_out,
        deduplicated=deduplicated,
        processed=processed,
    )
