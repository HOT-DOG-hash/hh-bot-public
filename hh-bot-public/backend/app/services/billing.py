from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple, cast

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.metrics import (
    observe_payment_failed,
    observe_payment_initiated,
    observe_payment_succeeded,
    observe_webhook_lag,
)
from backend.app.models.payments import (
    Payment,
    PaymentAttempt,
    PaymentEvent,
    PaymentStatus,
    Provider,
)
from backend.app.models.plan import Plan
from backend.app.models.quota import ApplicationQuota, UserTrial
from backend.app.models.subscription import Subscription, SubscriptionStatus
from backend.app.services.users import ensure_user
from backend.app.services.analytics import track_event

_LOGGER = logging.getLogger(__name__)
_UTC = timezone.utc
_FINAL_FAILURE_STATES = {
    PaymentStatus.FAILED,
    PaymentStatus.CANCELED,
    PaymentStatus.EXPIRED,
}


def calculate_price(plan: Plan) -> int:
    """Return amount in minor currency units for the plan."""
    return int(plan.amount_minor)


async def get_plan_by_code(session: AsyncSession, plan_code: str) -> Plan:
    result = await session.execute(select(Plan).where(Plan.code == plan_code))
    plan = result.scalar_one_or_none()
    if plan is None:
        raise ValueError(f"Plan '{plan_code}' not found")
    return plan


def _generate_invoice_url(payment_id: int) -> str:
    return f"https://pay.yoomoney.test/invoice/{payment_id}"


async def _get_payment_by_idempotency(session: AsyncSession, idempotency_key: str) -> Optional[Payment]:
    result = await session.execute(select(Payment).where(Payment.idempotency_key == idempotency_key))
    return result.scalar_one_or_none()


async def initiate_payment(
    session: AsyncSession,
    *,
    user_id: int,
    plan_code: str,
    idempotency_key: str,
    provider: Provider = Provider.YOOMONEY,
) -> Payment:
    existing = await _get_payment_by_idempotency(session, idempotency_key)
    if existing:
        _LOGGER.debug("idempotent payment hit for key %s -> %s", idempotency_key, existing.id)
        return existing

    plan = await get_plan_by_code(session, plan_code)
    payment = Payment(
        user_id=user_id,
        plan_code=plan.code,
        provider=provider,
        idempotency_key=idempotency_key,
        amount_minor=plan.amount_minor,
        currency=plan.currency,
        status=PaymentStatus.INITIATED,
    )
    session.add(payment)

    try:
        await session.flush()
    except IntegrityError:
        await session.rollback()
        existing = await _get_payment_by_idempotency(session, idempotency_key)
        if existing:
            _LOGGER.debug("race on payment creation, returning existing %s", existing.id)
            return existing
        raise

    payment.invoice_pdf_url = _generate_invoice_url(payment.id)
    attempt = PaymentAttempt(
        payment_id=payment.id,
        provider=provider,
        status=PaymentStatus.INITIATED,
        idempotency_key=idempotency_key,
        attempt_number=1,
    )
    session.add(attempt)
    await session.flush()

    observe_payment_initiated(plan.code)
    track_event("payment_initiated", payment_id=payment.id, plan_code=plan.code, user_id=user_id)
    return payment


def _normalize_dt(value: Optional[datetime]) -> datetime:
    if value is None:
        return datetime.now(tz=_UTC)
    if value.tzinfo is None:
        return value.replace(tzinfo=_UTC)
    return value.astimezone(_UTC)


def _is_valid_transition(current: PaymentStatus, new: PaymentStatus) -> bool:
    if current == new:
        return True
    if current == PaymentStatus.SUCCEEDED:
        return False
    if current in _FINAL_FAILURE_STATES:
        return False
    return True


async def _mark_latest_attempt(session: AsyncSession, payment_id: int, status: PaymentStatus) -> None:
    stmt = (
        select(PaymentAttempt)
        .where(PaymentAttempt.payment_id == payment_id)
        .order_by(PaymentAttempt.attempt_number.desc())
        .limit(1)
    )
    result = await session.execute(stmt)
    attempt = result.scalar_one_or_none()
    if attempt is None:
        return
    attempt.status = status
    if status in _FINAL_FAILURE_STATES:
        attempt.last_error = f"payment.{status.value}"
        attempt.next_retry_at = None


async def _get_quota(session: AsyncSession, user_id: int) -> ApplicationQuota | None:
    result = await session.execute(select(ApplicationQuota).where(ApplicationQuota.user_id == user_id))
    return result.scalar_one_or_none()


