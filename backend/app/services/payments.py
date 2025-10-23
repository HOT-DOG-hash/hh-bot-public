from __future__ import annotations

import hashlib
import hmac
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from time import monotonic
from typing import Any
from uuid import UUID, uuid4

from fastapi import Request
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core import metrics
from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.models import Payment, PaymentAttempt, PaymentEvent, Subscription, User
from backend.app.models.payments import (
    PaymentAttemptPhase,
    PaymentEventType,
    PaymentStatus,
    Provider,
)
from backend.app.payments.base import (
    PaymentInvoice,
    PaymentProviderError,
    PaymentStatus as ProviderPaymentStatus,
)
from backend.app.payments.yoomoney import provider as yoomoney_provider
from backend.app.services.analytics import track_event
from backend.app.services.billing import BillingProviderFailure, PaymentNotFoundError, activate_subscription, get_plan_config

TERMINAL_STATUSES = {
    PaymentStatus.SUCCEEDED,
    PaymentStatus.CANCELED,
    PaymentStatus.EXPIRED,
    PaymentStatus.FAILED,
}
PENDING_STATUS = PaymentStatus.PENDING


@dataclass(slots=True)
class PaymentInitiationResult:
    payment: Payment
    confirmation_url: str | None
    idempotency_key: str


class PaymentInitiationError(RuntimeError):
    pass


def _payment_raw(payment: Payment) -> dict[str, Any]:
    return dict(payment.raw or {})


def _update_payment_raw(payment: Payment, data: dict[str, Any]) -> None:
    payload = _payment_raw(payment)
    payload.update(data)
    payment.raw = payload


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


async def _next_attempt_no(
    session: AsyncSession, payment_id: UUID, phase: PaymentAttemptPhase
) -> int:
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
    phase: PaymentAttemptPhase,
    ok: bool,
    duration_ms: int,
    error: str | None = None,
) -> None:
    attempt_no = await _next_attempt_no(session, payment.id, phase)
    attempt = PaymentAttempt(
        payment_id=payment.id,
        attempt_no=attempt_no,
        phase=phase,
        ok=ok,
        error=error,
        duration_ms=duration_ms,
    )
    session.add(attempt)


def _confirmation_from_payment(payment: Payment) -> str | None:
    return _payment_raw(payment).get("confirmation_url")


def _metadata_for_payment(user: User, plan_code: str, idempotency_key: str, payment_id: UUID) -> dict[str, Any]:
    return {
        "payment_id": str(payment_id),
        "user_id": str(user.id),
        "plan_code": plan_code,
        "idempotency_key": idempotency_key,
    }


def _resolve_provider() -> Provider:
    try:
        return Provider(settings.payment_provider)
    except ValueError as exc:  # pragma: no cover - defensive
        raise PaymentInitiationError(f"Unsupported payment provider: {settings.payment_provider}") from exc


