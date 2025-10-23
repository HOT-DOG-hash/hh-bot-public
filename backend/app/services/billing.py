from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Iterable

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.config import settings
from backend.app.models import Payment, Subscription, User
from backend.app.models.billing import SubscriptionStatus
from backend.app.models.payments import PaymentStatus, Provider
from backend.app.payments.base import (
    PaymentProviderError,
    PaymentStatus as ProviderPaymentStatus,
)
from backend.app.payments.yoomoney import provider as yoomoney_provider

PLAN_CONFIG: dict[str, dict[str, Any]] = {
    "FREE_TRIAL": {
        "amount": 0.0,
        "amount_minor": 0,
        "currency": "RUB",
        "description": "Free trial (10 откликов)",
        "duration_days": 0,
        "granted_quota": 10,
    },
    "WEEKLY": {
        "amount": 690.0,
        "amount_minor": 69000,
        "currency": "RUB",
        "description": "Weekly premium plan",
        "duration_days": 7,
    },
    "MONTHLY": {
        "amount": 1900.0,
        "amount_minor": 190000,
        "currency": "RUB",
        "description": "Monthly premium plan",
        "duration_days": 30,
    },
}

IN_PROGRESS_STATUSES: set[PaymentStatus] = {PaymentStatus.PENDING}
PAID_STATUS = PaymentStatus.SUCCEEDED


class BillingPlanNotFoundError(ValueError):
    """Запрошенный тариф не найден."""


class BillingProviderFailure(RuntimeError):
    """Общая ошибка платёжного провайдера."""


class PaymentNotFoundError(LookupError):
    """Платёж не найден."""


@dataclass(slots=True)
class PaymentCreationResult:
    payment: Payment
    pay_url: str


@dataclass(slots=True)
class PaymentStatusResult:
    payment: Payment
    provider_status: ProviderPaymentStatus
    subscription: Subscription | None


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _normalize_plan_code(plan_code: str) -> str:
    return plan_code.upper()


def get_plan_config(plan_code: str) -> dict[str, Any]:
    normalized = _normalize_plan_code(plan_code)
    plan = PLAN_CONFIG.get(normalized)
    if plan:
        return plan
    raise BillingPlanNotFoundError(plan_code)


async def _ensure_user(session: AsyncSession, user_token: str) -> User:
    stmt = select(User).where(User.tg_id == user_token).limit(1)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()
    if user:
        return user

    user = User(tg_id=user_token, is_active=True, last_activity=_now())
    session.add(user)
    await session.flush()
    return user


def _idempotence_key(user: User, plan_code: str) -> str:
    raw = f"{user.id}:{plan_code}:yoomoney"
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    return digest[:64]


def _payment_payload(payment: Payment) -> dict[str, Any]:
    return dict(payment.raw or {})


def _update_payment_payload(payment: Payment, data: dict[str, Any]) -> None:
    payload = _payment_payload(payment)
    payload.update(data)
    payment.raw = payload


def _extract_pay_url(payment: Payment) -> str | None:
    payload = _payment_payload(payment)
    return payload.get("confirmation_url")