async def _ensure_quota_plan(session: AsyncSession, user_id: int, plan: Plan) -> ApplicationQuota:
    quota = await _get_quota(session, user_id)
    if quota is None:
        quota = ApplicationQuota(user_id=user_id, plan_code=plan.code)
        session.add(quota)
    quota.plan_code = plan.code
    quota.daily_limit = plan.granted_quota
    return quota


async def _ensure_trial(session: AsyncSession, user_id: int, plan: Plan, activated_at: datetime) -> UserTrial:
    result = await session.execute(select(UserTrial).where(UserTrial.user_id == user_id))
    trial = result.scalar_one_or_none()
    expires_at = activated_at + timedelta(days=plan.duration_days) if plan.duration_days else None
    if trial is None:
        trial = UserTrial(
            user_id=user_id,
            plan_code=plan.code,
            activated_at=activated_at,
            expires_at=expires_at,
            granted_quota=plan.granted_quota,
            consumed_quota=0,
        )
        session.add(trial)
    else:
        trial.plan_code = plan.code
        trial.activated_at = activated_at
        trial.expires_at = expires_at
        trial.granted_quota = plan.granted_quota
    return trial


async def _upsert_subscription(
    session: AsyncSession,
    user_id: int,
    plan: Plan,
    status: SubscriptionStatus,
    activated_at: datetime,
) -> Subscription:
    result = await session.execute(select(Subscription).where(Subscription.user_id == user_id))
    subscription = result.scalar_one_or_none()
    period_end: Optional[datetime] = (
        activated_at + timedelta(days=plan.duration_days) if plan.duration_days else None
    )

    if subscription is None:
        subscription = Subscription(
            user_id=user_id,
            plan_code=plan.code,
            status=status,
            current_period_start=activated_at,
            current_period_end=period_end,
            next_charge_at=period_end,
        )
        session.add(subscription)
        await session.flush()
    else:
        subscription.plan_code = plan.code
        subscription.status = status
        subscription.current_period_start = activated_at
        subscription.current_period_end = period_end
        subscription.next_charge_at = period_end

    return subscription


async def _activate_subscription(
    session: AsyncSession,
    payment: Payment,
    plan: Plan,
    activated_at: datetime,
) -> Subscription:
    subscription = await _upsert_subscription(
        session,
        payment.user_id,
        plan,
        SubscriptionStatus.ACTIVE,
        activated_at,
    )
    payment.subscription_id = subscription.id
    payment.subscription = subscription
    return subscription


async def activate_trial_for_user(
    session: AsyncSession,
    *,
    telegram_id: str,
    plan_code: str = "FREE_TRIAL",
) -> Subscription:
    user = await ensure_user(session, telegram_id=telegram_id)
    user_id = cast(int, user.id)
    plan = await get_plan_by_code(session, plan_code)
    activated_at = _normalize_dt(None)
    trial = await _ensure_trial(session, user_id, plan, activated_at)
    quota = await _ensure_quota_plan(session, user_id, plan)
    quota.trial_limit = trial.granted_quota
    subscription = await _upsert_subscription(
        session,
        user_id,
        plan,
        SubscriptionStatus.TRIAL,
        activated_at,
    )
    observe_payment_succeeded(plan.code, plan.amount_minor)
    track_event("trial_activated", user_id=user_id, plan_code=plan.code)
    return subscription


async def extend_subscription_for_user(
    session: AsyncSession,
    *,
    telegram_id: str,
    plan_code: str,
) -> Subscription:
    user = await ensure_user(session, telegram_id=telegram_id)
    user_id = cast(int, user.id)
    plan = await get_plan_by_code(session, plan_code)
    quota = await _ensure_quota_plan(session, user_id, plan)
    quota.daily_used = min(quota.daily_used, quota.daily_limit)
    now = _normalize_dt(None)
    result = await session.execute(select(Subscription).where(Subscription.user_id == user_id))
    subscription = result.scalar_one_or_none()
    if subscription is None:
        subscription = await _upsert_subscription(
            session,
            user_id,
            plan,
            SubscriptionStatus.ACTIVE,
            now,
        )
    else:
        current_end = _normalize_dt(subscription.current_period_end) if subscription.current_period_end else None
        period_end = current_end or now
        if period_end < now:
            period_end = now
        period_end = period_end + timedelta(days=plan.duration_days)
        if current_end is None or current_end < now:
            subscription.current_period_start = now
        subscription.plan_code = plan.code
        subscription.status = SubscriptionStatus.ACTIVE
        subscription.current_period_end = period_end
        subscription.next_charge_at = period_end
    return subscription