async def initiate_payment(
    session: AsyncSession,
    *,
    user_token: str,
    plan_code: str,
    idempotency_key: str | None = None,
) -> PaymentInitiationResult:
    user = await _ensure_user(session, user_token)
    normalized_plan = plan_code.upper()
    plan_cfg = get_plan_config(normalized_plan)
    key = (idempotency_key or uuid4().hex)[:128]

    stmt = select(Payment).where(Payment.idempotency_key == key).limit(1)
    result = await session.execute(stmt)
    existing = result.scalar_one_or_none()
    if existing:
        confirmation = _confirmation_from_payment(existing)
        return PaymentInitiationResult(existing, confirmation, key)

    provider_enum = _resolve_provider()
    amount_minor = int(plan_cfg.get("amount_minor") or round(float(plan_cfg["amount"]) * 100))
    currency = str(plan_cfg.get("currency", "RUB"))

    payment = Payment(
        user_id=user.id,
        plan_code=normalized_plan,
        provider=provider_enum,
        idempotency_key=key,
        amount_minor=amount_minor,
        currency=currency,
        status=PaymentStatus.PENDING,
    )
    session.add(payment)
    await session.flush()

    metadata = _metadata_for_payment(user, normalized_plan, key, payment.id)
    start = monotonic()
    invoice: PaymentInvoice | None = None
    error_message: str | None = None

    try:
        invoice = await yoomoney_provider.create_payment(
            amount_rub=float(plan_cfg["amount"]),
            description=str(plan_cfg.get("description") or normalized_plan),
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

    phase = PaymentAttemptPhase.INIT
    if ok and invoice is not None:
        payment.provider_payment_id = invoice.external_id or payment.provider_payment_id
        _update_payment_raw(
            payment,
            {
                "confirmation_url": invoice.confirmation_url,
                "provider_status": invoice.status,
                "raw": invoice.raw,
                "metadata": metadata,
            },
        )
        metrics.payments_initiated_total.labels(plan_code=normalized_plan).inc()
        track_event(
            "payment_init",
            {
                "payment_id": str(payment.id),
                "user_id": user.id,
                "plan_code": normalized_plan,
            },
        )
        await _record_attempt(
            session,
            payment,
            phase=phase,
            ok=True,
            duration_ms=duration_ms,
        )
        await session.commit()
        confirmation = invoice.confirmation_url
        return PaymentInitiationResult(payment, confirmation, key)

    payment.status = PaymentStatus.FAILED
    _update_payment_raw(
        payment,
        {
            "init_error": error_message,
            "metadata": metadata,
        },
    )
    metrics.payments_status_total.labels(status=PaymentStatus.FAILED.value).inc()
    track_event(
        "payment_init_failed",
        {
            "payment_id": str(payment.id),
            "user_id": user.id,
            "plan_code": normalized_plan,
            "error": error_message,
        },
    )
    await _record_attempt(
        session,
        payment,
        phase=phase,
        ok=False,
        duration_ms=duration_ms,
        error=error_message,
    )
    await session.commit()
    raise PaymentInitiationError(error_message or "Платёжный провайдер не ответил вовремя")


def _verify_webhook_signature(request: Request, payload: bytes) -> None:
    secret = settings.yoomoney_webhook_secret
    if not secret:
        return
    provided = request.headers.get("X-YooMoney-Signature") or ""
    expected = hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, provided):
        raise BillingProviderFailure("WEBHOOK_INVALID_SIGNATURE")


def _load_event(body: bytes) -> dict[str, Any]:
    try:
        return json.loads(body.decode("utf-8"))
    except json.JSONDecodeError as exc:
        raise BillingProviderFailure("Invalid webhook JSON") from exc


def _coerce_event_type(raw: str | None) -> PaymentEventType:
    if raw is None:
        return PaymentEventType.PENDING
    try:
        return PaymentEventType(raw)
    except ValueError:
        return PaymentEventType.PENDING


def _normalize_status(status: str | None) -> PaymentStatus:
    if status is None:
        return PaymentStatus.PENDING
    mapping = {
        "pending": PaymentStatus.PENDING,
        "waiting_for_capture": PaymentStatus.PENDING,
        "succeeded": PaymentStatus.SUCCEEDED,
        "canceled": PaymentStatus.CANCELED,
        "expired": PaymentStatus.EXPIRED,
        "failed": PaymentStatus.FAILED,
    }
    return mapping.get(status.lower(), PaymentStatus.PENDING)


