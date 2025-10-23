from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy import func, insert, select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.db import get_db
from backend.app.core.rate_limiter import SlidingWindowRateLimiter
from backend.app.models import User
from backend.app.models.billing import ApplicationQuota, UserApplication
from backend.app.services import billing_guard
from backend.app.services.analytics import track_event

router = APIRouter(prefix="/api/v1", tags=["trial", "applications"])

user_rate_limiter = SlidingWindowRateLimiter(limit=30, window_seconds=3.0)
ip_rate_limiter = SlidingWindowRateLimiter(limit=300, window_seconds=3.0)


class ApplyRequest(BaseModel):
    vacancy_id: str = Field(..., min_length=1, max_length=128)
    payload: dict[str, Any] | None = None


@dataclass(slots=True)
class ApplyResult:
    remaining: int | None


class DuplicateApplicationError(Exception):
    pass


class TrialExhaustedError(Exception):
    pass


class SubscriptionRequiredError(Exception):
    pass


async def _resolve_user(session: AsyncSession, token: str) -> User:
    token = token.strip()
    stmt = select(User).where(User.tg_id == token)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()
    if user:
        return user
    if token.isdigit():
        fallback = await session.get(User, int(token))
        if fallback:
            return fallback
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")


def _http_error(status_code: int, code: str, message: str) -> HTTPException:
    return HTTPException(status_code=status_code, detail={"code": code, "message": message})


async def _enforce_rate_limits(request: Request, user_id: int) -> None:
    client = request.client.host if request.client else "unknown"
    if not await ip_rate_limiter.allow(f"ip:{client}"):
        raise _http_error(
            status.HTTP_429_TOO_MANY_REQUESTS,
            "RATE_LIMITED",
            "Слишком много запросов, попробуйте позже.",
        )
    if not await user_rate_limiter.allow(f"user:{user_id}"):
        raise _http_error(
            status.HTTP_429_TOO_MANY_REQUESTS,
            "RATE_LIMITED",
            "Слишком много запросов, попробуйте позже.",
        )


async def _create_trial_quota(session: AsyncSession, user_id: int) -> ApplicationQuota:
    quota = ApplicationQuota(
        user_id=user_id,
        plan_code="FREE_TRIAL",
        granted=10,
        consumed=0,
        non_renewable=True,
        activated_at=datetime.now(timezone.utc),
    )
    session.add(quota)
    await session.flush()
    return quota


async def _record_application(session: AsyncSession, user_id: int, vacancy_id: str) -> None:
    dialect = session.bind.dialect.name if session.bind else ""
    if dialect == "postgresql":
        stmt = (
            pg_insert(UserApplication)
            .values(user_id=user_id, vacancy_id=vacancy_id, created_at=func.now())
            .on_conflict_do_nothing(index_elements=["user_id", "vacancy_id"])
            .returning(UserApplication.id)
        )
        result = await session.execute(stmt)
        if result.scalar_one_or_none() is None:
            raise DuplicateApplicationError
        return

    exists_stmt = (
        select(UserApplication.id)
        .where(
            UserApplication.user_id == user_id,
            UserApplication.vacancy_id == vacancy_id,
        )
        .limit(1)
    )
    result = await session.execute(exists_stmt)
    if result.scalar_one_or_none():
        raise DuplicateApplicationError
    await session.execute(
        insert(UserApplication).values(
            user_id=user_id,
            vacancy_id=vacancy_id,
            created_at=datetime.now(timezone.utc),
        )
    )


async def _consume_trial_quota(session: AsyncSession, user_id: int) -> ApplyResult:
    update_stmt = (
        update(ApplicationQuota)
        .where(
            ApplicationQuota.user_id == user_id,
            ApplicationQuota.plan_code == "FREE_TRIAL",
            ApplicationQuota.consumed < ApplicationQuota.granted,
        )
        .values(consumed=ApplicationQuota.consumed + 1)
        .returning(ApplicationQuota.id, ApplicationQuota.consumed, ApplicationQuota.granted)
    )
    result = await session.execute(update_stmt)
    row = result.mappings().first()
    if not row:
        raise TrialExhaustedError

    quota_id = row["id"]
    consumed = int(row["consumed"])
    granted = int(row["granted"])

    if consumed >= granted:
        await session.execute(
            update(ApplicationQuota)
            .where(ApplicationQuota.id == quota_id, ApplicationQuota.exhausted_at.is_(None))
            .values(exhausted_at=func.now())
        )

    remaining = max(granted - consumed, 0)
    return ApplyResult(remaining=remaining)


