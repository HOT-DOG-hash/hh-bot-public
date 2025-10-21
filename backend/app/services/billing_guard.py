from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Literal

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.billing import ApplicationQuota, Subscription, SubscriptionStatus

PAID_PLAN_CODES = {"WEEKLY", "MONTHLY"}


@dataclass(slots=True)
class QuotaInfo:
    plan_code: str
    granted: int
    consumed: int
    remaining: int
    non_renewable: bool
    exhausted_at: datetime | None


@dataclass(slots=True)
class Eligibility:
    mode: Literal["paid", "trial", "none"]
    subscription: Subscription | None
    quota: QuotaInfo | None


async def get_active_subscription(session: AsyncSession, user_id: int) -> Subscription | None:
    now = datetime.now(timezone.utc)
    stmt = (
        select(Subscription)
        .where(
            Subscription.user_id == user_id,
            Subscription.status.in_(
                [SubscriptionStatus.ACTIVE.value, SubscriptionStatus.TRIALING.value]
            ),
            or_(
                Subscription.current_period_start.is_(None),
                Subscription.current_period_start <= now,
            ),
            or_(Subscription.current_period_end.is_(None), Subscription.current_period_end >= now),
        )
        .order_by(
            Subscription.current_period_end.is_(None).desc(), Subscription.current_period_end.desc()
        )
        .limit(1)
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def get_quota(
    session: AsyncSession, user_id: int, plan_code: str = "FREE_TRIAL"
) -> QuotaInfo | None:
    stmt = (
        select(ApplicationQuota)
        .where(
            and_(
                ApplicationQuota.user_id == user_id,
                ApplicationQuota.plan_code == plan_code,
            )
        )
        .limit(1)
    )
    result = await session.execute(stmt)
    quota = result.scalar_one_or_none()
    if quota is None:
        return None
    remaining = max(quota.granted - quota.consumed, 0)
    return QuotaInfo(
        plan_code=quota.plan_code,
        granted=quota.granted,
        consumed=quota.consumed,
        remaining=remaining,
        non_renewable=quota.non_renewable,
        exhausted_at=quota.exhausted_at,
    )


async def evaluate_access(session: AsyncSession, user_id: int) -> Eligibility:
    subscription = await get_active_subscription(session, user_id)
    if subscription and (subscription.plan_code or "").upper() in PAID_PLAN_CODES:
        return Eligibility(mode="paid", subscription=subscription, quota=None)

    quota = await get_quota(session, user_id)
    if quota and quota.remaining > 0:
        return Eligibility(mode="trial", subscription=subscription, quota=quota)
    if quota and quota.remaining <= 0:
        return Eligibility(mode="none", subscription=subscription, quota=quota)
    return Eligibility(mode="none", subscription=subscription, quota=None)