async def _find_latest_payment(
    session: AsyncSession,
    *,
    user_id: int,
    plan_code: str,
    statuses: Iterable[PaymentStatus],
) -> Payment | None:
    stmt: Select[tuple[Payment]] = (
        select(Payment)
        .where(
            Payment.user_id == user_id,
            Payment.plan_code == plan_code,
            Payment.status.in_(tuple(statuses)),
        )
        .order_by(Payment.created_at.desc())
        .limit(1)
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


def _map_provider_status(status: str | None) -> PaymentStatus:
    mapping = {
        "pending": PaymentStatus.PENDING,
        "waiting_for_capture": PaymentStatus.PENDING,
        "succeeded": PaymentStatus.SUCCEEDED,
        "canceled": PaymentStatus.CANCELED,
        "canceled_by_yoo": PaymentStatus.CANCELED,
        "expired": PaymentStatus.EXPIRED,
        "failed": PaymentStatus.FAILED,
    }
    return mapping.get((status or "").lower(), PaymentStatus.PENDING)


def _resolve_provider() -> Provider:
    try:
        return Provider(settings.payment_provider)
    except ValueError as exc:  # pragma: no cover - misconfiguration
        raise BillingProviderFailure(f"Unsupported payment provider: {settings.payment_provider}") from exc


async def create_payment(
    session: AsyncSession,
    *,
    user_token: str,
    plan_code: str,
    return_url: str,
) -> PaymentCreationResult:
    normalized_plan = _normalize_plan_code(plan_code)
    plan_cfg = get_plan_config(normalized_plan)
    user = await _ensure_user(session, user_token)
    key = _idempotence_key(user, normalized_plan)

    existing = await _find_latest_payment(
        session,
        user_id=user.id,
        plan_code=normalized_plan,
        statuses=IN_PROGRESS_STATUSES,
    )
    if existing:
        url = _extract_pay_url(existing) or return_url
        return PaymentCreationResult(payment=existing, pay_url=url)

    amount_minor = int(plan_cfg.get("amount_minor") or round(float(plan_cfg["amount"]) * 100))
    currency = str(plan_cfg.get("currency", "RUB"))
    provider_enum = _resolve_provider()
    metadata = {
        "user_id": str(user.id),
        "plan_code": normalized_plan,
        "idempotence_key": key,
    }

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

    metadata["payment_id"] = str(payment.id)

    try:
        invoice = await yoomoney_provider.create_payment(
            amount_rub=float(plan_cfg["amount"]),
            description=str(plan_cfg.get("description") or normalized_plan),
            return_url=return_url,
            metadata=metadata,
            idempotence_key=key,
        )
    except PaymentProviderError as exc:
        payment.status = PaymentStatus.FAILED
        _update_payment_payload(
            payment,
            {
                "error": str(exc),
                "metadata": metadata,
            },
        )
        await session.commit()
        raise BillingProviderFailure(str(exc)) from exc

    payment.provider_payment_id = invoice.external_id or payment.provider_payment_id
    _update_payment_payload(
        payment,
        {
            "provider_status": invoice.status,
            "confirmation_url": invoice.confirmation_url,
            "metadata": metadata,
            "raw": invoice.raw,
            "return_url": return_url,
        },
    )

    user.last_activity = _now()
    session.add(user)
    await session.commit()
    await session.refresh(payment)

    url = _extract_pay_url(payment) or return_url
    return PaymentCreationResult(payment=payment, pay_url=url)


async def refresh_payment_status(
    session: AsyncSession,
    *,
    user_token: str,
    external_id: str,
) -> PaymentStatusResult:
    user = await _ensure_user(session, user_token)

    stmt = (
        select(Payment)
        .where(
            Payment.user_id == user.id,
            Payment.provider == _resolve_provider(),
            Payment.provider_payment_id == external_id,
        )
        .limit(1)
    )
    result = await session.execute(stmt)
    payment = result.scalar_one_or_none()
    if not payment:
        raise PaymentNotFoundError(external_id)

    try:
        provider_status = await yoomoney_provider.get_payment_status(external_id)
    except PaymentProviderError as exc:
        raise BillingProviderFailure(str(exc)) from exc

    mapped_status = _map_provider_status(provider_status.status)
    payment.status = mapped_status
    _update_payment_payload(
        payment,
        {
            "provider_status": provider_status.status,
            "paid_at": provider_status.paid_at.isoformat() if provider_status.paid_at else None,
            "raw": provider_status.raw,
        },
    )

    subscription: Subscription | None = None
    if mapped_status is PAID_STATUS:
        plan_cfg = get_plan_config(payment.plan_code)
        subscription = await activate_subscription(
            session,
            user=user,
            plan_code=payment.plan_code,
            duration_days=int(plan_cfg.get("duration_days", 0)),
        )
        if subscription:
            payment.subscription_id = subscription.id

    user.last_activity = _now()
    session.add_all([payment, user])
    await session.commit()
    if subscription:
        await session.refresh(subscription)

    return PaymentStatusResult(
        payment=payment,
        provider_status=provider_status,
        subscription=subscription,
    )


async def activate_subscription(
    session: AsyncSession,
    *,
    user: User,
    plan_code: str,
    duration_days: int,
) -> Subscription:
    normalized_plan = _normalize_plan_code(plan_code)
    stmt = (
        select(Subscription)
        .where(Subscription.user_id == user.id, Subscription.plan_code == normalized_plan)
        .order_by(Subscription.created_at.desc())
        .limit(1)
    )
    result = await session.execute(stmt)
    subscription = result.scalar_one_or_none()
    now = _now()

    period_end = now + timedelta(days=duration_days) if duration_days > 0 else None

    if subscription:
        base = subscription.current_period_end or now
        if base < now:
            base = now
        subscription.current_period_start = now
        subscription.current_period_end = base + timedelta(days=duration_days)
        subscription.status = SubscriptionStatus.ACTIVE
    else:
        subscription = Subscription(
            user_id=user.id,
            plan_code=normalized_plan,
            status=SubscriptionStatus.ACTIVE,
            current_period_start=now,
            current_period_end=period_end,
            next_charge_at=period_end,
            cancel_at=None,
            cancel_at_period_end=False,
        )
        session.add(subscription)

    return subscription


async def get_subscription(
    session: AsyncSession,
    *,
    user_token: str,
) -> Subscription | None:
    user = await _ensure_user(session, user_token)
    stmt = (
        select(Subscription)
        .where(Subscription.user_id == user.id)
        .order_by(
            Subscription.current_period_end.is_(None),
            Subscription.current_period_end.desc().nullslast(),
        )
        .limit(1)
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()