@router.post("/trial/activate")
async def activate_trial(
    request: Request,
    session: AsyncSession = Depends(get_db),
    user_token: str = Header(..., alias="X-User-Id"),
) -> dict[str, Any]:
    try:
        async with session.begin():
            user = await _resolve_user(session, user_token)
            await _enforce_rate_limits(request, user.id)
            quota = await _create_trial_quota(session, user.id)
    except IntegrityError:
        track_event("trial_already_used", {"user_id": user.id})
        raise _http_error(
            status.HTTP_409_CONFLICT,
            "TRIAL_ALREADY_USED",
            "Триал уже был активирован ранее.",
        ) from None

    track_event("trial_activated", {"user_id": user.id, "granted": quota.granted})
    activated = quota.activated_at or datetime.now(timezone.utc)
    return {
        "plan_code": quota.plan_code,
        "granted": quota.granted,
        "consumed": quota.consumed,
        "activated_at": activated.astimezone(timezone.utc).isoformat(),
    }


@router.get("/quota")
async def quota_details(
    session: AsyncSession = Depends(get_db),
    user_token: str = Header(..., alias="X-User-Id"),
) -> dict[str, Any]:
    user = await _resolve_user(session, user_token)
    eligibility = await billing_guard.evaluate_access(session, user.id)

    if eligibility.mode == "paid" and eligibility.subscription:
        return {"plan_code": eligibility.subscription.plan_code, "unlimited": True}

    quota = eligibility.quota or await billing_guard.get_quota(session, user.id)
    if quota:
        payload: dict[str, Any] = {
            "plan_code": quota.plan_code,
            "granted": quota.granted,
            "consumed": quota.consumed,
            "remaining": quota.remaining,
            "non_renewable": quota.non_renewable,
        }
        if quota.exhausted_at:
            payload["exhausted_at"] = quota.exhausted_at.astimezone(timezone.utc).isoformat()
        return payload

    return {
        "plan_code": None,
        "granted": 0,
        "consumed": 0,
        "remaining": 0,
        "non_renewable": True,
    }


@router.post("/apply")
async def apply_to_vacancy(
    payload: ApplyRequest,
    request: Request,
    session: AsyncSession = Depends(get_db),
    user_token: str = Header(..., alias="X-User-Id"),
) -> dict[str, Any]:
    try:
        async with session.begin():
            user = await _resolve_user(session, user_token)
            await _enforce_rate_limits(request, user.id)

            vacancy_id = payload.vacancy_id.strip()
            if not vacancy_id:
                raise _http_error(
                    status.HTTP_400_BAD_REQUEST,
                    "INVALID_VACANCY_ID",
                    "vacancy_id обязателен.",
                )

            track_event("apply_click", {"user_id": user.id, "vacancy_id": vacancy_id})

            eligibility = await billing_guard.evaluate_access(session, user.id)
            await _record_application(session, user.id, vacancy_id)

            if eligibility.mode == "paid":
                result = ApplyResult(remaining=None)
            elif eligibility.mode == "trial":
                result = await _consume_trial_quota(session, user.id)
            else:
                if eligibility.quota:
                    raise TrialExhaustedError
                raise SubscriptionRequiredError
    except DuplicateApplicationError:
        track_event("apply_duplicate", {"user_id": user.id, "vacancy_id": vacancy_id})
        raise _http_error(
            status.HTTP_409_CONFLICT,
            "DUPLICATE_APPLY",
            "Отклик уже был отправлен на эту вакансию.",
        ) from None
    except TrialExhaustedError:
        track_event("trial_exhausted", {"user_id": user.id, "vacancy_id": vacancy_id})
        raise _http_error(
            status.HTTP_403_FORBIDDEN,
            "TRIAL_EXHAUSTED",
            "Квота триала исчерпана. Оформите подписку, чтобы продолжить.",
        ) from None
    except SubscriptionRequiredError:
        track_event("subscription_required", {"user_id": user.id, "vacancy_id": vacancy_id})
        raise _http_error(
            status.HTTP_403_FORBIDDEN,
            "SUBSCRIPTION_REQUIRED",
            "Требуется активная подписка.",
        ) from None

    response: dict[str, Any] = {"status": "ok", "applied": True}
    if result.remaining is not None:
        response["remaining"] = result.remaining
    track_event(
        "apply_ok",
        {"user_id": user.id, "vacancy_id": vacancy_id, "remaining": result.remaining},
    )
    return response
