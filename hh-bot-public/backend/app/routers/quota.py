from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.db import get_db
from backend.app.models.quota import ApplicationQuota
from backend.app.schemas.quota import QuotaConsumeRequest, QuotaInfo
from backend.app.services.billing import consume_quota, get_quota_snapshot

router = APIRouter(prefix="/api/v1/quota", tags=["quota"])


def build_quota_info(quota: ApplicationQuota) -> QuotaInfo:
    remaining_daily = max(0, quota.daily_limit - quota.daily_used)
    remaining_trial = max(0, quota.trial_limit - quota.trial_used)
    return QuotaInfo(
        plan_code=quota.plan_code,
        daily_limit=quota.daily_limit,
        daily_used=quota.daily_used,
        trial_limit=quota.trial_limit,
        trial_used=quota.trial_used,
        remaining_daily=remaining_daily,
        remaining_trial=remaining_trial,
        has_trial=quota.trial_limit > 0,
        trial_exhausted=quota.trial_limit > 0 and remaining_trial == 0,
    )


@router.get("", response_model=QuotaInfo)
async def get_quota(
    telegram_id: str = Query(..., description="Telegram user id"),
    db: AsyncSession = Depends(get_db),
) -> QuotaInfo:
    quota = await get_quota_snapshot(db, telegram_id=telegram_id)
    await db.commit()
    return build_quota_info(quota)


@router.post("/consume", response_model=QuotaInfo, status_code=status.HTTP_200_OK)
async def consume_quota_endpoint(
    payload: QuotaConsumeRequest,
    db: AsyncSession = Depends(get_db),
) -> QuotaInfo:
    try:
        quota = await consume_quota(
            db,
            telegram_id=payload.telegram_id,
            count=payload.count,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    await db.commit()
    return build_quota_info(quota)
