from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.db import get_db
from backend.app.models.plan import Plan
from backend.app.models.subscription import Subscription
from backend.app.schemas.billing import (
    PlansResponse,
    SubscriptionExtendRequest,
    SubscriptionResponse,
    TrialActivateRequest,
    TrialActivateResponse,
    SubscriptionUpgradeRequest,
    SubscriptionInfo,
)
from backend.app.schemas.plan import PlanOut
from backend.app.services.billing import (
    activate_trial_for_user,
    extend_subscription_for_user,
    get_quota_snapshot,
)
from backend.app.services.users import ensure_user
from backend.app.routers.quota import build_quota_info

router = APIRouter(prefix="/api/v1/billing", tags=["billing"])
_UTC = timezone.utc


def _ensure_aware(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=_UTC)
    return value.astimezone(_UTC)


async def _serialize_subscription(
    session: AsyncSession,
    *,
    telegram_id: str,
) -> SubscriptionInfo:
    user = await ensure_user(session, telegram_id=telegram_id)
    result = await session.execute(select(Subscription).where(Subscription.user_id == user.id))
    subscription = result.scalar_one_or_none()
    if subscription is None:
        return SubscriptionInfo()

    now = datetime.now(tz=_UTC)
    expires_in_days: int | None = None
    period_end = _ensure_aware(subscription.current_period_end)
    period_start = _ensure_aware(subscription.current_period_start)
    next_charge = _ensure_aware(subscription.next_charge_at)

    if period_end:
        remaining = (period_end - now).total_seconds()
        expires_in_days = max(0, int(remaining // 86400)) if remaining > 0 else 0

    return SubscriptionInfo(
        status=subscription.status,
        plan_code=subscription.plan_code,
        current_period_start=period_start,
        current_period_end=period_end,
        next_charge_at=next_charge,
        expires_in_days=expires_in_days,
    )


@router.get("/plans", response_model=PlansResponse)
async def list_public_plans(db: AsyncSession = Depends(get_db)) -> PlansResponse:
    stmt = select(Plan).where(Plan.is_active.is_(True)).order_by(Plan.sort_order.asc())
    result = await db.execute(stmt)
    plans = result.scalars().all()
    payload = [PlanOut.model_validate(plan) for plan in plans]
    return PlansResponse(plans=payload)


@router.post("/trial/activate", response_model=TrialActivateResponse, status_code=status.HTTP_200_OK)
async def activate_trial(
    payload: TrialActivateRequest,
    db: AsyncSession = Depends(get_db),
) -> TrialActivateResponse:
    await activate_trial_for_user(
        db,
        telegram_id=payload.telegram_id,
        plan_code=payload.plan_code,
    )
    quota = await get_quota_snapshot(db, telegram_id=payload.telegram_id)
    await db.commit()
    return TrialActivateResponse(
        subscription=await _serialize_subscription(db, telegram_id=payload.telegram_id),
        quota=build_quota_info(quota),
    )


@router.get("/subscription", response_model=SubscriptionResponse)
async def get_subscription(
    telegram_id: str = Query(..., description="Telegram user id"),
    db: AsyncSession = Depends(get_db),
) -> SubscriptionResponse:
    info = await _serialize_subscription(db, telegram_id=telegram_id)
    return SubscriptionResponse(subscription=info)


@router.post("/subscription/extend", response_model=SubscriptionResponse)
async def extend_subscription(
    payload: SubscriptionExtendRequest,
    db: AsyncSession = Depends(get_db),
) -> SubscriptionResponse:
    await extend_subscription_for_user(
        db,
        telegram_id=payload.telegram_id,
        plan_code=payload.plan_code,
    )
    await db.commit()
    info = await _serialize_subscription(db, telegram_id=payload.telegram_id)
    return SubscriptionResponse(subscription=info)


@router.post("/subscription/upgrade", response_model=SubscriptionResponse)
async def upgrade_subscription(
    payload: SubscriptionUpgradeRequest,
    db: AsyncSession = Depends(get_db),
) -> SubscriptionResponse:
    # Upgrade is treated as an extend with immediate plan switch for MVP.
    return await extend_subscription(payload, db)
