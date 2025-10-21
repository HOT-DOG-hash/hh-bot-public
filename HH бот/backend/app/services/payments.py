from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from time import monotonic
from typing import Any
from uuid import uuid4

from fastapi import Request
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core import metrics
from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.models import Payment, PaymentAttempt, PaymentEvent, Subscription, User
from backend.app.payments.base import PaymentProviderError
from backend.app.payments.yoomoney import provider as yoomoney_provider
from backend.app.services.analytics import track_event
from backend.app.services.billing import (
    BillingProviderFailure,
    PaymentNotFoundError,
    activate_subscription,
    get_plan_config,
)

TERMINAL_STATUSES = {"succeeded", "canceled", "expired", "failed"}
PENDING_STATUS = "pending"


@dataclass(slots=True)
class PaymentInitiationResult:
    payment: Payment
    confirmation_url: str | None
    idempotency_key: str


class PaymentInitiationError(RuntimeError):
    pass


async def _ensure_user(session: AsyncSession, user_token: str) -> User:
    stmt = select(User).where(User.tg_id == user_token).limit(1)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()
    if user:
        return user
    user = User(tg_id=user_token, is_active=True)
    session.add(user)
    await session.flush()
    return user


async def _next_attempt_no(session: AsyncSession, payment_id: int, phase: str) -> int:
    stmt = select(func.count(PaymentAttempt.id)).where(
        PaymentAttempt.payment_id == payment_id,
        PaymentAttempt.phase == phase,
    )
    result = await session.execute(stmt)
    return int(result.scalar_one()) + 1


async def _record_attempt(
    session: AsyncSession,
    payment: Payment,
    *,
    phase: str,
    ok: bool,
    duration_ms: int,
    error: str | None = None,
) -> None:
    attempt_no = await _next_attempt_no(session, payment.id, phase)
    attempt = PaymentAttempt(
        id=str(uuid4()),
        payment_id=payment.id,
        attempt_no=attempt_no,
        phase=phase,
        ok=ok,
        error=error,
        duration_ms=duration_ms,
    )
    session.add(attempt)


def _confirmation_from_payload(payment: Payment) -> str | None:
    if payment.confirmation_url:
        return payment.confirmation_url
    payload = payment.payload_json or {}
    return payload.get("confirmation_url")


def _metadata_for_payment(user: User, plan_code: str, idempotency_key: str) -> dict[str, Any]:
    return {
        "user_id": str(user.id),
        "plan_code": plan_code,
        "idempotency_key": idempotency_key,
    }


async def initiate_payment(
    session: AsyncSession,
    *,
    user_token: str,
    plan_code: str,
    idempotency_key: str | None = None,
) -> PaymentInitiationResult:
    user = await _ensure_user(session, user_token)
    plan = get_plan_config(plan_code)
    key = idempotency_key or uuid4().hex

    stmt = select(Payment).where(Payment.idempotency_key == key).limit(1)
    result = await session.execute(stmt)
    existing = result.scalar_one_or_none()
    if existing:
        confirmation = _confirmation_from_payload(existing)
        return PaymentInitiationResult(existing, confirmation, key)

    amount_minor = int(plan.get("amount_minor") or round(float(plan["amount"]) * 100))
    currency = str(plan.get("currency", "RUB"))
    placeholder_external_id = f"pending-{uuid4().hex}"

    payment = Payment(
        user_id=user.id,
        provider=settings.payment_provider,
        external_id=placeholder_external_id,
        plan=plan_code,
        amount=amount_minor,
        currency=currency,
        status=PENDING_STATUS,
        payload_json={"plan": plan_code},
        idempotency_key=key,
        confirmation_url=None,
    )
    session.add(payment)
    await session.flush()
    await session.refresh(payment)

    start = monotonic()
    metadata = _metadata_for_payment(user, plan_code, key)
    invoice = None
    error_message: str | None = None
    try:
        invoice = await yoomoney_provider.create_payment(
            amount_rub=float(plan["amount"]),
            description=str(plan.get("description") or plan_code),
            return_url=f"{settings.base_url_normalized}/payments/return",
            metadata=metadata,
            idempotence_key=key,
        )
        ok = True
    except PaymentProviderError as exc:
        ok = False
        error_message = str(exc)
    duration_ms = int((monotonic() - start) * 1000)
    metrics.yoomoney_api_latency_ms.labels(action="create_payment").observe(duration_ms)

    if ok and invoice is not None:
        payment.external_id = invoice.external_id or payment.external_id
        payment.confirmation_url = invoice.confirmation_url
        payload = payment.payload_json or {}
        payload.update(
            {
                "provider_status": invoice.status,
                "raw": invoice.raw,
            }
        )
        payment.payload_json = payload
        metrics.payments_initiated_total.labels(plan_code=plan_code).inc()
        track_event(
            "payment_init",
            {
                "user_id": user.id,
                "payment_id": payment.id,
                "plan_code": plan_code,
            },
        )
    else:
        payment.status = "failed"
        track_event(
            "payment_init_failed",
            {
                "user_id": user.id,
                "payment_id": payment.id,
                "plan_code": plan_code,
                "error": error_message or "provider_error",
            },
        )

    user.last_activity = datetime.now(timezone.utc)
    session.add_all([payment, user])
    await _record_attempt(
        session,
        payment,
        phase="init",
        ok=ok,
        duration_ms=duration_ms,
        error=error_message,
    )
    await session.commit()
    await session.refresh(payment)

    if not ok or invoice is None:
        raise PaymentInitiationError(error_message or "Payment provider did not return invoice")

    return PaymentInitiationResult(payment, invoice.confirmation_url, key)


