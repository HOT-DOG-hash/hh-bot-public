from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.core.config import settings
from backend.app.core.db import get_db
from backend.app.core.logging import logger
from backend.app.core.redis import init_redis
from backend.app.integrations.hh.client import HHAPIError, HHUnauthorized, get_me
from backend.app.integrations.hh.config import get_redirect_uri
from backend.app.integrations.hh.oauth import build_auth_url, exchange_code_for_tokens
from backend.app.models import User

router = APIRouter(prefix="/oauth/hh", tags=["oauth", "headhunter"])
_STATE_PREFIX = "hh:oauth:state:"
_STATE_TTL = 600


async def _get_or_create_user(session: AsyncSession, chat_id: str) -> User:
    stmt = select(User).where(User.tg_id == chat_id)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()
    if user:
        return user

    user = User(tg_id=chat_id, is_active=True)
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


@router.get("/login", status_code=status.HTTP_302_FOUND)
async def start_hh_oauth(
    chat_id: str = Query(..., description="Telegram chat id or unique user key"),
    session: AsyncSession = Depends(get_db),
):
    user = await _get_or_create_user(session, chat_id=str(chat_id))

    state = secrets.token_urlsafe(24)
    redis = await init_redis()
    await redis.setex(f"{_STATE_PREFIX}{state}", _STATE_TTL, str(user.id))

    redirect_uri = get_redirect_uri(settings.base_url_normalized)
    url = build_auth_url(redirect_uri=redirect_uri, state=state)
    return RedirectResponse(url, status_code=status.HTTP_302_FOUND)


@router.get("/callback")
async def hh_oauth_callback(
    code: str,
    state: str,
    session: AsyncSession = Depends(get_db),
):
    redis = await init_redis()
    key = f"{_STATE_PREFIX}{state}"
    user_id = await redis.get(key)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired state"
        )
    await redis.delete(key)

    user = await session.get(User, int(user_id))
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    redirect_uri = get_redirect_uri(settings.base_url_normalized)
    try:
        token_payload = await exchange_code_for_tokens(code=code, redirect_uri=redirect_uri)
    except RuntimeError as exc:
        logger.warning("hh_exchange_failed")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY, detail="HH token exchange failed"
        ) from exc

    access_token = token_payload.get("access_token")
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY, detail="HH access_token missing"
        )

    refresh_token = token_payload.get("refresh_token")
    expires_in = token_payload.get("expires_in")
    expires_at = None
    if expires_in:
        try:
            expires_at = datetime.now(timezone.utc) + timedelta(seconds=int(expires_in))
        except (TypeError, ValueError):  # pragma: no cover - defensive guard
            logger.warning("hh_token_expires_parse", value=expires_in)

    hh_profile_id = None
    try:
        profile = await get_me(access_token)
        hh_profile_id = profile.get("id")
    except HHUnauthorized:
        logger.warning("hh_profile_lookup_failed", user_id=user.id, reason="unauthorized")
    except HHAPIError as exc:
        logger.warning("hh_profile_lookup_failed", user_id=user.id, reason=str(exc))
    except RuntimeError:
        logger.warning("hh_profile_lookup_failed", user_id=user.id, reason="unknown")

    user.hh_access_token = access_token
    user.hh_refresh_token = refresh_token or user.hh_refresh_token
    user.hh_token_expires_at = expires_at
    if hh_profile_id:
        user.hh_user_id = str(hh_profile_id)
    user.last_activity = datetime.now(timezone.utc)

    session.add(user)
    await session.commit()

    return JSONResponse({"status": "linked", "user_id": user.id, "hh_user_id": user.hh_user_id})