async def get_quota_snapshot(session: AsyncSession, *, telegram_id: str) -> ApplicationQuota:
    user = await ensure_user(session, telegram_id=telegram_id)
    user_id = cast(int, user.id)
    quota = await _get_quota(session, user_id)
    if quota is None:
        quota = ApplicationQuota(user_id=user_id, plan_code=None)
        session.add(quota)
        await session.flush()
    return quota


async def consume_quota(
    session: AsyncSession,
    *,
    telegram_id: str,
    count: int,
) -> ApplicationQuota:
    if count <= 0:
        raise ValueError("count must be positive")
    quota = await get_quota_snapshot(session, telegram_id=telegram_id)
    remaining_daily = max(0, quota.daily_limit - quota.daily_used)
    if remaining_daily < count:
        raise ValueError("daily quota exceeded")
    trial_remaining = max(0, quota.trial_limit - quota.trial_used)
    quota.daily_used += count
    if trial_remaining:
        if trial_remaining < count:
            raise ValueError("trial quota exceeded")
        quota.trial_used += count
    await session.flush()
    return quota


async def process_webhook_event(
    session: AsyncSession,
    *,
    provider_event_id: str,
    status: PaymentStatus,
    payment_id: Optional[int] = None,
    provider_payment_id: Optional[str] = None,
    raw_payload: Optional[dict] = None,
    occurred_at: Optional[datetime] = None,
) -> Tuple[Optional[Payment], bool]:
    if not provider_event_id:
        raise ValueError("provider_event_id is required")

    existing_event_stmt = select(PaymentEvent).where(PaymentEvent.provider_event_id == provider_event_id)
    event_result = await session.execute(existing_event_stmt)
    existing_event = event_result.scalar_one_or_none()
    if existing_event:
        _LOGGER.info("Duplicate webhook event %s", provider_event_id)
        existing_payment = await session.get(Payment, existing_event.payment_id)
        return existing_payment, False

    payment: Optional[Payment]
    if payment_id is not None:
        payment = await session.get(Payment, payment_id)
    elif provider_payment_id:
        result = await session.execute(
            select(Payment).where(Payment.provider_payment_id == provider_payment_id)
        )
        payment = result.scalar_one_or_none()
    else:
        raise ValueError("Either payment_id or provider_payment_id must be provided")

    if payment is None:
        _LOGGER.warning(
            "Webhook event %s ignored: payment not found (payment_id=%s, provider_payment_id=%s)",
            provider_event_id,
            payment_id,
            provider_payment_id,
        )
        return None, False

    plan = await get_plan_by_code(session, payment.plan_code)
    now = _normalize_dt(None)
    occurred = _normalize_dt(occurred_at) if occurred_at else None

    event = PaymentEvent(
        payment_id=payment.id,
        provider_event_id=provider_event_id,
        event_type=status.value,
        payload=raw_payload or {},
        status=status.value,
        processed_at=now,
    )
    session.add(event)

    if provider_payment_id:
        payment.provider_payment_id = provider_payment_id

    if _is_valid_transition(payment.status, status):
        previous = payment.status
        payment.status = status
        await _mark_latest_attempt(session, payment.id, status)
        _LOGGER.info(
            "Payment %s status %s -> %s via event %s",
            payment.id,
            previous.value,
            status.value,
            provider_event_id,
        )
    else:
        _LOGGER.warning(
            "Ignoring invalid status transition %s -> %s for payment %s",
            payment.status.value,
            status.value,
            payment.id,
        )

    if occurred is not None:
        observe_webhook_lag((now - occurred).total_seconds())
    else:
        observe_webhook_lag(None)

    if status is PaymentStatus.SUCCEEDED:
        activated_at = occurred or now
        await _activate_subscription(session, payment, plan, activated_at)
        if plan.code.upper() == "FREE_TRIAL":
            await _ensure_trial(session, payment.user_id, plan, activated_at)
        await _ensure_quota_plan(session, payment.user_id, plan)
        observe_payment_succeeded(plan.code, plan.amount_minor)
        track_event(
            "payment_succeeded",
            payment_id=payment.id,
            plan_code=plan.code,
            user_id=payment.user_id,
        )
    elif status in _FINAL_FAILURE_STATES:
        observe_payment_failed(plan.code, status.value)
        track_event(
            "payment_failed",
            payment_id=payment.id,
            plan_code=plan.code,
            user_id=payment.user_id,
            reason=status.value,
        )

    await session.flush()
    return payment, True
