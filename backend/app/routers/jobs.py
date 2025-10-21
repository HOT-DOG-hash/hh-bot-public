from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.db import get_db
from backend.app.core.logging import logger
from backend.app.integrations.hh.client import HHAPIError, HHUnauthorized, search_vacancies
from backend.app.integrations.hh.oauth import refresh_tokens
from backend.app.models import Subscription, User

router = APIRouter(prefix="/jobs", tags=["jobs"])


async def _resolve_user(session: AsyncSession, token: str) -> User:
    stmt = select(User).where(User.tg_id == token)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()
    if user:
        return user

    if token.isdigit():
        user = await session.get(User, int(token))
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


async def _require_active_subscription(session: AsyncSession, user: User) -> None:
    now = datetime.now(timezone.utc)
    stmt = (
        select(Subscription)
        .where(
            Subscription.user_id == user.id,
            Subscription.status == "active",
            or_(Subscription.valid_until.is_(None), Subscription.valid_until >= now),
        )
        .limit(1)
    )
    result = await session.execute(stmt)
    subscription = result.scalar_one_or_none()
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED, detail="Premium subscription required"
        )


def _apply_token_payload(user: User, payload: dict[str, Any]) -> str:
    now = datetime.now(timezone.utc)
    access_token = payload.get("access_token")
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY, detail="HH не вернул access_token"
        )
    user.hh_access_token = access_token
    user.hh_refresh_token = payload.get("refresh_token") or user.hh_refresh_token
    expires_in = payload.get("expires_in")
    if expires_in:
        try:
            user.hh_token_expires_at = now + timedelta(seconds=int(expires_in))
        except (TypeError, ValueError):  # pragma: no cover - defensive
            user.hh_token_expires_at = None
    else:
        user.hh_token_expires_at = None
    user.last_activity = now
    return access_token


async def _refresh_hh_token(session: AsyncSession, user: User) -> str:
    if not user.hh_refresh_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="HeadHunter account не привязан"
        )
    try:
        token_payload = await refresh_tokens(user.hh_refresh_token)
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY, detail="Не удалось обновить токен HH"
        ) from exc
    access_token = _apply_token_payload(user, token_payload)
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return access_token


async def _ensure_hh_token(session: AsyncSession, user: User) -> str:
    now = datetime.now(timezone.utc)
    token = user.hh_access_token
    if token:
        expires_at = user.hh_token_expires_at
        if expires_at and expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if not expires_at or expires_at > now + timedelta(seconds=60):
            return token
    return await _refresh_hh_token(session, user)


@router.get("/search")
async def search_jobs(
    q: str = Query(..., alias="q", description="Search text for vacancies"),
    page: int = Query(0, ge=0),
    per_page: int = Query(20, ge=1, le=100),
    area: str | None = Query(None, description="HeadHunter area identifier"),
    session: AsyncSession = Depends(get_db),
    user_token: str = Header(..., alias="X-User-Id"),
) -> dict[str, Any]:
    user = await _resolve_user(session, user_token.strip())
    await _require_active_subscription(session, user)

    params: dict[str, Any] = {"text": q, "page": page, "per_page": per_page}
    if area:
        params["area"] = area

    refreshed = False

    async def _perform_search(token: str) -> dict[str, Any]:
        return await search_vacancies(token, params, cache_ttl=120, cache_namespace=str(user.id))

    access_token = await _ensure_hh_token(session, user)

    try:
        data = await _perform_search(access_token)
    except HHUnauthorized:
        refreshed = True
        access_token = await _refresh_hh_token(session, user)
        try:
            data = await _perform_search(access_token)
        except HHUnauthorized as exc:
            logger.warning("hh_jobs_unauthorized", refreshed=True)
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="HeadHunter авторизация недействительна",
            ) from exc
    except HHAPIError as exc:
        logger.warning("hh_jobs_failed", status=exc.status, refreshed=False)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY, detail="HeadHunter временно недоступен"
        ) from exc

    if refreshed:
        logger.info("hh_jobs_refreshed_token")

    user.last_activity = datetime.now(timezone.utc)
    session.add(user)
    await session.commit()
    return data