async def process_webhook(session: AsyncSession, request: Request) -> dict[str, Any]:
    body = await request.body()
    _verify_webhook_signature(request, body)
    payload = _load_event(body)

    event_id = str(payload.get("event_id") or payload.get("id") or uuid4())
    event_type_raw = str(payload.get("event") or payload.get("type") or "")
    event_type = _coerce_event_type(event_type_raw)
    object_payload = payload.get("object") or {}
    provider_payment_id = object_payload.get("id")
    idempotency_key = object_payload.get("metadata", {}).get("idempotency_key")

    start = monotonic()
    event = PaymentEvent(
        provider_event_id=event_id,
        event_type=event_type,
        payload=payload,
    )

    try:
        await session.begin()
        session.add(event)
        await session.flush()
    except IntegrityError:
        await session.rollback()
        metrics.payment_webhooks_total.labels(event_type=event_type_raw or "unknown").inc()
        duration_ms = int((monotonic() - start) * 1000)
        metrics.webhook_processing_ms.labels(result="duplicate").observe(duration_ms)
        return {"status": "duplicate"}

    payment: Payment | None = None
    if provider_payment_id:
        stmt = select(Payment).where(Payment.provider_payment_id == provider_payment_id).limit(1)
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
            event_id=event_id,
            provider_payment_id=provider_payment_id,
        )
    else:
        event.payment_id = payment.id
        target_status = _normalize_status(object_payload.get("status"))
        previous_status = payment.status
        if previous_status in TERMINAL_STATUSES:
            result_label = "already_terminal"
        elif target_status is PENDING_STATUS:
            payment.status = PaymentStatus.PENDING
            result_label = PaymentStatus.PENDING.value
        else:
            payment.status = target_status
            _update_payment_raw(
                payment,
                {
                    "provider_status": target_status.value,
                    "webhook_payload": object_payload,
                },
            )
            if target_status is PaymentStatus.SUCCEEDED:
                plan_cfg = get_plan_config(payment.plan_code)
                duration_days = int(plan_cfg.get("duration_days", 0))
                user = await session.get(User, payment.user_id)
                subscription = await activate_subscription(
                    session,
                    user=user,
                    plan_code=payment.plan_code,
                    duration_days=duration_days,
                )
                if subscription:
                    payment.subscription_id = subscription.id
                metrics.payments_status_total.labels(status=target_status.value).inc()
                track_event(
                    "payment_success",
                    {
                        "payment_id": str(payment.id),
                        "user_id": payment.user_id,
                        "plan_code": payment.plan_code,
                        "subscription_id": str(subscription.id) if subscription else None,
                    },
                )
                result_label = target_status.value
            else:
                metrics.payments_status_total.labels(status=target_status.value).inc()
                track_event(
                    f"payment_{target_status.value}",
                    {
                        "payment_id": str(payment.id),
                        "user_id": payment.user_id,
                        "plan_code": payment.plan_code,
                    },
                )
                result_label = target_status.value

        duration_ms = int((monotonic() - start) * 1000)
        await _record_attempt(
            session,
            payment,
            phase=PaymentAttemptPhase.WEBHOOK,
            ok=True,
            duration_ms=duration_ms,
        )

    await session.commit()
    metrics.payment_webhooks_total.labels(event_type=event_type_raw or "unknown").inc()
    duration_ms = int((monotonic() - start) * 1000)
    metrics.webhook_processing_ms.labels(result=result_label).observe(duration_ms)
    return {"status": result_label}


async def get_payment_status(session: AsyncSession, payment_id: UUID) -> dict[str, Any]:
    payment = await session.get(Payment, payment_id)
    if not payment:
        raise PaymentNotFoundError(str(payment_id))
    confirmation = _confirmation_from_payment(payment)
    response: dict[str, Any] = {
        "payment_id": str(payment.id),
        "status": payment.status.value if isinstance(payment.status, PaymentStatus) else payment.status,
        "provider_payment_id": payment.provider_payment_id,
        "plan_code": payment.plan_code,
        "confirmation_url": confirmation,
    }
    if payment.status is PaymentStatus.SUCCEEDED:
        stmt = (
            select(Subscription)
            .where(Subscription.user_id == payment.user_id)
            .order_by(
                Subscription.current_period_end.is_(None),
                Subscription.current_period_end.desc().nullslast(),
            )
            .limit(1)
        )
        result = await session.execute(stmt)
        subscription = result.scalar_one_or_none()
        if subscription and subscription.current_period_end:
            response["next_charge_at"] = subscription.current_period_end.isoformat()
    return response


__all__ = [
    "PaymentInitiationResult",
    "PaymentInitiationError",
    "initiate_payment",
    "process_webhook",
    "get_payment_status",
]