def _verify_webhook_signature(request: Request, payload: bytes) -> None:
    secret = getattr(settings, "yoomoney_webhook_secret", None)
    if not secret:
        return
    provided = request.headers.get("X-YooMoney-Signature")
    import hashlib
    import hmac

    expected = hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, (provided or "")):
        raise BillingProviderFailure("invalid webhook signature")


def _normalize_status(raw_status: str | None) -> str:
    status = (raw_status or "").lower()
    mapping = {
        "pending": PENDING_STATUS,
        "waiting_for_capture": PENDING_STATUS,
        "succeeded": "succeeded",
        "canceled": "canceled",
        "canceled_by_merchant": "canceled",
        "expired": "expired",
        "failed": "failed",
        "refunded": "canceled",
    }
    return mapping.get(status, PENDING_STATUS)


async def process_webhook(session: AsyncSession, request: Request) -> dict[str, Any]:
    raw_body = await request.body()
    _verify_webhook_signature(request, raw_body)
    try:
        payload = json.loads(raw_body.decode("utf-8"))
    except json.JSONDecodeError as exc:
        raise BillingProviderFailure("invalid webhook payload") from exc

    provider_event_id = payload.get("event_id") or payload.get("id")
    if not provider_event_id:
        raise BillingProviderFailure("missing event_id")
    event_type = payload.get("event") or "unknown"
    object_payload = payload.get("object") or {}
    provider_payment_id = object_payload.get("id")
    metadata = object_payload.get("metadata") or {}
    idempotency_key = metadata.get("idempotency_key")

    start = monotonic()
    event = PaymentEvent(
        id=str(uuid4()),
        payment_id=None,
        provider_event_id=str(provider_event_id),
        event_type=str(event_type),
        payload=payload,
    )

    try:
        await session.begin()
        session.add(event)
        await session.flush()
    except IntegrityError:
        await session.rollback()
        metrics.payment_webhooks_total.labels(event_type="duplicate").inc()
        duration_ms = int((monotonic() - start) * 1000)
        metrics.webhook_processing_ms.labels(result="duplicate").observe(duration_ms)
        return {"status": "duplicate"}

    payment = None
    if provider_payment_id:
        stmt = select(Payment).where(Payment.external_id == provider_payment_id).limit(1)
        result = await session.execute(stmt)
        payment = result.scalar_one_or_none()
    if payment is None and idempotency_key:
        stmt = select(Payment).where(Payment.idempotency_key == idempotency_key).limit(1)
        result = await session.execute(stmt)
        payment = result.scalar_one_or_none()

    result_label = "unknown"
    if payment is None:
        logger.warning(
            "payment_webhook_orphan",
            event_id=provider_event_id,
            provider_payment_id=provider_payment_id,
        )
    else:
        event.payment_id = payment.id
        target_status = _normalize_status(object_payload.get("status"))
        previous_status = payment.status
        if previous_status in TERMINAL_STATUSES:
            result_label = "already_terminal"
        elif target_status == PENDING_STATUS:
            payment.status = PENDING_STATUS
            result_label = "pending"
        else:
            payment.status = target_status
            payment.payload_json = {
                **(payment.payload_json or {}),
                "provider_status": target_status,
                "webhook_payload": object_payload,
            }
            if target_status == "succeeded":
                plan = get_plan_config(payment.plan)
                duration_days = int(plan.get("duration_days", 30))
                user = await session.get(User, payment.user_id)
                subscription = await activate_subscription(
                    session,
                    user=user,
                    plan_code=payment.plan,
                    duration_days=duration_days,
                )
                metrics.payments_status_total.labels(status="succeeded").inc()
                track_event(
                    "payment_success",
                    {
                        "payment_id": payment.id,
                        "user_id": payment.user_id,
                        "plan_code": payment.plan,
                        "subscription_id": subscription.id if subscription else None,
                    },
                )
                result_label = "succeeded"
            else:
                metrics.payments_status_total.labels(status=target_status).inc()
                track_event(
                    f"payment_{target_status}",
                    {
                        "payment_id": payment.id,
                        "user_id": payment.user_id,
                        "plan_code": payment.plan,
                    },
                )
                result_label = target_status

        duration_ms = int((monotonic() - start) * 1000)
        await _record_attempt(
            session,
            payment,
            phase="webhook",
            ok=True,
            duration_ms=duration_ms,
        )

    await session.commit()
    metrics.payment_webhooks_total.labels(event_type=event_type).inc()
    duration_ms = int((monotonic() - start) * 1000)
    metrics.webhook_processing_ms.labels(result=result_label).observe(duration_ms)
    return {"status": result_label}


async def get_payment_status(session: AsyncSession, payment_id: int) -> dict[str, Any]:
    payment = await session.get(Payment, payment_id)
    if not payment:
        raise PaymentNotFoundError(payment_id)
    confirmation = _confirmation_from_payload(payment)
    response: dict[str, Any] = {
        "payment_id": payment.id,
        "status": payment.status,
        "provider_payment_id": payment.external_id,
        "plan_code": payment.plan,
        "confirmation_url": confirmation,
    }
    if payment.status == "succeeded":
        stmt = (
            select(Subscription)
            .where(Subscription.user_id == payment.user_id)
            .order_by(Subscription.valid_until.desc().nulls_last())
            .limit(1)
        )
        result = await session.execute(stmt)
        subscription = result.scalar_one_or_none()
        if subscription and subscription.valid_until:
            response["next_charge_at"] = subscription.valid_until.isoformat()
    return response


__all__ = [
    "PaymentInitiationResult",
    "PaymentInitiationError",
    "initiate_payment",
    "process_webhook",
    "get_payment_status",
]
