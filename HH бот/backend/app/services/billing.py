from __future__ import annotations

import hashlib
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.config import settings
from backend.app.models import Payment, Subscription, User
from backend.app.payments.base import PaymentProviderError, PaymentStatus
from backend.app.payments.yoomoney import provider as yoomoney_provider

PLAN_CONFIG: dict[str, dict[str, Any]] = {
    "premium-week": {
        "amount": 690.0,
        "amount_minor": 69000,
        "currency": "RUB",
        "description": "Premium plan (7 days)",
        "duration_days": 7,
    },
    "premium-month": {
        "amount": 1900.0,
        "amount_minor": 190000,
        "currency": "RUB",
        "description": "Premium plan (30 days)",
        "duration_days": 30,
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

IN_PROGRESS_STATUSES: set[str] = {"created", "pending", "waiting_for_capture"}
PAID_STATUS = "paid"


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
    provider_status: PaymentStatus
    subscription: Subscription | None


def _now() -> datetime:
    return datetime.now(timezone.utc)


def get_plan_config(plan_code: str) -> dict[str, Any]:
    candidates = (
        PLAN_CONFIG.get(plan_code),
        PLAN_CONFIG.get(plan_code.upper()),
        PLAN_CONFIG.get(plan_code.lower()),
    )
    for plan in candidates:
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


def _extract_pay_url(payment: Payment) -> str | None:
    payload = payment.payload_json or {}
    return payload.get("confirmation_url")


def _update_payment_payload(payment: Payment, data: dict[str, Any]) -> None:
    payload = payment.payload_json or {}
    payload.update(data)
    payment.payload_json = payload


async def _find_latest_payment(
    session: AsyncSession,
    *,
    user_id: int,
    plan_code: str,
    statuses: Iterable[str],
) -> Payment | None:
    stmt: Select[tuple[Payment]] = (
        select(Payment)
        .where(
            Payment.user_id == user_id,
            Payment.provider == settings.payment_provider,
            Payment.plan == plan_code,
            Payment.status.in_(tuple(statuses)),
        )
        .order_by(Payment.created_at.desc())
        .limit(1)
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def create_payment(
    session: AsyncSession,
    *,
    user_token: str,
    plan_code: str,
    return_url: str,
) -> PaymentCreationResult:
    plan = get_plan_config(plan_code)
    user = await _ensure_user(session, user_token)

    existing = await _find_latest_payment(
        session,
        user_id=user.id,
        plan_code=plan_code,
        statuses=IN_PROGRESS_STATUSES | {PAID_STATUS},
    )
    if existing:
        pay_url = _extract_pay_url(existing)
        if existing.status in IN_PROGRESS_STATUSES and pay_url:
            return PaymentCreationResult(payment=existing, pay_url=pay_url)
        if existing.status == PAID_STATUS:
            return PaymentCreationResult(payment=existing, pay_url=pay_url or return_url)

    metadata = {"plan": plan_code, "user_id": user.id}
    idempotence_key = _idempotence_key(user, plan_code)

    try:
        invoice = await yoomoney_provider.create_payment(
            amount_rub=float(plan["amount"]),
            description=str(plan["description"]),
            return_url=return_url,
            metadata=metadata,
            idempotence_key=idempotence_key,
        )
    except PaymentProviderError as exc:
        raise BillingProviderFailure(str(exc)) from exc

    amount_minor = int(round(float(plan["amount"]) * 100))
    now = _now()

    payment = Payment(
        user_id=user.id,
        provider=settings.payment_provider,
        external_id=invoice.external_id,
        plan=plan_code,
        amount=amount_minor,
        currency=str(plan["currency"]),
        status=invoice.status or "created",
        payload_json={
            "plan": plan_code,
            "confirmation_url": invoice.confirmation_url,
            "provider_status": invoice.status,
            "created_at": invoice.created_at.isoformat() if invoice.created_at else None,
            "raw": invoice.raw,
        },
    )
    user.last_activity = now
    session.add_all([payment, user])
    await session.commit()
    await session.refresh(payment)

    return PaymentCreationResult(payment=payment, pay_url=invoice.confirmation_url)


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
            Payment.provider == settings.payment_provider,
            Payment.external_id == external_id,
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

    status = provider_status.status
    if status == "succeeded":
        payment.status = PAID_STATUS
    else:
        payment.status = status

    _update_payment_payload(
        payment,
        {
            "provider_status": status,
            "paid_at": provider_status.paid_at.isoformat() if provider_status.paid_at else None,
            "raw": provider_status.raw,
        },
    )

    subscription: Subscription | None = None
    if payment.status == PAID_STATUS:
        plan = PLAN_CONFIG.get(payment.plan, PLAN_CONFIG["premium-month"])
        subscription = await activate_subscription(
            session,
            user=user,
            plan_code=payment.plan,
            duration_days=int(plan["duration_days"]),
        )

    user.last_activity = _now()
    session.add_all([payment, user])
    await session.commit()
    if subscription:
        await session.refresh(subscription)

    return PaymentStatusResult(
        payment=payment, provider_status=provider_status, subscription=subscription
    )


async def activate_subscription(
    session: AsyncSession,
    *,
    user: User,
    plan_code: str,
    duration_days: int,
) -> Subscription:
    stmt = (
        select(Subscription)
        .where(Subscription.user_id == user.id, Subscription.plan == plan_code)
        .order_by(Subscription.created_at.desc())
        .limit(1)
    )
    result = await session.execute(stmt)
    subscription = result.scalar_one_or_none()
    now = _now()

    if subscription:
        base = subscription.valid_until or now
        if base < now:
            base = now
        subscription.valid_until = base + timedelta(days=duration_days)
        subscription.status = "active"
        subscription.active = True
        subscription.auto_renew = False
    else:
        subscription = Subscription(
            user_id=user.id,
            plan=plan_code,
            status="active",
            active=True,
            valid_until=now + timedelta(days=duration_days),
            auto_renew=False,
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
        .order_by(Subscription.valid_until.desc().nulls_last(), Subscription.created_at.desc())
        .limit(1)
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()
